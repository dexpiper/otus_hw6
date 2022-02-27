from django.shortcuts import render
from hasker.helpers import render_with_error
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.views import LoginView, LogoutView

from .models import Profile
from .forms import ProfileForm
from .helpers import save_avatar, update_email, update_alerts


class Login(LoginView):
    template_name = 'users/login.html'


class Logout(LogoutView):
    template_name = 'users/logged_out.html'


@login_required
def profile(request):
    context = {}
    if request.method == 'POST':
        form = ProfileForm(request.POST, user=request.user)
        if form.is_valid():
            avatar = request.FILES.get('avatar', None)
            email = form.cleaned_data['email']
            alerts = form.cleaned_data['alerts']
            email_updated = update_email(request, email)
            alerts_updated = update_alerts(request, alerts)
            if avatar:
                save_avatar(request, avatar)
                context['submit_avatar'] = 'new avatar saved'
            if email_updated:
                context['submit_email'] = 'new email saved'
            if alerts_updated:
                status = 'turned on' if alerts else 'turned off'
                context['submit_alert'] = f'email alerts {status}'
    else:
        form = ProfileForm(
            initial={
                'email': request.user.email,
                'alerts': request.user.profile.send_email
            }
        )
    context['form'] = form
    return render(request, 'users/profile.html', context)


def signup(request, fallback=False):
    if request.user.is_authenticated:
        return HttpResponseRedirect(
            reverse('users:profile', args=()))
    context = {}
    if not fallback:
        return render(request, 'users/signup.html', context)
    else:
        return [request, 'users/signup.html', context]


def do_signup(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(
            reverse('users:profile', args=()))
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
    context = {'user': user}
    if user is not None:
        login(request, user)
        return render(request, 'users/profile.html', context)
