from django.dispatch import receiver
import django.dispatch
from django.core.mail import send_mail


question_answered = django.dispatch.Signal()


@receiver(question_answered, dispatch_uid='unique_identifier')
def my_callback(sender, **kwargs):
    question = kwargs.get('question', None)
    if not question:
        return
    if question.author.profile.send_email:
        email_sender = Sender(question)
        email_sender.send()


class Sender:
    domain = 'www.hasker.media'
    subject = 'Hasker - New answer for your question'
    from_email = 'example@hasker.com'
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
