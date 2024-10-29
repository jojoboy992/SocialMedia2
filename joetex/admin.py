from django.contrib import admin
from .models import Post, Comment, Reply

class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at')  # Adjust fields to display in the admin list view
    search_fields = ('title',)  # Enable search on the title field

class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'profile', 'created_at')
    list_filter = ('post', 'profile')  # Filter comments by post and profile

class ReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'user', 'created_at')
    list_filter = ('comment', 'user')  # Filter replies by comment and user

# Register the models with the admin site
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Reply, ReplyAdmin)