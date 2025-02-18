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
        return self.user.username

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



