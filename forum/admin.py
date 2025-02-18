from django.contrib import admin
from .models import (
    Post, Comment, Conversation, Message, Notification,
    ProjectUpdate, Poll, PollOption, GovernmentNotification,
    DepartmentPost, Feedback
)

# Register your models here
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Notification)
admin.site.register(ProjectUpdate)
admin.site.register(Poll)
admin.site.register(PollOption)
admin.site.register(GovernmentNotification)
admin.site.register(DepartmentPost)
admin.site.register(Feedback)
