import tempfile
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib import auth


class TestSignUp(TestCase):

    def test_sign_up_page_rendering(self):
        """
        Alice opens sign-up page
        """
        response = self.client.get('/users/signup')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/signup.html')

    def test_sign_up_controller(self):
        """
        Alice enters her credentials and is redirected
        to her brand-new profile page
        """
        response = self.client.post(
            '/users/signup',
            {
                'username': 'alice',
                'email': 'alice@wonderland.com',
                'password1': 'alicepassword',
                'password2': 'alicepassword'
            }
        )
        self.assertEqual(response.status_code, 302)
        alice = User.objects.get(username='alice')
        self.assertEqual(alice.username, 'alice')
        self.assertEqual(alice.email, 'alice@wonderland.com')
        self.assertIsNotNone(alice.profile)
        self.assertRedirects(response, '/users/profile')

    def test_sign_up_with_existing_username(self):
        """
        Alice tries to sign up again
        """
        alice = User.objects.create_user(
            username='alice',
            email='alice@wonderland.com',
            password='alicepassword'
        )
        alice.save()
        response = self.client.post(
            '/users/signup',
            {
                'username': 'alice',
                'email': 'alice@wonderland.com',
                'password1': 'alicepassword',
                'password2': 'alicepassword'
            },
            follow=True
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertTemplateNotUsed(response, 'users/profile.html')
        self.assertTemplateUsed(response, 'users/signup.html')
        self.assertFormError(response, 'form', 'username',
                             'A user with that username already exists.')

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
            '/users/signup',
            {
                'username': 'jane',
                'email': 'alice@wonderland.com',
                'password1': 'janepassword',
                'password2': 'janepassword'
            },
            follow=True
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertTemplateNotUsed(response, 'users/profile.html')
        self.assertTemplateUsed(response, 'users/signup.html')
        self.assertFormError(response, 'form', 'email',
                             'A user with that email already exists.')

    def test_sign_up_password_misspelled(self):
        """
        Jane uses unique email to sign up, but misspells
        her password
        """
        response = self.client.post(
            '/users/signup',
            {
                'username': 'jane',
                'email': 'jane@wonderland.com',
                'password1': 'janepassword',
                'password2': 'jneapsasd&^5'
            }
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertTemplateNotUsed(response, 'users/profile.html')
        self.assertTemplateUsed(response, 'users/signup.html')
        self.assertFormError(response, 'form', 'password2',
                             'The two password fields didn’t match.')

    def test_sign_up_empty_field(self):
        """
        Jane forgetting sign-up fields
        """
        for d in (
            {
                'username': '',
                'email': 'jane@wonderland.com',
                'password': 'janepass',
                'password2': 'jneapsas'
            },
            {
                'username': 'jane',
                'email': '',
                'password': 'janepass',
                'password2': 'jneapsas'
            },
            {
                'username': 'jane',
                'email': 'jane@wonderland.com',
                'password': '',
                'password2': 'jneapsas'
            },
            {
                'username': 'jane',
                'email': 'jane@wonderland.com',
                'password': 'janepass',
                'password2': ''
            }
                    ):
            with self.subTest(d=d):
                response = self.client.post('/users/signup', d)
                self.assertTemplateNotUsed(response, 'users/profile.html')
                self.assertTemplateUsed(response, 'users/signup.html')
                self.assertContains(response, 'This field is required.')

    def test_logged_user_cannot_signup(self):
        """
        Already-logged-in Alice tries to see signup page
        """
        alice = User.objects.create_user(
            username='alice',
            email='alice@wonderland.com'
        )
        alice.set_password('alicepass')
        alice.save()
        self.client.login(username='alice', password='alicepass')
        self.assertEqual(auth.get_user(self.client), alice)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get('/users/signup')
        self.assertRedirects(response, '/users/profile')


class TestLogIn(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.alice = User.objects.create_user(
            username='alice',
            email='alice@wonderland.com',
            password='alicepass'
        )
        cls.alice.save()

    def test_log_in_page(self):
        response = self.client.get('/users/login')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        with self.assertRaises(KeyError):
            response.context['error_message']

    def test_log_in_controller(self):
        response = self.client.post(
            '/users/login',
            {
                'username': 'alice',
                'password': 'alicepass'
            },
            follow=True
        )
        self.assertEqual(auth.get_user(self.client), self.alice)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/users/profile')
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context['user'], self.alice)

    def test_bad_login_credentials(self):
        for dct in (
            {
                'username': 'alice',
                'password': ''
            },
            {
                'username': '',
                'password': 'alicepass'
            },
            {
                'username': 'foobar',
                'password': 'alicepass'
            },
            {
                'username': 'alice',
                'password': 'foobar'
            },
            {
                'username': '',
                'password': ''
            },

        ):
            with self.subTest(dct=dct):
                response = self.client.post(
                    '/users/login',
                    dct,
                    follow=True
                )
                self.assertTemplateNotUsed(response, 'users/profile.html')
                self.assertTemplateUsed(response, 'users/login.html')
                self.assertContains(
                    response,
                    "Your username and password didn't match."
                )


class TestProfile(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.alice = User.objects.create_user(
            username='alice',
            email='alice@wonderland.com',
            password='alicepass'
        )
        cls.alice.save()
        cls.bob = User.objects.create_user(
            username='bob',
            email='bob@yagoo.org',
            password='bobpass'
        )
        cls.bob.save()

    def test_profile_page(self):
        for usr in (self.alice, self.bob):
            with self.subTest(usr=usr):
                self.client.force_login(usr)
                response = self.client.get('/users/profile')
                self.assertTemplateUsed(response, 'users/profile.html')
                self.assertEqual(response.context['user'], usr)

    @patch('django.core.files.storage.FileSystemStorage.save')
    def test_profile_logic(self, mock_save):
        self.client.force_login(self.alice)
        mock_save.return_value = 'alice_avatar.jpg'
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmpimage:
            response = self.client.post(
                    '/users/profile',
                    {
                        'avatar': tmpimage,
                        'alerts': 'on',
                        'email': 'newalice@wonderland.com'
                    },
                    format='multipart',
                    follow=True
                )
        self.assertEqual(response.status_code, 200)
        alice_updated = User.objects.get(username='alice')
        self.assertEqual(alice_updated.profile.send_email, True)
        self.assertEqual(alice_updated.email, 'newalice@wonderland.com')
        self.assertContains(response, "email alerts turned on")
        self.assertIsNotNone(alice_updated.profile.avatar)
        mock_save.assert_called_once()
