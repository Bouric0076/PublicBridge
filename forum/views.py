from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Post, Comment, Notification, Conversation, Message, User
from users.models import Profile
from .forms import PostForm, CommentForm
from users.forms import ProfileForm

# Profile View
@login_required
def profile_view(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user

    profile, created = Profile.objects.get_or_create(user=user)
    form = None

    if user == request.user:
        if request.method == 'POST':
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('forum:profile_view', username=user.username)
        else:
            form = ProfileForm(instance=profile)

    user_posts = Post.objects.filter(author=user).order_by('-created_at')
    return render(request, 'forum/profile.html', {
        'form': form,
        'profile': profile,
        'posts': user_posts,
        'is_own_profile': user == request.user,
    })

# Create a Post
@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect("forum:feed")
    else:
        form = PostForm()
    return render(request, "forum/create_post.html", {"form": form})

# Edit Post
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('forum:profile_view', username=request.user.username)
    else:
        form = PostForm(instance=post)
    return render(request, 'forum/edit_post.html', {'form': form, 'post': post})

# Delete Post
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('forum:profile_view', username=request.user.username)
    return render(request, 'forum/delete_post.html', {'post': post})

# Post Detail
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.filter(parent_comment__isnull=True).order_by("-created_at")
    comment_form = CommentForm()
    return render(request, "forum/post_detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": comment_form
    })

# Add Comment or Reply
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            parent_id = request.POST.get("parent_id")
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent_comment = parent_comment
                except Comment.DoesNotExist:
                    return redirect("forum:post_detail", post_id=post.id)
            comment.save()
            recipient = comment.parent_comment.author if comment.parent_comment else post.author
            if recipient != request.user:
                Notification.objects.create(
                    user=recipient,
                    message=f"{request.user.username} commented on your post."
                )
            return redirect("forum:post_detail", post_id=post.id)
    return redirect("forum:post_detail", post_id=post.id)

# Upvote or Downvote Post
@login_required
def vote_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    action = request.GET.get("action")
    if action == "upvote":
        post.upvotes.add(request.user)
        post.downvotes.remove(request.user)
    elif action == "downvote":
        post.downvotes.add(request.user)
        post.upvotes.remove(request.user)
    return JsonResponse({
        "upvotes": post.upvotes.count(),
        "downvotes": post.downvotes.count(),
    })

# Notifications
@login_required
def notifications(request):
    notifications = request.user.notifications.filter(is_read=False).order_by("-created_at")
    return render(request, "forum/notifications.html", {"notifications": notifications})

@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect("notifications")

# Inbox
@login_required
def inbox(request):
    conversations = request.user.conversations.all().order_by("-last_updated")
    return render(request, "forum/inbox.html", {"conversations": conversations})

# Chat Room
@login_required
def chat_room(request, username):
    other_user = get_object_or_404(User, username=username)
    conversation, created = Conversation.objects.get_or_create(participants=request.user)
    return render(request, "forum/chat_room.html", {"conversation": conversation, "other_user": other_user})

# Follow User
@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    if user_to_follow == request.user:
        return JsonResponse({"status": "error", "message": "You cannot follow yourself."}, status=400)
    user_profile = request.user.profile
    if user_to_follow.profile in user_profile.following.all():
        return JsonResponse({"status": "error", "message": f"You are already following {user_to_follow.username}."}, status=400)
    user_profile.following.add(user_to_follow.profile)
    return JsonResponse({"status": "success", "message": f"You are now following {user_to_follow.username}."})

# Feed
@login_required
def feed(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    following = profile.following.all()
    if following.exists():
        posts = Post.objects.filter(author__in=following).order_by("-created_at")
    else:
        posts = Post.objects.all().order_by("-created_at")[:20]
    suggested_users = User.objects.exclude(id__in=following.values_list('id', flat=True)).exclude(id=request.user.id)[:5]
    return render(request, "forum/feed.html", {"posts": posts, "suggested_users": suggested_users})
