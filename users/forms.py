from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class ProfileForm(forms.Form):
    avatar = forms.ImageField(required=False, label='Upload your avatar')
    email = forms.EmailField(required=False)
    alerts = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        provided_email = self.cleaned_data.get('email')
        if self.user and self.user.email == provided_email:
            return provided_email

        if User.objects.filter(email=provided_email).count():
            raise forms.ValidationError(
                u'That email address already exists.'
            )
        return provided_email


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with that email already exists.')
        return email
