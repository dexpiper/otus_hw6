from django.test import TestCase
from django.contrib.auth.models import User

from questions.forms import AnswerForm, QuestionForm
from questions.models import Answer, Question


class TestAnswerForm(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.user.save()
        cls.question = Question(
            title='How to Django?',
            author=cls.user,
            content='Lorem ipsum dolor est'
        )
        cls.question.save()

    def test_answer_form_basics(self):
        form = AnswerForm(
            {'content': 'This is some answer'},
            question_id=self.question.id
        )
        self.assertTrue(form.is_valid())

    def test_answer_content_clearing(self):
        '''
        Answers with the same text are not allowed
        '''
        old_answer = Answer(
            author=self.user,
            question=self.question,
            content='This is the same answer'
        )
        old_answer.save()
        form = AnswerForm(
            {'content': 'This is the same answer'},
            question_id=self.question.id
        )
        self.assertFalse(form.is_valid())


class TestQuestionForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.user.save()
        cls.old_question = Question(
            title='How to Django?',
            author=cls.user,
            content='Lorem ipsum dolor est'
        )
        cls.old_question.save()

    def test_question_form_basics(self):
        form = QuestionForm(
            {
                'title': 'How to OTUS?',
                'content': 'This is a question so sophisticated! Lorem Ipsum',
                'tags': 'Lorem Python'
            }
        )
        self.assertTrue(form.is_valid())

    def test_question_form_clean_tags_good(self):
        for choice in (
            'awfwa',
            'Python OTUS Django',
            'one two',
            ''
        ):
            with self.subTest(choice=choice):
                form = QuestionForm(
                    {
                        'title': 'How to OTUS?',
                        'content': 'This is a question so sophisticated!',
                        'tags': choice
                    }
                )
                self.assertTrue(form.is_valid())
                self.assertEqual(
                    form.cleaned_data.get('tags'),
                    choice.split()
                )

    def test_question_form_clean_tags_bad(self):
        '''
        Only 3 tags can be provided
        '''
        for choice in (
            'awfwa afwf wafwf faw waf wafwa',
            'Python OTUS Django Main',
            'one two three four five six seven eight'
        ):
            with self.subTest(choice=choice):
                form = QuestionForm(
                    {
                        'title': 'How to OTUS?',
                        'content': 'This is a question so sophisticated!',
                        'tags': choice
                    }
                )
        self.assertFalse(form.is_valid())

    def test_question_form_clean_title(self):
        pass
