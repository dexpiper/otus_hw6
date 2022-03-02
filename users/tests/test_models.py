from django.test import TestCase
from django.contrib.auth.models import User


class TestUserBasics(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.foo = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.foo.save()

    def test_user_creation(self):
        sam = User.objects.get(username='Sam')
        self.assertEqual(sam.username, 'Sam')
        self.assertEqual(sam.email, 'sam@pisem.net')
        self.assertEqual(sam.id, self.foo.id)

    def test_user_profile_created(self):
        """
        Profile should be created automaticly after
        User object creation (via sigals).
        """
        sam = User.objects.get(username='Sam')
        self.assertIsNotNone(sam.profile)
        self.assertEqual(sam.profile.user, sam)

    def test_default_profile_settings(self):
        sam = User.objects.get(username='Sam')
        self.assertFalse(bool(sam.profile.avatar))
        self.assertFalse(sam.profile.send_email)

    def test_check_profile_changing(self):
        sam = User.objects.get(username='Sam')
        sam.profile.send_email = True
        sam.profile.save()
        self.assertTrue(sam.profile.send_email)

    def test_user_email_changing(self):
        sam = User.objects.get(username='Sam')
        sam.email = 'sam@yagoo.what'
        sam.save()
        self.assertEqual(sam.email, 'sam@yagoo.what')

    def test_user_avatar_setting(self):
        sam = User.objects.get(username='Sam')
        sam.profile.avatar = '/media/sam_avatar.jpg'
        sam.profile.save()
        self.assertEqual(sam.profile.avatar, '/media/sam_avatar.jpg')
