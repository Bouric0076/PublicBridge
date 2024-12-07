from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_citizen = models.BooleanField(default=True)
    is_government_admin = models.BooleanField(default=False)
    engagement_score = models.IntegerField(default=0)

    def __str__(self):
        return self.username

class GovernmentAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department_name = models.CharField(max_length=255)  # Ministry/Department name
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.department_name}"


class Follow(models.Model):
    follower = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        related_name="following_set"
    )
    followed = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        related_name="followers_set"
    )

    def __str__(self):
        return f"{self.follower.user.username} follows {self.followed.user.username}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'followed'], name='unique_follow')
        ]

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
