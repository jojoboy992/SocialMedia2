from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .forms import *
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .models import *
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse,reverse_lazy
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count,F
import json
from django.conf import settings
import mimetypes
import os

def is_not_authenticated(user):
    return not user.is_authenticated  # Allow access only if user is not authenticated


from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from .models import Post, Comment
from .forms import CommentForm, ReplyForm  # Import the ReplyForm

from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from .models import Post, Comment, Like
from .forms import CommentForm, ReplyForm
from .utils import time_since_creation


def serve_media(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, 'rb') as f:
            return HttpResponse(f.read(), content_type=mime_type or "application/octet-stream")
    else:
        raise Http404("Media file not found.")

@method_decorator(login_required, name="dispatch")
class HomePage(LoginRequiredMixin, ListView):
    model = Post
    template_name = "index.html"
    context_object_name = "posts"
    ordering = ["-created_at"]
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pre-fetch liked IDs for posts, comments, and replies by the current user
        liked_post_ids = set(Like.objects.filter(user=self.request.user).values_list("post_id", flat=True))
        liked_comment_ids = set(CommentLike.objects.filter(user=self.request.user).values_list("comment_id", flat=True))
        liked_reply_ids = set(ReplyLike.objects.filter(user=self.request.user).values_list("reply_id", flat=True))

        # Fetch the current user's profile picture
        user_profile_picture = (
            self.request.user.profile.profile_picture.url
            if hasattr(self.request.user, 'profile') and self.request.user.profile.profile_picture
            else static("imgs/profile.png")
        )
        context['user_profile_picture'] = user_profile_picture

        # Retrieve followers and following information
        profile_user = self.request.user
        followers = User.objects.filter(following__following=profile_user)  # Users who follow the current user
        following_users = User.objects.filter(followers__follower=profile_user)  # Users that the current user follows

        # Add followers, following users, and is_following status
        context['followers'] = followers
        context['following_users'] = following_users
        context['is_following'] = following_users.exists()  # Check if following any users

        # Process each post in context
        for post in context["posts"]:
            post.like_count = get_like_count(post.id)
            post.is_liked = post.id in liked_post_ids

            # Fetch comments and their replies efficiently
            post.comments_list = post.comments.prefetch_related('user', 'comment_replies__user').all()
            post.comment_count = post.comments.count()  # Count only top-level comments

            # Calculate the total number of replies across all comments
            post.reply_count = sum(comment.reply_count for comment in post.comments_list)
            print(f"Post ID: {post.id}, Total Replies Counted: {post.reply_count}")

            # Total comments include both top-level comments and replies
            post.total_comments_count = post.comment_count + post.reply_count

            post.time_since_creation = post.time_since_created()

            # Process each comment in post's comments list
            for comment in post.comments_list:
                comment.time_since_creation = comment.time_since_created()
                comment.is_liked = comment.id in liked_comment_ids
                comment.liked_heart = comment.is_liked
                comment.reply_count = comment.reply_count  # Use signal-updated reply count

                # Print the expected and actual reply count (if you have an expected count)
                expected_count = comment.reply_count  # Example: you might have a different logic for this
                print(f"Comment ID: {comment.id}, Expected Reply Count: {expected_count}, Actual Reply Count: {comment.reply_count}")

                comment.replies_list = comment.comment_replies.all().select_related('user')
                # Access the username directly from the user field
                comment.username = comment.user.username
                comment.profile_picture = (
                    comment.user.profile.profile_picture.url if hasattr(comment.user, 'profile') and comment.user.profile.profile_picture else static("imgs/profile.png")
                )

                # Process each reply in comment's replies list
                for reply in comment.replies_list:
                    reply.time_since_creation = reply.time_since_created()
                    reply.like_count = reply.likes.count()  # Count likes for each reply
                    reply.is_liked = reply.id in liked_reply_ids  # Check if user liked the reply
                    reply.username = reply.user.username
                    reply.profile_picture = (
                        reply.user.profile.profile_picture.url if hasattr(reply.user, 'profile') and reply.user.profile.profile_picture else static("imgs/profile.png")
                    )
            print(f"Post ID: {post.id}, Comment Count: {post.comment_count}, Reply Count: {post.reply_count}, Total Count: {post.total_comments_count}")
            # Print each comment's reply count again for thoroughness
            for comment in post.comments_list:
                print(f"Comment ID: {comment.id}, Reply Count: {comment.comment_replies.count()}")
        
        return context
    
class PostDeleteView(DeleteView):
    model = Post
    template_name = 'post_confirm_delete.html'  # Create this template for confirmation
    success_url = reverse_lazy('home')     

@login_required
def comment_count_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comment_count = post.comments.count()
    return JsonResponse({'comment_count': comment_count})

@login_required
def reply_count_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    reply_count = comment.comment_replies.count()
    return JsonResponse({'reply_count': reply_count})


