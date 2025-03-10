from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Profile, FriendRequest, ChatMessage, Post, Comment
from django.utils.dateparse import parse_date
from django.http import JsonResponse
from django.db.models import Q
from .utils import send_friend_request_email
from google.generativeai import GenerativeModel
import google.generativeai as genai
import os

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = GenerativeModel('gemini-pro')

def handle_profile_pic_update(profile, new_pic):
    """Handle profile picture update and cleanup"""
    try:
        old_profile = Profile.objects.get(id=profile.id)
        if old_profile.profile_pic != new_pic and old_profile.profile_pic != 'profile_pics/default.png':
            old_profile.profile_pic.delete(save=False)
    except Profile.DoesNotExist:
        pass

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already exists'})
        
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('profile_setup')
    
    return render(request, 'signup.html')

@login_required
def profile_setup_view(request):
    # Redirect superusers to admin panel
    if request.user.is_superuser:
        return redirect('admin:index')
        
    if request.method == 'POST':
        profile = request.user.profile
        
        if 'profile_pic' in request.FILES:
            new_pic = request.FILES['profile_pic']
            handle_profile_pic_update(profile, new_pic)
            profile.profile_pic = new_pic
        
        profile.email = request.POST.get('email', '')
        profile.bio = request.POST.get('bio', '')
        profile.location = request.POST.get('location', '')
        profile.gender = request.POST.get('gender', 'N')
        birth_date = request.POST.get('birth_date')
        if birth_date:
            profile.birth_date = parse_date(birth_date)
        profile.website = request.POST.get('website', '')
        
        try:
            profile.save()
            return redirect('landing')
        except Exception as e:
            print(f"Error saving profile: {e}")
            return render(request, 'profile_setup.html', {'error': 'Error saving profile'})
    
    return render(request, 'profile_setup.html')

@login_required
def landing_view(request):
    if request.user.is_superuser:
        return redirect('admin:index')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        if content:
            post = Post.objects.create(
                user=request.user,
                content=content,
                image=image
            )
            return redirect('landing')
    
    posts = Post.objects.select_related('user', 'user__profile').prefetch_related('likes').all()
    return render(request, 'landing.html', {'posts': posts})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin:index')
            return redirect('landing')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    # Redirect superusers to admin panel
    if request.user.is_superuser:
        return redirect('admin:index')
    return render(request, 'profile.html')

def home_view(request):
    if request.user.is_authenticated:
        return redirect('landing')
    return render(request, 'homebef.html')

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
    else:
        users = []
    
    return render(request, 'search_results.html', {
        'users': users,
        'query': query
    })

@login_required
def send_friend_request(request, user_id):
    if request.method == 'POST':
        to_user = User.objects.get(id=user_id)
        
        # Check if request already exists
        if not FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=request.user)
        ).exists():
            # Create friend request
            FriendRequest.objects.create(
                from_user=request.user,
                to_user=to_user
            )
            
            # Send email notification
            send_friend_request_email(request.user, to_user)
                    
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def handle_friend_request(request, request_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        friend_request = FriendRequest.objects.get(id=request_id)
        
        if friend_request.to_user == request.user:
            if action == 'accept':
                friend_request.status = 'accepted'
            elif action == 'reject':
                friend_request.status = 'rejected'
            friend_request.save()
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

def get_friend_requests(request):
    """Context processor for friend requests"""
    try:
        if request.user.is_authenticated:
            friend_requests = FriendRequest.objects.filter(
                to_user=request.user,
                status='pending'
            ).select_related('from_user').order_by('-created_at')
            return {
                'friend_requests': friend_requests,
                'has_notifications': friend_requests.exists()
            }
    except:
        pass
    
    return {
        'friend_requests': [],
        'has_notifications': False
    }

@login_required
def friends_view(request):
    # Get all accepted friend requests where the user is either the sender or receiver
    accepted_requests = FriendRequest.objects.filter(
        (Q(from_user=request.user) | Q(to_user=request.user)) &
        Q(status='accepted')
    )
    
    # Get the friend users from the requests
    friends = []
    for fr in accepted_requests:
        if fr.from_user == request.user:
            friends.append(fr.to_user)
        else:
            friends.append(fr.from_user)
    
    # Get all users who are not friends and not the current user
    # Also exclude users who already have pending friend requests
    pending_requests = FriendRequest.objects.filter(
        (Q(from_user=request.user) | Q(to_user=request.user)) &
        Q(status='pending')
    )
    pending_users = [fr.from_user if fr.to_user == request.user else fr.to_user 
                    for fr in pending_requests]
    
    available_users = User.objects.exclude(
        Q(id=request.user.id) |
        Q(id__in=[friend.id for friend in friends]) |
        Q(id__in=[user.id for user in pending_users])
    )
    
    return render(request, 'friends.html', {
        'friends': friends,
        'available_users': available_users
    })

@login_required
def chatroom_view(request, friend_id):
    try:
        friend = User.objects.get(id=friend_id)
        # Verify that they are actually friends
        if not FriendRequest.objects.filter(
            (Q(from_user=request.user, to_user=friend) | Q(from_user=friend, to_user=request.user)),
            status='accepted'
        ).exists():
            return redirect('friends')
        
        # Get chat messages
        messages = ChatMessage.objects.filter(
            (Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user))
        ).order_by('timestamp')
        
        return render(request, 'chatroom.html', {
            'friend': friend,
            'messages': messages
        })
    except User.DoesNotExist:
        return redirect('friends')

@login_required
def like_post(request, post_id):
    if request.method == 'POST':
        post = Post.objects.get(id=post_id)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': post.likes_count()
        })
    return JsonResponse({'status': 'error'})

@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            post = Post.objects.get(id=post_id)
            comment = Comment.objects.create(
                post=post,
                user=request.user,
                content=content
            )
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'content': comment.content,
                    'username': comment.user.username,
                    'created_at': comment.created_at.strftime('%b %d, %Y %I:%M %p'),
                    'user_pic': comment.user.profile.profile_pic.url
                }
            })
    return JsonResponse({'status': 'error'})

@login_required
def hivebot_chat(request):
    if request.method == 'POST':
        try:
            user_message = request.POST.get('message', '')
            
            # Add system prompt to guide the bot's behavior
            system_prompt = """You are HiveBot, a helpful AI assistant for HiveNet social media platform. 
            Your main role is to help users format and improve their text content. 
            Keep responses concise and friendly."""
            
            # Generate response using Gemini
            response = model.generate_content(f"{system_prompt}\nUser: {user_message}")
            
            return JsonResponse({
                'status': 'success',
                'response': response.text
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
