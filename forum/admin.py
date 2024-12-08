from django.contrib import admin
from .models import (
    Post, Comment, Conversation, Message, Notification,
    ProjectUpdate, Poll, PollOption, GovernmentNotification, DepartmentPost, Feedback
)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'vote_count')
    list_filter = ('created_at',)
    search_fields = ('title', 'content', 'author__username')
    raw_id_fields = ('author', 'upvotes', 'downvotes', 'shared_by')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'author', 'post', 'created_at', 'vote_count', 'is_parent')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'post__title')
    raw_id_fields = ('author', 'post', 'parent_comment', 'upvotes', 'downvotes')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_updated', 'participant_count')
    raw_id_fields = ('participants',)

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('content', 'sender', 'conversation', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('content', 'sender__username')
    raw_id_fields = ('sender', 'conversation')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message', 'user__username')


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'department', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'author__username', 'department__department_name')


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'department', 'created_at')
    search_fields = ('title', 'created_by__username', 'department__department_name')


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ('poll', 'option_text', 'votes')
    search_fields = ('poll__title', 'option_text')


@admin.register(GovernmentNotification)
class GovernmentNotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'department', 'is_broadcast', 'created_at')
    list_filter = ('is_broadcast',)
    search_fields = ('message', 'department__department_name')


@admin.register(DepartmentPost)
class DepartmentPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'department', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'content', 'author__username', 'department__department_name')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'project_update', 'created_at')
    search_fields = ('content', 'user__username', 'department__department_name')
    raw_id_fields = ('user', 'department', 'project_update')


# Optional: Customize the Admin Site header
admin.site.site_header = "Forums Admin Panel"
admin.site.site_title = "Forums Administration"
admin.site.index_title = "Manage Forums Data"

