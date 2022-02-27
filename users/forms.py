from django import forms
from django.contrib.auth.models import User


class AlertsBoolField(forms.CharField):
    def to_python(self, value):
        print(f'Incoming alerts value: {value}')
        return True if value == 'on' else False


class ProfileForm(forms.Form):
    avatar = forms.ImageField(required=False, label='Upload your avatar')
    email = forms.EmailField(required=False)
    alerts = AlertsBoolField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)

    def clean_alerts(self):
        provided_alerts = self.cleaned_data.get('alerts')
        self.alerts = provided_alerts
        return provided_alerts

    def clean_email(self):
        provided_email = self.cleaned_data.get('email')
        if self.user and self.user.email == provided_email:
            return provided_email

        if User.objects.filter(email=provided_email).count():
            raise forms.ValidationError(
                u'That email address already exists.'
            )
        return provided_email
