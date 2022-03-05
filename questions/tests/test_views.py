from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib import auth

from questions.models import Question, Tag


class TestIndex(TestCase):

    def test_index_page_basic_rendering(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/index.html')

    @patch('questions.models.Question.trending')
    def test_index_page_hot_questions(self, mock):
        mock.return_value = Question.objects.all().order_by('-votes')[:20]
        response = self.client.get('/questions/hot')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/hot_questions.html')
        mock.assert_called_once()


class TestSearch(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.sam = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.sam.save()

    def test_search_tag(self):
        q = Question(
            title='How to Django?',
            author=self.sam,
            content='Lorem ipsum dolor est'
        )
        q.save()
        tag = Tag(title='Python')
        tag.save()
        tag.questions.add(q)
        self.assertEqual(tag.questions.all().count(), 1)
        response = self.client.get(f'/questions/tag/{tag.id}')
        self.assertEqual(response.status_code, 200, f'Failed with {tag.id}')
        self.assertTemplateUsed(response, 'questions/tag.html')

    def test_index_search(self):
        pass

    def test_show_question(self):
        pass


class TestQuestionMaking(TestCase):

    def test_make_question(self):
        pass


class TestQuestionFlags(TestCase):

    def test_alter_flag(self):
        pass


class TestAnswerVoting(TestCase):

    def test_answer_vote(self):
        pass


class TestQuestionVoting(TestCase):

    def test_question_vote(self):
        pass
