from django.core.mail import send_mail
from django.conf import settings


class Sender:
    domain = settings.DOMAIN
    subject = 'Hasker - New answer for your question'
    from_email = settings.SENDER_EMAIL
    email_template = (
        'Hello, {username}!\n'
        'You have a new answer on your question "{qw_title}" on Hasker. '
        'Would you like to check it out? \n'
        '{qw_link}'
        '\n\nIf you do not want email alerts anymore, turn them off in your'
        ' profile: {profile_link}'
    )
    html_email_temlate = (
        '<p>Hello, {username}!</p>'
        '<p>You have a new answer on your question "{qw_title}" on Hasker. '
        'Would you like to check it out?</p>'
        '<p><a href="{qw_link}">Here is your link!</a></p>'
        '<p>If you do not want email alerts anymore, turn them off in your'
        ' <a href="{profile_link}">profile</a>.</p>'
    )

    def __init__(self, question):
        self.username = question.author.username
        self.user_email = question.author.email
        self.qw_link = f'http://{self.domain}/questions/{question.id}'
        self.qw_title = question.title
        self.profile_link = f'http://{self.domain}/questions/profile'
        self.dct = dict(
            username=self.username,
            qw_title=self.qw_title,
            qw_link=self.qw_link,
            profile_link=self.profile_link
        )

    def send(self):
        return send_mail(subject=self.subject,
                         message=self.email_template.format_map(self.dct),
                         html_message=self.html_email_temlate.format_map(
                            self.dct),
                         from_email=self.from_email,
                         recipient_list=[self.user_email],
                         fail_silently=False)
