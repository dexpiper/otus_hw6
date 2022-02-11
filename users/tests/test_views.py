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
        with self.assertRaises(KeyError):
            # no error message should be shown
            response.context['error_message']

    def test_sign_up_controller(self):
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
        self.assertTemplateUsed(response, 'users/login.html')
        with self.assertRaises(KeyError):
            # no error message should be shown
            response.context['error_message']

    def test_log_in_controller(self):
        response = self.client.post(
            '/users/do_login',
            {
                'login': 'alice',
                'password': 'alicepass'
            }
        )
        self.assertEqual(auth.get_user(self.client), self.alice)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context['user'], self.alice)

    def test_bad_login_credentials(self):
        for dct in (
            {
                'login': 'alice',
                'password': ''
            },
            {
                'login': '',
                'password': 'alicepass'
            },
            {
                'login': 'foobar',
                'password': 'alicepass'
            },
            {
                'login': 'alice',
                'password': 'foobar'
            },
            {
                'login': '',
                'password': ''
            },

        ):
            with self.subTest(dct=dct):
                response = self.client.post(
                    '/users/do_login',
                    dct
                )
                self.assertTemplateNotUsed(response, 'users/profile.html')
                self.assertTemplateUsed(response, 'users/login.html')
                self.assertIn(
                    'Username or password are invalid',
                    response.context['error_message']
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
                with self.assertRaises(KeyError):
                    # no error message should be shown
                    response.context['error_message']
                    response.context['submit_email']
                    response.context['submit_avatar']
                    response.context['submit_alert']
                self.assertEqual(response.context['user'], usr)

    def test_profile_logic(self):
        self.client.force_login(self.alice)
        with open('users/tests/fixtures/my_best_photo.jpg', 'rb') as image:
            response = self.client.post(
                    '/users/save_profile',
                    {
                        'avatar': image,
                        'alerts': 'on',
                        'email': 'newalice@wonderland.com'
                    },
                    format='multipart'
                )
        self.assertEqual(response.status_code, 302)
        alice_updated = User.objects.get(username='alice')
        self.assertEqual(alice_updated.profile.send_email, True)
        self.assertEqual(alice_updated.email, 'newalice@wonderland.com')
        self.assertIsNotNone(alice_updated.profile.avatar)
