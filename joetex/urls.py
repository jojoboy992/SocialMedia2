from django.urls import path
from .views import *
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('media/<path:path>', serve_media, name='serve_media'),  # Route media requests to the custom view
    path("", HomePage.as_view(), name="home"),
    path("signup/", signup, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("post/new/", views.post_new, name="post_new"),
    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path("post/<int:pk>/edit/", views.post_edit, name="post_edit"),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path("like/<int:post_id>/", like_post, name="like_post"),
    path("like-count/<int:post_id>/", like_count, name="like_count"),
    path("like_comment/<int:comment_id>/", views.like_comment, name="like_comment"),  # New URL for liking a comment
    path("like-reply/<int:reply_id>/", views.like_reply, name="like_reply"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/", views.profile, name="profile"),
    path('add-comment/', add_comment, name='add_comment'),
    path('add_reply/<int:post_id>/', add_reply, name='add_reply'),
    path('follow/<str:username>/', views.follow, name='follow'),
    path('unfollow/<str:username>/', views.unfollow, name='unfollow'),
    path('send_message/', send_message, name='send_message'),
    path('fetch_messages/<str:username>/', fetch_messages, name='fetch_messages'),
    path('messages/<str:username>/', chat_view, name='chat_view'),
    path('send_message/', send_message, name='send_message'),  # Endpoint to send messages
    path('fetch_messages/<str:username>/', fetch_messages, name='fetch_messages'),  # Endpoint to fetch messages
    path('search/', views.user_search, name='user_search'),
    path('delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
]

if not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)