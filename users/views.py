from django.shortcuts import redirect, render
from hasker.helpers import render_with_error
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage

from .models import Profile


def login_page(request, fallback=False):
    if not request.user.is_authenticated:
        context = {}
        if not fallback:
            return render(request, 'users/login.html', context)
        else:
            return [request, 'users/login.html', context]
    else:
        return redirect('users:profile')


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
    if not request.user.is_authenticated:
        render_with_error(do_login, request, errormsg='Please log in')
    context = {}
    if not fallback:
        return render(request, 'users/profile.html', context)
    else:
        return [request, 'users/profile.html', context]


def save_profile(request):
    context = {'submit_email': '', 'submit_avatar': ''}
    if not request.method == 'POST':
        return render_with_error(profile, request, errormsg=(
            'Internal form error. Please try again'))
    avatar = request.FILES.get('avatar', None)
    email = request.POST.get('email', None)
    email_alerts_status = request.POST.get('alerts', None)
    user = User.objects.get(id=request.user.id)
    if avatar:
        fss = FileSystemStorage()
        file = fss.save(
            f'{request.user.username}_avatar.{avatar.name.split(".")[-1]}',
            avatar
        )
        user.profile.avatar = fss.url(file)
        user.profile.save()
        context['submit_avatar'] = 'new avatar saved'
    if email:
        if email == user.email:
            pass
        elif Profile.param_exists('email', email):
            return render_with_error(profile, request, errormsg=(
                'There is a user with this e-mail'))
        else:
            user.email = email
            user.save()
            context['submit_email'] = 'new email saved, please reload page'
    if email_alerts_status is not None:
        if email_alerts_status == 'on':
            email_alerts_status = True
        else:
            email_alerts_status = False
        user.profile.send_email = email_alerts_status
        user.profile.save()
        context['submit_alert'] = 'email alerts changed'
    return render(request, 'users/profile.html', context)


def signup(request, fallback=False):
    context = {}
    if not fallback:
        return render(request, 'users/signup.html', context)
    else:
        return [request, 'users/signup.html', context]


def do_signup(request):
    if not request.method == 'POST':
        return render_with_error(profile, request, errormsg=(
            'Internal form error. Please try again'))
    username = request.POST.get('login', None)
    email = request.POST.get('email', None)
    pwd = request.POST.get('password', None)
    pwd_conf = request.POST.get('password-conf', None)

    # validation
    if not all((username, email, pwd, pwd_conf)):
        return render_with_error(signup, request, errormsg=(
            'Some fields are empty'))
    if Profile.param_exists('username', username):
        return render_with_error(signup, request, errormsg=(
            f'Username {username} is occupied'))
    if Profile.param_exists('email', email):
        return render_with_error(signup, request, errormsg=(
            f'There is a user with e-mail {email}. Is it you?'))
    if not pwd == pwd_conf:
        return render_with_error(signup, request, errormsg=(
            'Passwords do not match'))

    # creation
    new_user = User.objects.create_user(username=username,
                                        email=email, password=pwd)
    new_user.save()
    try:
        user = authenticate(request, username=new_user, password=pwd)
    except Exception:
        return render_with_error(signup, request, errormsg=(
            'Internal auth error: cannot authenticate new user'))
    context = {'user': new_user}
    if user is not None:
        login(request, user)
        return render(request, 'users/profile.html', context)


def do_logout(request):
    logout(request)
    return render(request, 'questions/index.html', {})
