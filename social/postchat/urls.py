from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('landing/', views.landing_view, name='landing'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/setup/', views.profile_setup_view, name='profile_setup'),
    path('profile/', views.profile_view, name='profile'),
    path('search/', views.search_users, name='search_users'),
    path('friend-request/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/handle/<int:request_id>/', views.handle_friend_request, name='handle_friend_request'),
    path('friends/', views.friends_view, name='friends'),
    path('chat/<int:friend_id>/', views.chatroom_view, name='chatroom'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('hivebot/chat/', views.hivebot_chat, name='hivebot_chat'),
] 