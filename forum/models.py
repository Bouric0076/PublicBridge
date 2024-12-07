import os
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

def upload_to(instance, filename):
    """Generate a dynamic upload path for media files."""
    return os.path.join('uploads', filename)


# Post Model
class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    media = models.FileField(upload_to="post_media/", blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.ManyToManyField(User, related_name="upvoted_posts", blank=True)
    downvotes = models.ManyToManyField(User, related_name="downvoted_posts", blank=True)
    shared_by = models.ManyToManyField(User, related_name="shared_posts", blank=True)

    def __str__(self):
        return self.title

    def vote_count(self):
        return self.upvotes.count() - self.downvotes.count()


# Comment Model
class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(default="No content")  # Default text for empty comments
    media = models.FileField(upload_to="comment_media/", blank=True, null=True)
    parent_comment = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    upvotes = models.ManyToManyField(User, related_name="upvoted_comments", blank=True)
    downvotes = models.ManyToManyField(User, related_name="downvoted_comments", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Helper fields
    depth = models.PositiveIntegerField(default=0)  # For nesting levels

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    def save(self, *args, **kwargs):
        """
        Automatically set the depth of the comment based on the parent comment.
        Top-level comments have a depth of 0; replies are incremented accordingly.
        """
        if self.parent_comment:
            self.depth = self.parent_comment.depth + 1
        else:
            self.depth = 0
        super().save(*args, **kwargs)

    def vote_count(self):
        return self.upvotes.count() - self.downvotes.count()

    def is_parent(self):
        """
        Returns True if the comment is a top-level comment.
        """
        return self.parent_comment is None

    def get_replies(self):
        """
        Returns all replies to this comment.
        """
        return self.replies.all().order_by("created_at")

# Conversation Model (for private messaging)
class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name="conversations")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation between {', '.join([user.username for user in self.participants.all()])}"

# Message Model
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    media = models.FileField(upload_to="message_media/", blank=True, null=True)  # Optional media in messages
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

# Notification Model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:30]}"

    class Meta:
        ordering = ["-created_at"]

# Government-Specific Models
class ProjectUpdate(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_updates"
    )
    department = models.ForeignKey(
        'users.GovernmentAdmin',
        on_delete=models.CASCADE,
        related_name="updates"
    )
    milestone = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed'),
        ],
        default='Pending',
    )
    media = models.FileField(upload_to="project_update_media/", blank=True, null=True)  # Added media support
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.department.department_name})"

class Poll(models.Model):
    title = models.CharField(max_length=255)
    question = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_polls"
    )
    department = models.ForeignKey(
        'users.GovernmentAdmin',
        on_delete=models.CASCADE,
        related_name="polls"
    )
    media = models.FileField(upload_to="poll_media/", blank=True, null=True)  # Added media support
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Poll: {self.title} ({self.department.department_name})"

class PollOption(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="options"
    )
    option_text = models.CharField(max_length=255)
    votes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.poll.title} - {self.option_text}"

class GovernmentNotification(models.Model):
    department = models.ForeignKey(
        'users.GovernmentAdmin',
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    target_audience = models.TextField(blank=True, null=True)
    message = models.TextField()
    is_broadcast = models.BooleanField(default=True)
    media = models.FileField(upload_to="notification_media/", blank=True, null=True)  # Added media support
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification from {self.department.department_name}"

class DepartmentPost(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="department_posts"
    )
    department = models.ForeignKey(
        'users.GovernmentAdmin',
        on_delete=models.CASCADE,
        related_name="department_posts"
    )
    category = models.CharField(
        max_length=50,
        choices=[
            ('Health', 'Health'),
            ('Education', 'Education'),
            ('Infrastructure', 'Infrastructure'),
            ('Economy', 'Economy'),
        ],
        default='General',
    )
    media = models.FileField(upload_to="department_post_media/", blank=True, null=True)  # Added media support
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.department.department_name})"

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feedbacks")
    department = models.ForeignKey(
        'users.GovernmentAdmin',
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )
    project_update = models.ForeignKey(
        ProjectUpdate,
        on_delete=models.CASCADE,
        related_name="feedbacks",
        blank=True,
        null=True
    )
    content = models.TextField()
    media = models.FileField(upload_to="feedback_media/", blank=True, null=True)  # Added media support
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.username} to {self.department.department_name}"
