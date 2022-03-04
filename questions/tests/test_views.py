from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib import auth

from questions.models import Question


class TestIndex(TestCase):

    def test_index_page_basic_rendering(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/index.html')
