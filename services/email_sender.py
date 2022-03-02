from django.core.mail import send_mail
from django.conf import settings


class Sender:
    domain = settings.DOMAIN
    subject = 'Hasker alerts'
    from_email = settings.SENDER_EMAIL

    def __init__(self, recipients: list[str], template: dict, vars: dict,
                 subject: str = None, validate: bool = True):
        self.recipients = recipients
        self.template = template
        self.vars = vars
        if subject:
            self.subject = subject
        self.email_template = template.get('email_template', None)
        self.html_email_temlate = template.get('html_email_temlate', None)
        if validate:
            try:
                self.valid = self.validate()
            except AssertionError as exc:
                self.valid = False
                self.error = str(exc)

    def validate(self):
        if not isinstance(self.recipients, list):
            raise AssertionError('Recipients var should be a list')
        for email in self.recipients:
            if not isinstance(email, str):
                raise AssertionError('Recipients var should contain strings')
            if '@' not in email:
                raise AssertionError(
                    'Recipients var should contain valid emails '
                    f'({email} is not)')
        if not self.email_template:
            raise AssertionError('Email_template not in template dict')
        return True

    def send(self):
        html_message = (
            self.html_email_temlate.format_map(self.vars)
            if self.html_email_temlate
            else None
        )
        return send_mail(subject=self.subject,
                         message=self.email_template.format_map(self.vars),
                         html_message=html_message,
                         from_email=self.from_email,
                         recipient_list=[self.recipients],
                         fail_silently=False)