@login_required
def add_comment(request):
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        post = get_object_or_404(Post, id=post_id)

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.user = request.user  # Set the user for the comment

            # Set the profile based on the user
            if hasattr(request.user, 'profile'):
                comment.profile = request.user.profile  # Set the profile if it exists
            else:
                return JsonResponse({"success": False, "error": "User profile not found."})

            comment.save()

            return JsonResponse(
                {
                    "success": True,
                    "comment": {
                        "id": comment.id,
                        "content": comment.content,
                        "profile_picture": (
                            comment.profile.profile_picture.url
                            if comment.profile.profile_picture
                            else static("imgs/profile.png")
                        ),
                        "username": comment.user.username,
                        "post_time": "Just now",
                        "likes": 0,
                    },
                }
            )

        return JsonResponse({"success": False, "error": "Invalid form submission."})

    return JsonResponse({"success": False, "error": "Only POST requests are allowed."})

@login_required
def add_reply(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)
        parent_comment_id = request.POST.get("parent_comment_id")
        parent_comment = get_object_or_404(Comment, id=parent_comment_id)
        reply_content = request.POST.get("reply_content")

        # Validation
        if not reply_content or len(reply_content) > 300:  # Example limit
            return JsonResponse({"success": False, "error": "Invalid reply content"}, status=400)

        # Create and save the reply
        reply = Reply(
            user=request.user,
            comment=parent_comment,
            content=reply_content
        )
        reply.save()

        # Update reply count (this should already be handled by signals, but if needed)
        parent_comment.reply_count = parent_comment.comment_replies.count()
        parent_comment.save()

        print(f"Reply added: {reply.id} to Comment ID: {parent_comment.id} by User: {reply.user.username}")  # Debugging line

        return JsonResponse(
            {
                "success": True,
                "reply_content": reply.content,
                "username": reply.user.username,
                "profile_picture": (
                    reply.user.profile.profile_picture.url
                    if hasattr(reply.user, 'profile') and reply.user.profile.profile_picture
                    else static("imgs/profile.png")
                ),
            }
        )
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


# View for creating a new post
@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("home")
    else:
        form = PostForm()
    return render(request, "new_post.html", {"form": form})


# View for updating an existing post
@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("post_detail", pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, "your_app/post_form.html", {"form": form})


# View for displaying a single post
@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "your_app/post_detail.html", {"post": post})


# Signup View
@user_passes_test(
    is_not_authenticated, login_url="home"
)  # Redirect to home if user is authenticated
def signup(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log the user in after signup
            return redirect("home")  # Redirect to a desired page after signup
    else:
        form = CustomSignupForm()
    return render(request, "signup.html", {"form": form})


# Login View
@user_passes_test(
    is_not_authenticated, login_url="home"
)  # Redirect to home if user is authenticated
def login_view(request):
    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("home")  # Redirect to a desired page after login
        else:
            # Capture specific errors from form validation
            if form.errors:
                for field in form:
                    if field.errors:
                        for error in field.errors:
                            form.add_error(field, error)  # Attach errors to form
    else:
        form = CustomLoginForm()
    return render(request, "login.html", {"form": form})

def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user.is_authenticated:
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()  # Unlike if already liked
            liked = False
        else:
            liked = True

        # Get the updated like count
        count = post.like_set.count()
        formatted_count = format_like_count(count)  # Format the like count

        return JsonResponse(
            {"liked": liked, "count": formatted_count}
        )  # Return formatted count

    return JsonResponse({"error": "You must be logged in to like a post."}, status=401)

def get_like_count(post_id):
    # Always get the count from the database
    post = get_object_or_404(Post, id=post_id)
    like_count = post.like_set.count()
    return like_count

def like_count(request, post_id):
    if request.method == "GET":
        count = get_like_count(post_id)
        return JsonResponse({"count": count})

def format_like_count(count):
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"  # Format for millions
    elif count >= 1_000:
        return f"{count / 1_000:.1f}k"  # Format for thousands
    return str(count)

@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Get or create the like
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)

    # Update the comment's like count
    if created:
        comment.like_count += 1  # Increment if a new like was created
        liked = True
    else:
        like.delete()  # Unlike if already liked
        comment.like_count -= 1  # Decrement if unliked
        liked = False

    comment.save()  # Save the updated like count

    # Return updated like count
    response_data = {
        "liked": liked,
        "count": comment.like_count  # Ensure you return the updated count from the comment
    }
    print(response_data)  # Debugging output
    return JsonResponse(response_data)

@login_required
@require_POST
def like_reply(request, reply_id):
    print(f"Attempting to like reply with ID: {reply_id}")  # Debug output
    try:
        reply = get_object_or_404(Reply, id=reply_id)
    except Reply.DoesNotExist:
        print(f"Reply with ID {reply_id} does not exist.")
        return JsonResponse({"error": "Reply not found"}, status=404)

    like, created = ReplyLike.objects.get_or_create(user=request.user, reply=reply)

    if created:
        reply.like_count += 1
        reply.save()
        return JsonResponse({"liked": True, "like_count": reply.like_count})
    else:
        like.delete()
        reply.like_count -= 1
        reply.save()
        return JsonResponse({"liked": False, "like_count": reply.like_count})


def format_like_count(count):
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"  # Format for millions
    elif count >= 1_000:
        return f"{count / 1_000:.1f}k"  # Format for thousands
    return str(count)



