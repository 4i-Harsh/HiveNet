from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Profile, FriendRequest
from django.utils.dateparse import parse_date
from django.http import JsonResponse
from django.db.models import Q

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
    # Redirect superusers to admin panel
    if request.user.is_superuser:
        return redirect('admin:index')
    return render(request, 'landing.html')

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
            FriendRequest.objects.create(
                from_user=request.user,
                to_user=to_user
            )
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

@login_required
def get_friend_requests(request):
    """Context processor for friend requests"""
    if request.user.is_authenticated:
        friend_requests = FriendRequest.objects.filter(
            to_user=request.user,
            status='pending'
        ).select_related('from_user').order_by('-created_at')
        return {'friend_requests': friend_requests}
    return {'friend_requests': []}
