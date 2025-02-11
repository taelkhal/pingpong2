from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated,AllowAny
from .models import Profile,FriendRequest,Friendship
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegistrationSerializer, LoginSerializer, ProfileSerializer, UserSerializer, RegistrationSerializer_42
import requests
import json

DEFAULT_AVATAR_URL = "https://upload.wikimedia.org/wikipedia/commons/7/7c/Profile_avatar_placeholder_large.png"

class login_42(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return redirect("https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-b292b631faa175f40c72f3c46c0648df398518e1cd514dc73a6a8014d4600584&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Foauth%2Fcallback%2F&response_type=code")

def save_to_json(data, file_path="data.json"):
    try:
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"An error occurred while saving data to {file_path}: {e}")

class callback_42(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        code = request.GET.get('code')
        token_url = 'https://api.intra.42.fr/oauth/token'
        data = {
            'grant_type': 'authorization_code',
            'client_id': "u-s4t2ud-b292b631faa175f40c72f3c46c0648df398518e1cd514dc73a6a8014d4600584",
            'client_secret': "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",
            'code': code,
            'redirect_uri': "http://localhost:8000/oauth/callback/",
        }
        response = requests.post(token_url, data=data)
        token_info = response.json()
        print(token_info)
        access_token = token_info.get('access_token')

        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        response = requests.get('https://api.intra.42.fr/v2/me', headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            user_data_serialized = {
            'username': user_data.get('login'),
            'email': user_data.get('email'),
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            }
            serializer = RegistrationSerializer_42(data=user_data_serialized)
            if serializer.is_valid():
                print(user_data.get('login'))
                avatar_urls = user_data.get("image", {}).get("link") or DEFAULT_AVATAR_URL
                print("Extracted avatar:", avatar_urls)    
                user = serializer.save()
                profile = Profile.objects.get(user=user)
                profile.avatar_url = avatar_urls
                profile.save()
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
            save_to_json(user_data)
            # redirect_url = f"http://127.0.0.1:5500/dashboard.html&access_token={access_token}"
            redirect_url = f"http://127.0.0.1:5500/#dashboard?access_token={access_token}"
            return redirect(redirect_url)
        else:
            return redirect("http://127.0.0.1:8000/?error")

        refresh = RefreshToken.for_user(user)

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            email = request.data.get('email')
            if User.objects.filter(email=email).exists():
                return Response({"error": "Email already exists"}, status=400)
            user = serializer.save()
            profile = Profile.objects.get(user=user)
            return Response({
                "message": "User registered successfully!",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "profile": {
                    "bio": profile.bio,
                    "email": profile.email,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "avatar": profile.avatar.url if profile.avatar else None,
                    "created_at": profile.created_at,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful",
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully!", "profile": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        sender = request.user
        receiver = get_object_or_404(User, id=user_id)

        if sender == receiver:
            return Response({"error": "You cannot send a friend request to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        friend_request, created = FriendRequest.objects.get_or_create(sender=sender, receiver=receiver)
        if created:
            return Response({"message": "Friend request sent successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Friend request already sent."}, status=status.HTTP_400_BAD_REQUEST)
    
class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, friend_request_id):
        # print("Authenticated user:", request.user)
        friend_request = get_object_or_404(         
            FriendRequest,
            # print("friendreq:", friend_request),
            id=friend_request_id,
            receiver=request.user,
            accepted=False
        )
        friend_request.accepted = True
        friend_request.save()

        Friendship.objects.create(user1=friend_request.sender, user2=friend_request.receiver)
        return Response({"message": "Friend request accepted."}, status=status.HTTP_200_OK)

# def get_friends(user):
#     friendships1 = Friendship.objects.filter(user1=user)
#     friendships2 = Friendship.objects.filter(user2=user)
#     friends = [f.user2 for f in friendships1] + [f.user1 for f in friendships2]
#     return friends

class FriendsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        sent_requests = FriendRequest.objects.filter(sender=user, accepted=True)
        received_requests = FriendRequest.objects.filter(receiver=user, accepted=True)
        
        friends = []
        for fr in sent_requests:
            friends.append(fr.receiver)
        for fr in received_requests:
            friends.append(fr.sender)
        
        friends = list(set(friends))
        
        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

def user_list(request):
    users = User.objects.all()
    data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
    return JsonResponse({'users': data}, status=200)