@login_required
def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=profile_user)
    post_count = user_posts.count()

    # Check if the logged-in user is following the profile user
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    # Retrieve the user's profile
    profile = get_object_or_404(Profile, user=profile_user)

    # Get followers and following users
    followers = profile_user.followers.all()  # Users who follow this profile
    following_users = request.user.following.all()  # Users that the logged-in user follows

    return render(
        request,
        "profile.html",
        {
            "profile_user": profile_user,
            "user_posts": user_posts,
            "post_count": post_count,
            "is_following": is_following,
            "profile": profile,
            "followers": followers,  # Pass the followers
            "following_users": following_users,  # Pass the following users
        },
    )


@login_required
def edit_profile(request):
    # Use the currently logged-in user
    user = request.user

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect(
                "profile", username=user.username
            )  # Redirect to the user's profile page
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=user.profile)

    return render(
        request,
        "edit_profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )

@login_required
def follow(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if request.user != user_to_follow:
        Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    return redirect('profile', username=username)

@login_required
def unfollow(request, username):
    profile_user = get_object_or_404(User, username=username)

    # Assuming you have a Follow model to manage the followers
    follow_relationship = Follow.objects.filter(follower=request.user, following=profile_user).first()
    if follow_relationship:
        follow_relationship.delete()  # Remove the follow relationship

    # Check where the form was submitted from and redirect accordingly
    if request.POST.get("from_page") == "following_list":
        return redirect('home')  # Redirect to homepage after unfollowing from 'Users you follow' page
    else:
        return redirect('profile', username=profile_user.username)  # 


@login_required
def chat_view(request, username=None):
    # Get users who have either sent or received messages with the logged-in user
    users = User.objects.filter(
        Q(sent_messages__receiver=request.user) | Q(received_messages__sender=request.user)
    ).exclude(username=request.user.username).distinct().annotate(
        unread_messages=Count(
            'sent_messages',
            filter=Q(sent_messages__receiver=request.user, sent_messages__is_read=False)
        )
    )

    selected_user = None
    messages = []

    # Fetch the current user's profile picture
    user_profile_picture = (
        request.user.profile.profile_picture.url if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.profile_picture else static("imgs/profile.png")
    )

    if username:
        # Get the selected user for the chat
        selected_user = get_object_or_404(User, username=username)

        # Prevent sending messages to oneself
        if selected_user == request.user:
            selected_user = None  # Reset if selected user is the current user

        # Retrieve all messages exchanged with the selected user
        messages = Message.objects.filter(
            Q(sender=request.user, receiver=selected_user) |
            Q(sender=selected_user, receiver=request.user)
        ).order_by('timestamp')

        # Mark received messages as read
        received_messages = messages.filter(sender=selected_user, receiver=request.user, is_read=False)
        
        # Update messages as read only if there are any
        if received_messages.exists():
            received_messages.update(is_read=True)

    return render(request, 'messages.html', {
        'users': users,
        'selected_user': selected_user,  # Will be None if no valid user is selected
        'messages': messages,
        'user_profile_picture': user_profile_picture,  # Pass the profile picture to the template
    })

@require_POST
def send_message(request):
    import json
    data = json.loads(request.body)
    
    recipient_username = data.get('recipient')
    message_content = data.get('message')
    
    if recipient_username and message_content:
        recipient = get_object_or_404(User, username=recipient_username)
        message = Message.objects.create(
            sender=request.user,
            receiver=recipient,
            content=message_content,
            timestamp=timezone.now()
        )
        return JsonResponse({'status': 'success', 'message_id': message.id})

    return JsonResponse({'status': 'error'}, status=400)



def fetch_messages(request, username):
    selected_user = get_object_or_404(User, username=username)

    # Retrieve all messages exchanged with the selected user
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=selected_user) |
        Q(sender=selected_user, receiver=request.user)
    ).order_by('timestamp')

    # Include the delete permission for each message
    messages_data = [{
        'id': message.id,
        'sender': message.sender.username,
        'content': message.content,
        'can_delete': message.sender == request.user  # Only the sender can delete
    } for message in messages]

    return JsonResponse(messages_data, safe=False)


@require_POST
@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    
    message.delete()
    
    return JsonResponse({'status': 'success'})

def user_search(request):
    query = request.GET.get('query', '').strip()
    users = User.objects.filter(username__icontains=query) if query else []

    # Fetch the current user's profile picture
    user_profile_picture = (
        request.user.profile.profile_picture.url if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.profile_picture else static("imgs/profile.png")
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_data = []
        for user in users:
            profile = getattr(user, 'profile', None)
            profile_picture_url = profile.profile_picture.url if profile and profile.profile_picture else '/static/imgs/profile.png'  # Default image
            user_data.append({
                'username': user.username,
                'profile_picture': profile_picture_url
            })
        return JsonResponse({'users': user_data, 'user_profile_picture': user_profile_picture})
    else:
        return render(request, 'user_search.html', {'users': users, 'user_profile_picture': user_profile_picture})

@login_required
def logout_view(request):
    logout(request)  # Log out the user
    return redirect("login")


