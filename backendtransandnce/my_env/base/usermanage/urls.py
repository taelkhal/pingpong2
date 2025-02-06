from django.urls import path
from .views import login_42, callback_42,RegistrationView, LoginView, ProfileUpdateView, SendFriendRequestView, AcceptFriendRequestView, FriendsListView
from . import views

urlpatterns = [
    path('42_login/', login_42.as_view(), name='login_42'),
    path('oauth/callback/', callback_42.as_view(), name='callback_42'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('send_friend_request/<int:user_id>/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path("friends/accept/<int:friend_request_id>/", AcceptFriendRequestView.as_view(), name="accept-friend-request"),
    path("friends/list/", FriendsListView.as_view(), name="friends-list"),
    path('users/', views.user_list, name='user_list'),
]