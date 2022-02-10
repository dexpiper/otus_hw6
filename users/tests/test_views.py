from django.test import TestCase
from django.contrib.auth.models import User


class TestSignUp(TestCase):

    def test_sign_up_page_rendering(self):
        """
        Alice opens sign-up page
        """
        response = self.client.get('/users/signup')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/signup.html')
        with self.assertRaises(KeyError):
            # no error message should be shown
            response.context['error_message']

    def test_sign_up_view(self):
        """
        Alice enters her credentials and is redirected
        to her brand-new profile page
        """
        response = self.client.post(
            '/users/do_signup',
            {
                'login': 'alice',
                'email': 'alice@wonderland.com',
                'password': 'alicepass',
                'password-conf': 'alicepass'
            }
        )
        self.assertEqual(response.status_code, 200)
        alice = User.objects.get(username='alice')
        self.assertEqual(alice.username, 'alice')
        self.assertEqual(alice.email, 'alice@wonderland.com')
        self.assertIsNotNone(alice.profile)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context.get('user'), alice)

    def test_sign_up_with_existing_username(self):
        """
        Alice tries to sign up again
        """
        alice = User.objects.create_user(
            username='alice',
            email='alice@wonderland.com',
            password='alicepass'
        )
        alice.save()
        response = self.client.post(
            '/users/do_signup',
            {
                'login': 'alice',
                'email': 'alice@wonderland.com',
                'password': 'alicepass',
                'password-conf': 'alicepass'
            }
        )
        self.assertTemplateNotUsed(response, 'users/profile.html')
        self.assertTemplateUsed(response, 'users/signup.html')
        self.assertIn(
            'Username alice is occupied',
            response.context['error_message']
        )

    def test_sign_up_with_existing_email(self):
        """
        Jane tries to use Alice's email to sign up
        """
        alice = User.objects.create_user(
            username='alice',
            email='alice@wonderland.com',
            password='alicepass'
        )
        alice.save()
        response = self.client.post(
            '/users/do_signup',
            {
                'login': 'jane',
                'email': 'alice@wonderland.com',
                'password': 'janepass',
                'password-conf': 'janepass'
            }
        )
        self.assertTemplateNotUsed(response, 'users/profile.html')
        self.assertTemplateUsed(response, 'users/signup.html')
        self.assertIn(
            'There is a user with e-mail alice@wonderland.com',
            response.context['error_message']
        )

    def test_sign_up_password_misspelled(self):
        """
        Jane uses unique email to sign up, but misspells
        her password
        """
        response = self.client.post(
            '/users/do_signup',
            {
                'login': 'jane',
                'email': 'jane@wonderland.com',
                'password': 'janepass',
                'password-conf': 'jneapsas'
            }
        )
        self.assertTemplateNotUsed(response, 'users/profile.html')
        self.assertTemplateUsed(response, 'users/signup.html')
        self.assertIn(
            'Passwords do not match',
            response.context['error_message']
        )

    def test_sign_up_empty_field(self):
        """
        Jane forgetting sign-up fields
        """
        for d in (
            {
                'login': '',
                'email': 'jane@wonderland.com',
                'password': 'janepass',
                'password-conf': 'jneapsas'
            },
            {
                'login': 'jane',
                'email': '',
                'password': 'janepass',
                'password-conf': 'jneapsas'
            },
            {
                'login': 'jane',
                'email': 'jane@wonderland.com',
                'password': '',
                'password-conf': 'jneapsas'
            },
            {
                'login': 'jane',
                'email': 'jane@wonderland.com',
                'password': 'janepass',
                'password-conf': ''
            }
                    ):
            with self.subTest(d=d):
                response = self.client.post('/users/do_signup', d)
                self.assertTemplateNotUsed(response, 'users/profile.html')
                self.assertTemplateUsed(response, 'users/signup.html')
                self.assertIn(
                    'Some fields are empty',
                    response.context['error_message']
                )
