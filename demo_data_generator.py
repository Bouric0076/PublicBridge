import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files import File
from io import BytesIO

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

from reports.models import Report, Category
from users.models import Profile
from forum.models import Post, Comment
from main.models import Notification


def create_demo_data():
    """Create comprehensive demo data for the hackathon presentation."""
    
    print("🚀 Starting demo data generation for PublicBridge AI...")
    
    # Create categories if they don't exist
    categories = [
        'Infrastructure', 'Public Safety', 'Sanitation', 'Utilities',
        'Transportation', 'Parks & Recreation', 'Environmental', 'Noise'
    ]
    
    category_objects = {}
    for cat_name in categories:
        cat, created = Category.objects.get_or_create(name=cat_name)
        category_objects[cat_name] = cat
        if created:
            print(f"✅ Created category: {cat_name}")
    
    # Create demo users
    demo_users = [
        {'username': 'john_citizen', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Citizen'},
        {'username': 'sarah_resident', 'email': 'sarah@example.com', 'first_name': 'Sarah', 'last_name': 'Resident'},
        {'username': 'mike_neighbor', 'email': 'mike@example.com', 'first_name': 'Mike', 'last_name': 'Neighbor'},
        {'username': 'lisa_community', 'email': 'lisa@example.com', 'first_name': 'Lisa', 'last_name': 'Community'},
        {'username': 'david_local', 'email': 'david@example.com', 'first_name': 'David', 'last_name': 'Local'},
    ]
    
    user_objects = []
    for user_data in demo_users:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )
        if created:
            user.set_password('demo123')
            user.save()
            # Create profile
            Profile.objects.get_or_create(user=user)
            user_objects.append(user)
            print(f"✅ Created user: {user_data['username']}")
    
    # Sample report data with AI-enhanced fields
    sample_reports = [
        {
            'title': 'Large pothole on Main Street',
            'description': 'There is a large pothole approximately 2 feet wide on Main Street near the intersection with Oak Avenue. Several cars have already hit it and it is getting worse with the recent rain.',
            'category': 'Infrastructure',
            'location': 'Main St & Oak Ave, Downtown',
            'priority': 'high',
            'ai_confidence': 0.87,
            'ai_sentiment': 'negative',
            'ai_urgency': 'high',
            'ai_category_prediction': 'Infrastructure',
            'ai_insights': 'High priority infrastructure issue requiring immediate attention'
        },
        {
            'title': 'Broken streetlight in residential area',
            'description': 'The streetlight on the corner of Pine Street and 3rd Avenue has been out for over a week. It is very dark at night and could be a safety concern for pedestrians.',
            'category': 'Infrastructure',
            'location': 'Pine St & 3rd Ave, Residential Area',
            'priority': 'medium',
            'ai_confidence': 0.92,
            'ai_sentiment': 'neutral',
            'ai_urgency': 'medium',
            'ai_category_prediction': 'Infrastructure',
            'ai_insights': 'Standard infrastructure maintenance issue'
        },
        {
            'title': 'Illegal dumping in vacant lot',
            'description': 'Someone has dumped old furniture and household trash in the vacant lot on Elm Street. This is attracting rats and creating an eyesore for the neighborhood.',
            'category': 'Sanitation',
            'location': 'Elm Street Vacant Lot',
            'priority': 'high',
            'ai_confidence': 0.78,
            'ai_sentiment': 'negative',
            'ai_urgency': 'high',
            'ai_category_prediction': 'Environmental',
            'ai_insights': 'Environmental health hazard requiring cleanup'
        },
        {
            'title': 'Water leak on sidewalk',
            'description': 'There is a constant water leak coming from the ground near the water meter at 456 Oak Avenue. Water is running down the sidewalk and being wasted.',
            'category': 'Utilities',
            'location': '456 Oak Avenue',
            'priority': 'high',
            'ai_confidence': 0.94,
            'ai_sentiment': 'concerned',
            'ai_urgency': 'high',
            'ai_category_prediction': 'Utilities',
            'ai_insights': 'Water waste issue requiring immediate utility department attention'
        },
        {
            'title': 'Loud music from neighbor',
            'description': 'My neighbor has been playing very loud music every night until 2 AM. I have asked them to turn it down but they refuse. This is affecting my sleep and work.',
            'category': 'Noise',
            'location': '789 Maple Street, Apartment 3B',
            'priority': 'medium',
            'ai_confidence': 0.71,
            'ai_sentiment': 'negative',
            'ai_urgency': 'medium',
            'ai_category_prediction': 'Noise',
            'ai_insights': 'Quality of life issue requiring mediation'
        },
        {
            'title': 'Graffiti on public building',
            'description': 'The community center on Washington Street has been vandalized with graffiti. This needs to be cleaned up as soon as possible to maintain the professional appearance of our public facilities.',
            'category': 'Environmental',
            'location': 'Community Center, Washington Street',
            'priority': 'medium',
            'ai_confidence': 0.83,
            'ai_sentiment': 'disappointed',
            'ai_urgency': 'medium',
            'ai_category_prediction': 'Environmental',
            'ai_insights': 'Vandalism requiring cleanup and possible investigation'
        },
        {
            'title': 'Pothole damaging vehicles',
            'description': 'Multiple deep potholes on Industrial Boulevard are causing damage to vehicles. Several residents have reported flat tires and alignment issues. This is a busy road that needs immediate repair.',
            'category': 'Infrastructure',
            'location': 'Industrial Boulevard, near factories',
            'priority': 'high',
            'ai_confidence': 0.89,
            'ai_sentiment': 'frustrated',
            'ai_urgency': 'high',
            'ai_category_prediction': 'Infrastructure',
            'ai_insights': 'Critical infrastructure failure causing vehicle damage'
        },
        {
            'title': 'Overgrown tree blocking sidewalk',
            'description': 'The tree in front of 234 Pine Avenue has grown so large that it is completely blocking the sidewalk. Pedestrians have to walk in the street to get around it, which is dangerous.',
            'category': 'Parks & Recreation',
            'location': '234 Pine Avenue',
            'priority': 'low',
            'ai_confidence': 0.76,
            'ai_sentiment': 'neutral',
            'ai_urgency': 'low',
            'ai_category_prediction': 'Parks & Recreation',
            'ai_insights': 'Routine maintenance issue for parks department'
        }
    ]
    
    # Create reports with AI fields
    report_objects = []
    for i, report_data in enumerate(sample_reports):
        user = random.choice(user_objects)
        category = category_objects[report_data['category']]
        
        # Create report with random timestamp within last 30 days
        days_ago = random.randint(1, 30)
        created_at = timezone.now() - timedelta(days=days_ago)
        
        report = Report.objects.create(
            title=report_data['title'],
            description=report_data['description'],
            category=category,
            location=report_data['location'],
            priority=report_data['priority'],
            status=random.choice(['pending', 'in_progress', 'resolved']),
            user=user,
            created_at=created_at,
            updated_at=created_at,
            # AI-enhanced fields
            ai_confidence=report_data['ai_confidence'],
            ai_sentiment=report_data['ai_sentiment'],
            ai_urgency=report_data['ai_urgency'],
            ai_category_prediction=report_data['ai_category_prediction'],
            ai_insights=report_data['ai_insights']
        )
        report_objects.append(report)
        print(f"✅ Created report: {report_data['title']}")
    
    # Create forum posts
    forum_topics = [
        'Community Safety Meeting This Thursday',
        'New Park Development Proposal',
        'Traffic Concerns on Main Street',
        'Recycling Program Updates',
        'Neighborhood Watch Program',
        'City Budget Public Hearing',
        'Local Business Development',
        'Environmental Sustainability Initiatives'
    ]
    
    for topic in forum_topics:
        user = random.choice(user_objects)
        post = Post.objects.create(
            title=topic,
            content=f"This is a community discussion about {topic.lower()}. We encourage all residents to participate and share their thoughts and concerns.",
            author=user,
            created_at=timezone.now() - timedelta(days=random.randint(1, 14))
        )
        print(f"✅ Created forum post: {topic}")
    
    # Create notifications
    notification_types = ['report_status_update', 'new_comment', 'system_announcement', 'meeting_reminder']
    
    for user in user_objects[:3]:  # Create notifications for first 3 users
        for _ in range(random.randint(2, 5)):
            notification = Notification.objects.create(
                user=user,
                notification_type=random.choice(notification_types),
                title=f"Demo Notification for {user.username}",
                message="This is a demo notification to showcase the notification system.",
                is_read=random.choice([True, False]),
                created_at=timezone.now() - timedelta(hours=random.randint(1, 72))
            )
    
    print("✅ Created demo notifications")
    
    # Create AI analytics data summary
    print("\n📊 AI ANALYTICS SUMMARY:")
    print("=" * 50)
    
    total_reports = len(report_objects)
    high_confidence_reports = sum(1 for r in report_objects if r.ai_confidence >= 0.8)
    medium_confidence_reports = sum(1 for r in report_objects if 0.6 <= r.ai_confidence < 0.8)
    low_confidence_reports = sum(1 for r in report_objects if r.ai_confidence < 0.6)
    
    avg_confidence = sum(r.ai_confidence for r in report_objects) / total_reports if total_reports > 0 else 0
    
    sentiment_counts = {}
    for report in report_objects:
        sentiment = report.ai_sentiment
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    category_counts = {}
    for report in report_objects:
        category = report.category.name
        category_counts[category] = category_counts.get(category, 0) + 1
    
    print(f"Total Reports: {total_reports}")
    print(f"Average AI Confidence: {avg_confidence:.2%}")
    print(f"High Confidence Reports (≥80%): {high_confidence_reports}")
    print(f"Medium Confidence Reports (60-79%): {medium_confidence_reports}")
    print(f"Low Confidence Reports (<60%): {low_confidence_reports}")
    print("\nSentiment Analysis:")
    for sentiment, count in sentiment_counts.items():
        print(f"  {sentiment.title()}: {count}")
    print("\nCategory Distribution:")
    for category, count in category_counts.items():
        print(f"  {category}: {count}")
    
    print("\n🎉 Demo data generation completed successfully!")
    print("\n📋 NEXT STEPS:")
    print("1. Run the development server: python manage.py runserver")
    print("2. Access the AI Dashboard at: http://localhost:8000/dashboard/ai-dashboard/")
    print("3. Test the AI Chatbot at: http://localhost:8000/dashboard/ai-chatbot/")
    print("4. View AI Report Analysis by clicking on any report")
    print("5. Check AI Predictive Insights at: http://localhost:8000/dashboard/ai-predictive-insights/")
    
    print("\n🔑 LOGIN CREDENTIALS:")
    print("Demo users created with password: 'demo123'")
    for user_data in demo_users:
        print(f"  Username: {user_data['username']}")


if __name__ == '__main__':
    create_demo_data()