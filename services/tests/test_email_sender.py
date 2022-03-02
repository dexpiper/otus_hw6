from unittest import TestCase

from django.core import mail
from django.conf import settings

from services.email_sender import Sender
from services.email_templates.question_alert import (email_template,
                                                     html_email_temlate)


class TestSender(TestCase):

    def setUp(self):
        self.recipients = ['alice@wonderland.com']
        self.template = {
            'email_template': email_template,
            'html_email_temlate': html_email_temlate
        }
        self.vars = {
            'username': 'alice',
            'qw_link': 'question.com/myquestion',
            'qw_title': 'title',
            'profile_link': 'question.com/profile',
        }
        self.subject = 'Hasker - New answer for your question'

    def test_sender_validation(self):
        sender = Sender(self.recipients, self.template, self.vars,
                        self.subject, validate=False)
        self.assertTrue(sender.validate())

    def test_sender_creation(self):
        sender = Sender(self.recipients, self.template, self.vars,
                        self.subject)
        self.assertTrue(sender.valid)
        with self.assertRaises(AttributeError):
            sender.errors
        self.assertEqual(sender.recipients, self.recipients)
        self.assertEqual(sender.template, self.template)
        self.assertEqual(sender.vars, self.vars)
        self.assertEqual(sender.subject, self.subject)

    def test_bad_sender_creation(self):
        sender1 = Sender(None, self.template,
                         self.vars,
                         self.subject, validate=False)
        sender2 = Sender(['not an email'], self.template,
                         self.vars,
                         self.subject, validate=False)
        sender3 = Sender(self.recipients, {},
                         self.vars,
                         self.subject, validate=False)
        for s in (sender1, sender2, sender3):
            with self.subTest(s=s):
                with self.assertRaises(AssertionError):
                    s.validate()

    def test_sender_send_email(self):
        sender = Sender(self.recipients, self.template, self.vars,
                        self.subject)
        self.assertTrue(sender.valid)
        sender.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, self.subject)
        self.assertEqual(mail.outbox[0].from_email, settings.SENDER_EMAIL)
        self.assertEqual(mail.outbox[0].to, [['alice@wonderland.com']])
