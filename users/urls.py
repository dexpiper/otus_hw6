from django.urls import path

from . import views

app_name = 'users'
urlpatterns = [
    path('profile', views.profile, name='profile'),
    path('login', views.login_page, name='login'),
    path('do_login', views.do_login, name='do_login'),
    path('signup', views.signup, name='signup'),
    path('do_signup', views.do_signup, name='do_signup'),
    path('logout', views.do_logout, name='logout')
]
