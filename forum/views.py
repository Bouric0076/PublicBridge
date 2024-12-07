from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Post, Comment, Notification
from .forms import PostForm, CommentForm
from .models import Conversation, Message
from .models import User
from users.models import Profile
from users.forms import ProfileForm
@login_required
def profile_view(request, username=None):
    # Get the user by username, or default to the logged-in user
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user

    # Fetch or create the user's profile
    profile, created = Profile.objects.get_or_create(user=user)

    # Handle profile update form (only for the logged-in user viewing their profile)
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

    # Fetch posts created by the user
    user_posts = Post.objects.filter(author=user).order_by('-created_at')

    return render(
        request,
        'forum/profile.html',
        {
            'form': form,
            'profile': profile,
            'posts': user_posts,
            'is_own_profile': user == request.user,  # Flag for editing permissions
        },
    )
# Create a post
@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("forum:feed")
    else:
        form = PostForm()
    return render(request, "forum/create_post.html", {"form": form})


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


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('forum:profile_view', username=request.user.username)

    return render(request, 'forum/delete_post.html', {'post': post})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.filter(parent_comment__isnull=True).order_by("-created_at")
    comment_form = CommentForm()
    return render(request, "forum/post_detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": comment_form
    })


# Add a comment or reply
@login_required
def add_comment(request, post_id):
    # Get the post object or return 404 if not found
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the comment instance without saving to the database
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post

            # Handle parent comment (reply case)
            parent_id = request.POST.get("parent_id")
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent_comment = parent_comment
                except Comment.DoesNotExist:
                    # Handle the case where the parent comment does not exist
                    return redirect("forum:post_detail", post_id=post.id)

            # Save the comment to the database
            comment.save()

            # Notification logic
            recipient = comment.parent_comment.author if comment.parent_comment else post.author
            if recipient != request.user:
                Notification.objects.create(
                    user=recipient,
                    message=f"{request.user.username} commented on your post."
                )

            # Redirect to the post detail page after successful comment creation
            return redirect("forum:post_detail", post_id=post.id)

    # Redirect to the post detail page if the form is not valid or not a POST request
    return redirect("forum:post_detail", post_id=post.id)

# Upvote or downvote a post
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


# Notifications view
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

# Inbox view
@login_required
def inbox(request):
    conversations = request.user.conversations.all().order_by("-last_updated")
    return render(request, "forum/inbox.html", {"conversations": conversations})

# Chat room view
@login_required
def chat_room(request, username):
    other_user = get_object_or_404(User, username=username)
    conversation, created = Conversation.objects.get_or_create(participants=request.user)
    return render(request, "forum/chat_room.html", {"conversation": conversation, "other_user": other_user})

# Follow user
@login_required
def follow_user(request, user_id):
    # Fetch the target user
    user_to_follow = get_object_or_404(User, id=user_id)

    # Prevent users from following themselves
    if user_to_follow == request.user:
        return JsonResponse(
            {"status": "error", "message": "You cannot follow yourself."},
            status=400
        )

    # Get the current user's profile
    user_profile = request.user.profile

    # Check if already following
    if user_to_follow.profile in user_profile.following.all():
        return JsonResponse(
            {"status": "error", "message": f"You are already following {user_to_follow.username}."},
            status=400
        )

    # Add the user to the following list
    user_profile.following.add(user_to_follow.profile)

    return JsonResponse(
        {"status": "success", "message": f"You are now following {user_to_follow.username}."}
    )

@login_required
def feed(request):
    # Ensure the profile exists for the user
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Get the users that the current user is following
    following = profile.following.all()  # Correctly fetching the users that the current user is following

    if following.exists():
        posts = Post.objects.filter(author__in=following).order_by("-created_at")
    else:
        posts = Post.objects.all().order_by("-created_at")[:20]  # Return a limited set of posts if no one is followed

    suggested_users = User.objects.exclude(id__in=following.values_list('id', flat=True)).exclude(id=request.user.id)[:5]

    return render(request, "forum/feed.html", {"posts": posts, "suggested_users": suggested_users})