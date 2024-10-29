# models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django.conf import settings


class Post(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to="images/", blank=True, null=True)
    video = models.FileField(upload_to="videos/", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def time_since_created(self):
        now = timezone.now()
        time_diff = now - self.created_at

        if time_diff < timedelta(minutes=1):
            return f"{int(time_diff.seconds)}s ago"
        elif time_diff < timedelta(hours=1):
            return f"{int(time_diff.seconds // 60)}m ago"
        elif time_diff < timedelta(days=1):
            return f"{int(time_diff.seconds // 3600)}h ago"
        elif time_diff < timedelta(weeks=1):
            return f"{int(time_diff.days)}d ago"
        elif time_diff < timedelta(days=30):
            return f"{int(time_diff.days // 7)}w ago"
        elif time_diff < timedelta(days=365):
            return f"{int(time_diff.days // 30)}mo ago"
        else:
            return f"{int(time_diff.days // 365)}y ago"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "post")  # Ensure a user can like a post only once

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=150, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to="media/", null=True, blank=True)

    def __str__(self):
        return self.user.username


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="comment_replies",
        on_delete=models.CASCADE,
    )
    liked_heart = models.BooleanField(default=False)
    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(
        default=0
    )  # Add this line to track replies

    def __str__(self):
        return f"Comment by {self.profile.user.username} on {self.post.title}"

    def time_since_created(self):
        now = timezone.now()
        time_diff = now - self.created_at

        if time_diff < timedelta(minutes=1):
            return f"{int(time_diff.seconds)}s ago"
        elif time_diff < timedelta(hours=1):
            return f"{int(time_diff.seconds // 60)}m ago"
        elif time_diff < timedelta(days=1):
            return f"{int(time_diff.seconds // 3600)}h ago"
        elif time_diff < timedelta(weeks=1):
            return f"{int(time_diff.days)}d ago"
        elif time_diff < timedelta(days=30):
            return f"{int(time_diff.days // 7)}w ago"
        elif time_diff < timedelta(days=365):
            return f"{int(time_diff.days // 30)}mo ago"
        else:
            return f"{int(time_diff.days // 365)}y ago"


class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, related_name="likes", on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            "user",
            "comment",
        )  # Ensure a user can like a comment only once

    def __str__(self):
        return f"{self.user.username} likes a comment by {self.comment.profile.user.username}"


class Reply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Links to the User model
    comment = models.ForeignKey(
        Comment, related_name="replies", on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    like_count = models.PositiveIntegerField(default=0)  # Track the number of likes

    def __str__(self):
        return f"Reply by {self.user.username} to Comment {self.comment.id}"

    def time_since_created(self):
        now = timezone.now()
        time_diff = now - self.created_at

        if time_diff < timedelta(minutes=1):
            return f"{int(time_diff.seconds)}s ago"
        elif time_diff < timedelta(hours=1):
            return f"{int(time_diff.seconds // 60)}m ago"
        elif time_diff < timedelta(days=1):
            return f"{int(time_diff.seconds // 3600)}h ago"
        elif time_diff < timedelta(weeks=1):
            return f"{int(time_diff.days)}d ago"
        elif time_diff < timedelta(days=30):
            return f"{int(time_diff.days // 7)}w ago"
        elif time_diff < timedelta(days=365):
            return f"{int(time_diff.days // 30)}mo ago"
        else:
            return f"{int(time_diff.days // 365)}y ago"


class ReplyLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.ForeignKey("Reply", related_name="likes", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "reply")


class Follow(models.Model):
    follower = models.ForeignKey(
        User, related_name="following", on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User, related_name="followers", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.sender.username} to {self.receiver.username}: {self.content[:20]}"
        )
