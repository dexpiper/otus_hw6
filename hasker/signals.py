from django.dispatch import receiver
import django.dispatch

from services.email_sender import Sender

question_answered = django.dispatch.Signal()


@receiver(question_answered, dispatch_uid='unique_identifier')
def my_callback(sender, **kwargs):
    question = kwargs.get('question', None)
    if not question:
        return
    if question.author.profile.send_email:
        email_sender = Sender(question)
        email_sender.send()
