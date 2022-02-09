from django.dispatch import receiver
import django.dispatch


question_answered = django.dispatch.Signal()


@receiver(question_answered, dispatch_uid='unique_identifier')
def my_callback(sender, **kwargs):
    qw_author = kwargs.get('qw_author', None)
    if not qw_author:
        return
    if qw_author.profile.send_email:
        print(f'Got a signal from {str(sender)} for {qw_author.username}!')
