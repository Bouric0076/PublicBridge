"""
AI-specific serializers for enhanced API endpoints.
"""

from rest_framework import serializers
from .models import Report, ReportComment, ReportAttachment
from users.models import User, Profile
from forum.models import Post, Comment

class AIReportSerializer(serializers.ModelSerializer):
    """Enhanced report serializer with AI insights."""
    
    ai_insights = serializers.SerializerMethodField()
    similar_reports = serializers.SerializerMethodField()
    user_behavior_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'category', 'priority', 'urgency',
            'location', 'status', 'created_at', 'updated_at', 'user',
            'sentiment', 'keywords', 'nlp_category', 'ai_processed',
            'ai_processing_date', 'ai_confidence_score', 'ai_predicted_priority',
            'ai_hotspot_prediction', 'ai_insights', 'similar_reports', 'user_behavior_score'
        ]
        read_only_fields = ['ai_insights', 'similar_reports', 'user_behavior_score']
    
    def get_ai_insights(self, obj):
        """Get AI insights for this report."""
        return obj.get_ai_insights()
    
    def get_similar_reports(self, obj):
        """Get similar reports identified by AI."""
        similar_ids = obj.ai_similar_reports
        if similar_ids:
            similar_reports = Report.objects.filter(id__in=similar_ids)[:5]
            return [
                {
                    'id': report.id,
                    'title': report.title,
                    'category': report.category,
                    'priority': report.priority,
                    'created_at': report.created_at
                }
                for report in similar_reports
            ]
        return []
    
    def get_user_behavior_score(self, obj):
        """Get user behavior score for this report's author."""
        if obj.user:
            return {
                'score': obj.user.ai_behavior_score,
                'risk_level': obj.user.ai_risk_level,
                'processing_date': obj.user.ai_processing_date
            }
        return None

class AIUserSerializer(serializers.ModelSerializer):
    """Enhanced user serializer with AI insights."""
    
    ai_insights = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    ai_risk_assessment = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'engagement_score',
            'date_joined', 'last_login', 'is_active', 'ai_user_profile',
            'ai_behavior_score', 'ai_risk_level', 'ai_processing_date',
            'ai_insights', 'recent_activity', 'ai_risk_assessment'
        ]
        read_only_fields = ['ai_insights', 'recent_activity', 'ai_risk_assessment']
    
    def get_ai_insights(self, obj):
        """Get AI insights for this user."""
        if hasattr(obj, 'profile'):
            return obj.profile.get_ai_insights()
        return None
    
    def get_recent_activity(self, obj):
        """Get recent user activity."""
        from django.utils import timezone
        from datetime import timedelta
        
        recent_date = timezone.now() - timedelta(days=30)
        
        return {
            'reports_last_30_days': obj.reports.filter(created_at__gte=recent_date).count(),
            'comments_last_30_days': obj.comments.filter(created_at__gte=recent_date).count(),
            'posts_last_30_days': obj.posts.filter(created_at__gte=recent_date).count(),
            'total_engagement': obj.reports.count() + obj.comments.count() + obj.posts.count()
        }
    
    def get_ai_risk_assessment(self, obj):
        """Get AI risk assessment details."""
        if obj.ai_risk_level == 'high':
            return {
                'level': 'high',
                'recommendations': [
                    'Monitor user activity closely',
                    'Review recent reports for patterns',
                    'Consider manual verification of submissions'
                ],
                'triggers': obj.ai_user_profile.get('risk_triggers', [])
            }
        elif obj.ai_risk_level == 'medium':
            return {
                'level': 'medium',
                'recommendations': [
                    'Regular monitoring recommended',
                    'Check for unusual activity patterns',
                    'Verify report accuracy periodically'
                ]
            }
        return {
            'level': 'low',
            'recommendations': ['Standard monitoring sufficient']
        }

class AIPostSerializer(serializers.ModelSerializer):
    """Enhanced post serializer with AI insights."""
    
    sentiment_score = serializers.SerializerMethodField()
    engagement_prediction = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'created_at', 'updated_at',
            'sentiment_score', 'engagement_prediction'
        ]
    
    def get_sentiment_score(self, obj):
        """Get sentiment analysis for post content."""
        # This would integrate with sentiment analysis AI
        return {
            'sentiment': 'neutral',  # Placeholder
            'confidence': 0.8,
            'keywords': ['community', 'discussion']
        }
    
    def get_engagement_prediction(self, obj):
        """Get engagement prediction for this post."""
        # This would integrate with engagement prediction AI
        return {
            'predicted_views': 150,
            'predicted_comments': 12,
            'confidence': 0.75
        }

