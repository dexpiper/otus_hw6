from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView

from .forms import ProfileForm, SignUpForm
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


def signup(request):
    if request.user.is_authenticated:
        return redirect('users:profile')
    context = {}
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('users:profile')
    else:
        form = SignUpForm()
    context['form'] = form
    return render(request, 'users/signup.html', context)
