# forum/urls.py
from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    # Post and Feed
    path('', views.feed, name='feed'),
    path("post/new/", views.create_post, name="create_post"),
    path("post/<int:post_id>/", views.post_detail, name="post_detail"),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path("post/<int:post_id>/comment/", views.add_comment, name="add_comment"),
    path('post/<int:post_id>/vote/', views.vote_post, name='vote_post'),

    # Follow User
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    # Notifications
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_as_read, name="mark_as_read"),

    # Messaging
    path("messages/", views.inbox, name="inbox"),
    path("messages/<str:username>/", views.chat_room, name="chat_room"),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
]