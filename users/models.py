import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("citizen", "Citizen"),
        ("government_admin", "Government Admin"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="citizen")
    engagement_score = models.IntegerField(default=0)
    
    # AI Integration Fields
    ai_user_profile = models.JSONField(default=dict, blank=True)  # AI-generated user profile
    ai_behavior_score = models.FloatField(default=0.5)  # AI behavior analysis score (0-1)
    ai_risk_level = models.CharField(max_length=20, default='low')  # AI risk assessment
    ai_processing_date = models.DateTimeField(blank=True, null=True)  # When AI last processed

    def __str__(self):
        return self.username

    def is_govadmin(self):
        return self.role == "government_admin"




class GovernmentAdmin(models.Model):
    admin_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # Unique identifier
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="government_admin")
    is_active = models.BooleanField(default=True)  # Admin status (Active/Inactive)

    class Meta:
        permissions = [
            ("approve_ministries", "Can approve or reject ministry registrations"),
            ("manage_reports", "Can manage citizen-reported issues"),
            ("assign_reports", "Can assign reports to specific ministries"),
        ]

    def save(self, *args, **kwargs):
        """Ensure only users with 'government_admin' role can be GovernmentAdmins."""
        if self.user.role != "government_admin":
            raise ValidationError("User must have the 'government_admin' role.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} (GovernmentAdmin - Active: {self.is_active})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    following = models.ManyToManyField(
        'self',
        through='Follow',
        related_name='followers',
        symmetrical=False
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def analyze_with_ai(self):
        """Analyze user behavior and profile with AI."""
        from ai_agents import MultiAgentOrchestrator
        from django.utils import timezone
        
        try:
            # Get user data
            user_reports = self.user.reports.all()
            user_comments = self.user.comments.all()
            user_posts = self.user.posts.all()
            
            # Prepare input data
            input_data = {
                'user_id': self.user.id,
                'username': self.user.username,
                'role': self.user.role,
                'engagement_score': self.user.engagement_score,
                'created_at': self.user.date_joined.isoformat(),
                'last_login': self.user.last_login.isoformat() if self.user.last_login else None,
                'reports_count': user_reports.count(),
                'comments_count': user_comments.count(),
                'posts_count': user_posts.count(),
                'average_report_sentiment': self._get_average_sentiment(user_reports),
                'activity_frequency': self._get_activity_frequency(),
                'location': getattr(self, 'location', 'Unknown')
            }
            
            # Process with AI
            orchestrator = MultiAgentOrchestrator()
            result = orchestrator.analyze_user_behavior(input_data)
            
            # Update AI fields on User
            self.user.ai_user_profile = result.get('user_profile', {})
            self.user.ai_behavior_score = result.get('behavior_score', 0.5)
            self.user.ai_risk_level = result.get('risk_level', 'low')
            self.user.ai_processing_date = timezone.now()
            self.user.save()
            
            return True
            
        except Exception as e:
            print(f"AI analysis failed for user {self.user.username}: {e}")
            return False
    
    def _get_average_sentiment(self, reports):
        """Calculate average sentiment from user reports."""
        sentiments = [r.sentiment for r in reports if r.sentiment]
        if not sentiments:
            return 'neutral'
        
        sentiment_scores = {'positive': 1, 'neutral': 0, 'negative': -1}
        avg_score = sum(sentiment_scores.get(s, 0) for s in sentiments) / len(sentiments)
        
        if avg_score > 0.3:
            return 'positive'
        elif avg_score < -0.3:
            return 'negative'
        return 'neutral'
    
    def _get_activity_frequency(self):
        """Calculate user activity frequency."""
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.user.date_joined:
            return 'low'
        
        days_since_joined = (timezone.now() - self.user.date_joined).days
        if days_since_joined == 0:
            return 'high'
        
        total_activity = (
            self.user.reports.count() +
            self.user.comments.count() +
            self.user.posts.count()
        )
        
        activity_per_day = total_activity / days_since_joined
        
        if activity_per_day > 0.5:
            return 'high'
        elif activity_per_day > 0.1:
            return 'medium'
        return 'low'
    
    def get_ai_insights(self):
        """Get AI insights for this user."""
        return {
            'user_profile': self.user.ai_user_profile,
            'behavior_score': self.user.ai_behavior_score,
            'risk_level': self.user.ai_risk_level,
            'processing_date': self.user.ai_processing_date
        }

    def get_followers(self):
        return self.followers.all()

    def get_following(self):
        return self.following.all()


class Follow(models.Model):
    follower = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="following_set"
    )
    followed = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="followers_set"
    )

    def __str__(self):
        return f"{self.follower.user.username} follows {self.followed.user.username}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed"], name="unique_follow")
        ]



