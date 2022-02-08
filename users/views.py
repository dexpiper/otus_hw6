import os

from django.shortcuts import render
from hasker.helpers import render_with_error
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from PIL import Image

from .models import Profile


def login_page(request, fallback=False):
    context = {}
    if not fallback:
        return render(request, 'users/login.html', context)
    else:
        return [request, 'users/login.html', context]


def do_login(request):
    username = request.POST['login']
    pwd = request.POST['password']
    user = authenticate(request, username=username, password=pwd)
    if user:
        login(request, user)
        context = {'user': user}
        return render(request, 'users/profile.html', context)
    else:
        return render_with_error(login_page, request, errormsg=(
            'Username or password is invalid'))


def profile(request, fallback=False):
    context = {}
    if not fallback:
        return render(request, 'users/profile.html', context)
    else:
        return [request, 'users/profile.html', context]


def save_profile(request):
    if not request.method == 'POST' and request.FILES == 'avatar':
        return render_with_error(profile, request, errormsg=(
            'Get wrong form'))
    avatar = request.FILES['avatar']
    # email = request.POST['email']
    fss = FileSystemStorage()
    file = fss.save(
        f'{request.user.username}_avatar.{avatar.name.split(".")[-1]}', avatar
    )
    user = User.objects.get(id=request.user.id)
    """if Profile.param_exists('email', email) and email != user.email:
        return render_with_error(profile, request, errormsg=(
            'There is a user with this e-mail'))"""
    user_profile = Profile.objects.get(user=user)
    user_profile.avatar = fss.url(file)
    user_profile.save()
    context = {}
    return render(request, 'users/profile.html', context)


def signup(request, fallback=False):
    context = {}
    if not fallback:
        return render(request, 'users/signup.html', context)
    else:
        return [request, 'users/signup.html', context]


def do_signup(request):
    try:
        username = request.POST['login']
        email = request.POST['email']
        pwd = request.POST['password']
        pwd_conf = request.POST['password-conf']
    except KeyError:
        return render_with_error(signup, request, errormsg=(
            'Some of the fields are empty'))
    if Profile.param_exists('username', username):
        return render_with_error(signup, request, errormsg=(
            'This username is occupied'))
    if Profile.param_exists('email', email):
        return render_with_error(signup, request, errormsg=(
            'There is a user with this e-mail'))
    if not pwd == pwd_conf:
        return render_with_error(signup, request, errormsg=(
            'Passwords do not match'))
    new_user = User.objects.create_user(username=username,
                                        email=email, password=pwd)
    new_user.save()
    try:
        user = authenticate(request, username=new_user, password=pwd)
    except Exception:
        return render_with_error(signup, request, errormsg=(
            'Internal auth error'))
    context = {'user': new_user}
    if user is not None:
        login(request, user)
        return render(request, 'users/profile.html', context)


def do_logout(request):
    logout(request)
    return render(request, 'questions/index.html', {})
