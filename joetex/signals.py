from django.db.models.signals import post_save , post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import * # Adjust the import based on your project structure

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(post_save, sender=Reply)
def increase_reply_count(sender, instance, created, **kwargs):
    if created:
        comment = instance.comment
        comment.reply_count = comment.comment_replies.count()
        comment.save()

@receiver(post_delete, sender=Reply)
def decrease_reply_count(sender, instance, **kwargs):
    comment = instance.comment
    comment.reply_count = comment.comment_replies.count()
    comment.save()