from urllib.parse import urljoin

from django.dispatch import receiver
import django.dispatch
from django.conf import settings

from services.email_sender import Sender
from services.email_templates.question_alert import (email_template,
                                                     html_email_temlate)

question_answered = django.dispatch.Signal()


@receiver(question_answered, dispatch_uid='unique_identifier')
def my_callback(sender, **kwargs):
    question = kwargs.get('question', None)
    if not question:
        return
    if question.author.profile.send_email:
        recipients = [question.author.email]
        template = {
            'email_template': email_template,
            'html_email_temlate': html_email_temlate
        }
        vars = {
            'username': question.author.username,
            'qw_link': urljoin(settings.DOMAIN, f'/questions/{question.id}'),
            'qw_title': question.title,
            'profile_link': urljoin(settings.DOMAIN, 'users/profile'),
        }
        subject = 'Hasker - New answer for your question'

        email_sender = Sender(recipients, template, vars, subject)
        if email_sender.valid:
            email_sender.send()
        else:
            if not settings.SENDER_FALL_SILENT:
                raise AssertionError(
                    'Sender class is not valid. '
                    f'Exceptions: {email_sender.errors}')