class AIProcessingRequestSerializer(serializers.Serializer):
    """Serializer for AI processing requests."""
    
    PROCESSING_TYPES = [
        ('report_analysis', 'Report Analysis'),
        ('user_behavior', 'User Behavior Analysis'),
        ('trend_prediction', 'Trend Prediction'),
        ('hotspot_detection', 'Hotspot Detection'),
        ('sentiment_analysis', 'Sentiment Analysis')
    ]
    
    processing_type = serializers.ChoiceField(choices=PROCESSING_TYPES)
    target_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of IDs to process (optional for batch processing)"
    )
    custom_parameters = serializers.JSONField(
        required=False,
        help_text="Custom parameters for AI processing"
    )
    
    def validate_target_ids(self, value):
        """Validate target IDs."""
        if value and len(value) > 100:
            raise serializers.ValidationError("Maximum 100 items can be processed at once")
        return value


class ChatbotRequestSerializer(serializers.Serializer):
    """Serializer for chatbot requests."""
    
    message = serializers.CharField(
        required=True,
        max_length=1000,
        help_text="Citizen's message to the chatbot"
    )
    context = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional context (user info, conversation history, etc.)"
    )
    session_id = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Session ID for conversation continuity"
    )
    
    def validate_message(self, value):
        """Validate message content."""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Message must be at least 2 characters long")
        if len(value.strip()) > 1000:
            raise serializers.ValidationError("Message cannot exceed 1000 characters")
        return value.strip()


class ChatbotResponseSerializer(serializers.Serializer):
    """Serializer for chatbot responses."""
    
    response = serializers.CharField(
        required=True,
        help_text="Chatbot's response to the citizen"
    )
    confidence = serializers.FloatField(
        required=True,
        min_value=0.0,
        max_value=1.0,
        help_text="Confidence score of the response"
    )
    intent = serializers.CharField(
        required=False,
        help_text="Detected intent of the user's message"
    )
    entities = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Extracted entities from the conversation"
    )
    conversation_context = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Updated conversation context"
    )
    requires_escalation = serializers.BooleanField(
        default=False,
        help_text="Whether the conversation should be escalated to human support"
    )
    suggested_actions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Suggested actions for the user"
    )


class AdvancedAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for advanced AI analysis requests."""
    
    report_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of report IDs to analyze"
    )
    analysis_types = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            ('comprehensive', 'Comprehensive Analysis'),
            ('sentiment', 'Sentiment Analysis'),
            ('classification', 'Classification'),
            ('trend', 'Trend Analysis'),
            ('multilingual', 'Multilingual Analysis'),
            ('contextual', 'Contextual Understanding')
        ]),
        required=False,
        default=['comprehensive'],
        help_text="Types of analysis to perform"
    )
    include_llama_insights = serializers.BooleanField(
        default=True,
        help_text="Whether to include Llama-specific advanced insights"
    )
    
    def validate_report_ids(self, value):
        """Validate report IDs."""
        if not value:
            raise serializers.ValidationError("At least one report ID is required")
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 reports can be analyzed at once")
        return value


class AdvancedAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for advanced AI analysis responses."""
    
    analysis_types = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="Types of analysis performed"
    )
    total_reports = serializers.IntegerField(
        required=True,
        help_text="Total number of reports analyzed"
    )
    results = serializers.ListField(
        child=serializers.JSONField(),
        required=True,
        help_text="Analysis results for each report"
    )
    processing_time = serializers.FloatField(
        required=True,
        help_text="Total processing time in seconds"
    )
    llama_enabled = serializers.BooleanField(
        required=True,
        help_text="Whether Llama models were used for analysis"
    )
    summary = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Summary of all analyses"
    )

class AIProcessingResponseSerializer(serializers.Serializer):
    """Serializer for AI processing responses."""
    
    processing_type = serializers.CharField()
    processed_count = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    processing_time = serializers.FloatField()
    results = serializers.JSONField()
    errors = serializers.ListField(child=serializers.CharField())