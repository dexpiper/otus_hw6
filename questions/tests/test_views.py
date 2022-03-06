from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib import auth

from questions.models import Question, Tag, Answer


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
        cls.q = Question(
            title='How to Django?',
            author=cls.sam,
            content='Lorem ipsum dolor est'
        )
        cls.q.save()
        cls.q2 = Question(
            title='How to Lorem?',
            author=cls.sam,
            content='That is a nice question without search phrase'
        )
        cls.q2.save()
        cls.tag = Tag(title='Python')
        cls.tag.save()
        cls.tag.questions.add(cls.q, cls.q2)
        cls.tag2 = Tag(title='Lorem')
        cls.tag2.save()
        cls.tag2.questions.add(cls.q2)
        cls.a = Answer(
            author=cls.sam,
            question=cls.q2,
            content='Lorem ipsum dolor e, ne lorem.'
        )
        cls.a.save()

    def test_search_tag(self):
        '''
        Show all questions with given tag
        '''
        self.assertEqual(self.tag.questions.all().count(), 2)
        self.assertEqual(self.tag2.questions.all().count(), 1)
        for tag in (self.tag, self.tag2):
            with self.subTest(tag=tag):
                response = self.client.get(f'/questions/tag/{tag.id}')
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'questions/tag.html')
                self.assertContains(response, 'How to Lorem?')
                if tag == self.tag2:
                    self.assertContains(response, 'How to Django?')

    def test_index_search(self):
        '''
        Find search phrase 'ipsum dolor' in questions and in answers,
        but show only questions.
        '''
        response = self.client.post(
            '/questions/search',
            {
                'search': 'ipsum dolor'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/search.html')
        # 'ipsum dolor' search phrase in question text:
        self.assertContains(response, 'How to Django?')
        # 'ipsum dolor' search phrase in one of the answers:
        self.assertContains(response, 'How to Lorem?')

    def test_index_search_nothing_found(self):
        '''
        Check empty search result
        '''
        response = self.client.post(
            '/questions/search',
            {   # no such phrase in questions and answers:
                'search': 'abrakadabra!'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/search.html')
        self.assertContains(response, 'Search results for "abrakadabra!"')
        self.assertContains(response, 'No questions are available.')

    def test_tag_search_from_index_search(self):
        '''
        Check if user can find tags via search field with "tag:"
        '''
        response = self.client.post(
            '/questions/search',
            {
                'search': 'tag: Python'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/tag.html')
        self.assertContains(response, 'How to Lorem?')
        self.assertContains(response, 'How to Django?')


class TestQuestionViews(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.sam = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.sam.save()
        cls.q = Question(
            title='How to Django?',
            author=cls.sam,
            content='Lorem ipsum dolor est'
        )
        cls.q.save()

    def test_basic_show_question(self):
        response = self.client.get(f'/questions/{self.q.id}')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/question.html')

    def test_show_question_404(self):
        response = self.client.get('/questions/12345')
        self.assertEqual(response.status_code, 404)

    def test_show_question_and_its_answers(self):
        contents = 'This is first answer', 'This is second answer'
        for content in contents:
            a = Answer(
                author=self.sam,
                question=self.q,
                content=content
            )
            a.save()
        response = self.client.get(f'/questions/{self.q.id}')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/question.html')
        for content in contents:
            self.assertContains(response, content)

    def test_make_answer_form_not_show(self):
        '''
        User who not logged in cannot see answer form
        '''
        response = self.client.get(f'/questions/{self.q.id}')
        self.assertContains(
            response, 'Please register or sign up to write an answer')
        self.assertNotContains(
            response, '<legend><h3>Your answer:</h3></legend>')

    def test_make_answer_form_show(self):
        '''
        Logged-in user Sam can see answer form
        '''
        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(f'/questions/{self.q.id}')
        self.assertNotContains(
            response, 'Please register or sign up to write an answer')
        self.assertContains(response, '<legend><h3>Your answer:</h3></legend>')

    def test_make_answer_form_sending(self):
        '''
        Sam sends his answer
        '''
        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.post(
            f'/questions/{self.q.id}',
            {
                'content': 'This is the answer'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/question.html')
        self.assertEqual(Answer.objects.filter(question=self.q).count(), 1)
        self.assertEqual(
            Answer.objects.get(question=self.q).content, 'This is the answer')
        self.assertContains(response, 'This is the answer')

    def test_unregistered_user_redirected(self):
        '''
        Not logged in user post request redirected to login
        '''
        response = self.client.post(
            f'/questions/{self.q.id}',
            {
                'content': 'This is yet another answer'
            },
            follow=True
        )
        self.assertRedirects(response, '/users/login', target_status_code=200)
        self.assertFalse(
            Answer.objects.filter(content='This is yet another answer').count()
        )


class TestMakeQuestion(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.sam = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.sam.save()

    def test_unregistered_user_redirected(self):
        '''
        Only logged-in users can see make question page
        '''
        response = self.client.get('/questions/add')
        self.assertRedirects(
            response, '/users/login?next=/questions/add',
            status_code=302, target_status_code=200
        )

    def test_make_question_page(self):
        '''
        Logged-in user can see make question page
        '''
        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get('/questions/add')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questions/make_question.html')

    def test_make_question_form(self):
        '''
        Sam making question
        '''
        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.post(
            '/questions/add',
            {
                'title': 'This is a question',
                'content': 'Lorem Ipsum dolor est',
                'tags': 'Python Lorem Ipsum'
            },
            follow=True
        )

        self.assertTrue(
            Question.objects.filter(title='This is a question').count())
        qw = Question.objects.get(title='This is a question')
        self.assertEqual(qw.author.id, self.sam.id)
        self.assertEqual(qw.content, 'Lorem Ipsum dolor est')
        self.assertEqual(Tag.objects.filter(questions=qw.id).count(), 3)

        self.assertRedirects(response, f'/questions/{qw.id}',
                             target_status_code=200)
        for element in ('This is a question', 'Lorem Ipsum dolor est'):
            with self.subTest(element=element):
                self.assertContains(response, element)
        tags = Tag.objects.filter(questions=qw.id)
        for tag in tags:
            with self.subTest(tag=tag):
                self.assertContains(response, tag.title)

    def test_unauthorised_user_cannot_post_question(self):
        '''
        Post request from user who not logged in would result
        in redirection to login page
        '''
        response = self.client.post(
            '/questions/add',
            {
                'title': 'This is a question',
                'content': 'Lorem Ipsum dolor est',
                'tags': 'Python Lorem Ipsum'
            },
            follow=True
        )
        self.assertRedirects(
            response, '/users/login?next=/questions/add',
            status_code=302, target_status_code=200
        )


class TestQuestionFlags(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.sam = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.sam.save()
        cls.alice = User.objects.create_user(
            username='Alice',
            email='alice@wonderland.com',
            password='alicepass'
        )
        cls.alice.save()
        cls.q = Question(
            title='How to Django?',
            author=cls.sam,
            content='Lorem ipsum dolor est'
        )
        cls.q.save()

    def test_alter_flag_basic_logic(self):
        '''
        Sam can mark Alice's answer to his question with 'best' flag
        '''
        alice_answer = Answer(
            author=self.alice,
            question=self.q,
            content='This is best answer'
        )
        alice_answer.save()
        sam_question = self.q
        self.assertEqual(alice_answer.answer_flag, 0)
        self.assertEqual(sam_question.status, 0)

        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.client.get(
            f'/questions/alterflag/{alice_answer.id}',
            HTTP_REFERER=f'/questions/alterflag/{alice_answer.id}'
        )
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=alice_answer.id)
        self.assertEqual(alice_answer.answer_flag, 1)
        sam_question = Question.objects.get(id=self.q.id)
        self.assertEqual(sam_question.status, 1)

    def test_alter_flag_author_restriction(self):
        '''
        Sam cannot mark his own answer to his question with 'best' flag
        '''
        sam_answer = Answer(
            author=self.sam,
            question=self.q,
            content='This is best answer'
        )
        sam_answer.save()
        sam_question = self.q
        self.assertEqual(sam_question.status, 0)
        self.assertEqual(sam_answer.answer_flag, 0)
        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.client.get(
            f'/questions/alterflag/{sam_answer.id}',
            HTTP_REFERER=f'/questions/alterflag/{sam_answer.id}'
        )
        self.assertTemplateUsed('questions/question.html')
        sam_answer = Answer.objects.get(id=sam_answer.id)
        self.assertNotEqual(sam_answer.answer_flag, 1)     # not changed
        sam_question = Question.objects.get(id=self.q.id)
        self.assertNotEqual(sam_question.status, 1)        # not changed

    def test_alter_flag_other_user_restriction(self):
        '''
        Alice cannot mark her answer to Sam's question as 'best'
        '''
        alice_answer = Answer(
            author=self.alice,
            question=self.q,
            content='This is best answer'
        )
        alice_answer.save()
        sam_question = self.q
        self.assertEqual(alice_answer.answer_flag, 0)
        self.assertEqual(sam_question.status, 0)

        self.client.force_login(self.alice)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.client.get(
            f'/questions/alterflag/{alice_answer.id}',
            HTTP_REFERER=f'/questions/alterflag/{alice_answer.id}'
        )
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=alice_answer.id)
        self.assertNotEqual(alice_answer.answer_flag, 1)       # not changed
        sam_question = Question.objects.get(id=self.q.id)
        self.assertNotEqual(sam_question.status, 1)            # not changed

    def test_alter_flag_unauthorized(self):
        '''
        Unauthorised user cannot alter flags
        '''
        alice_answer = Answer(
            author=self.alice,
            question=self.q,
            content='This is best answer'
        )
        alice_answer.save()
        self.client.get(
            f'/questions/alterflag/{alice_answer.id}',
            HTTP_REFERER=f'/questions/alterflag/{alice_answer.id}'
        )
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=alice_answer.id)
        self.assertNotEqual(alice_answer.answer_flag, 1)       # not changed
        sam_question = Question.objects.get(id=self.q.id)
        self.assertNotEqual(sam_question.status, 1)            # not changed


class TestAnswerVoting(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.sam = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.sam.save()
        cls.alice = User.objects.create_user(
            username='Alice',
            email='alice@wonderland.com',
            password='alicepass'
        )
        cls.alice.save()
        cls.bob = User.objects.create_user(
            username='Bob',
            email='bob@wonderland.com',
            password='bobpass'
        )
        cls.bob.save()
        cls.q = Question(
            title='How to Django?',
            author=cls.sam,
            content='Lorem ipsum dolor est'
        )
        cls.q.save()
        cls.alice_answer = Answer(
            author=cls.alice,
            question=cls.q,
            content='This is best answer'
        )
        cls.alice_answer.save()

    def test_answer_upvote_basic_logic(self):
        '''
        Sam and Bob can upvote for Alice's answer
        '''
        self.assertEqual(self.alice_answer.votes, 0)  # no votes yet

        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            f'/questions/answervote/{self.alice_answer.id}/1',  # Sam upvotes
            HTTP_REFERER=f'/questions/{self.q.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.q.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, 1)  # Sam's upvote counted

        self.client.force_login(self.bob)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            f'/questions/answervote/{self.alice_answer.id}/1',  # Bob upvotes
            HTTP_REFERER=f'/questions/{self.q.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.q.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, 2)  # Bob's upvote counted

    def test_answer_downvote_basic_logic(self):
        '''
        Sam and Bob can downvote for Alice's answer
        '''
        self.assertEqual(self.alice_answer.votes, 0)  # no votes yet

        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            f'/questions/answervote/{self.alice_answer.id}/0',  # Sam downvotes
            HTTP_REFERER=f'/questions/{self.q.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.q.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, -1)  # Sam's downvote counted

        self.client.force_login(self.bob)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            f'/questions/answervote/{self.alice_answer.id}/0',  # Bob downvotes
            HTTP_REFERER=f'/questions/{self.q.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.q.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, -2)  # Bob's downvote counted

    def test_answer_vote_upvotes_and_downvotes(self):
        '''
        Sam can upvote, can downvote and change his mind
        '''
        self.assertEqual(self.alice_answer.votes, 0)  # no votes yet
        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)

        response = self.client.get(
            f'/questions/answervote/{self.alice_answer.id}/1',  # Sam upvotes
            HTTP_REFERER=f'/questions/{self.q.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.q.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, 1)  # Sam's upvote counted

        for _ in range(2):
            '''
            Sam downvotes twice:
            * first - he changes his mind and reset his voice
            * second - he downvotes
            '''
            response = self.client.get(
                # Sam downvotes
                f'/questions/answervote/{self.alice_answer.id}/0',
                HTTP_REFERER=f'/questions/{self.q.id}'
            )
            self.assertRedirects(
                response, f'/questions/{self.q.id}',
                status_code=302, target_status_code=200)
            self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, -1)  # Sam's downvote counted

        response = self.client.get(
                # Sam upvotes thus resetting his voice back to zero
                f'/questions/answervote/{self.alice_answer.id}/1',
                HTTP_REFERER=f'/questions/{self.q.id}'
            )
        self.assertRedirects(
            response, f'/questions/{self.q.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, 0)

    def test_answer_vote_author_restriction(self):
        '''
        Alice cannot upvote and downvote her own answer
        '''
        self.assertEqual(self.alice_answer.votes, 0)  # no votes yet

        self.client.force_login(self.alice)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            f'/questions/answervote/{self.alice_answer.id}/1',
            HTTP_REFERER=f'/questions/{self.q.id}'
        )
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, 0)  # Alice's upvote not counted

        response = self.client.get(
            # Alice tries to downvote
            f'/questions/answervote/{self.alice_answer.id}/0',
            HTTP_REFERER=f'/questions/{self.q.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.q.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_answer = Answer.objects.get(id=self.alice_answer.id)
        self.assertEqual(alice_answer.votes, 0)  # Alice's downvote not counted

    def test_answer_vote_unauthorized(self):
        '''
        Not logged in user cannot vote for answers
        '''
        for vote in ('0', '1'):
            with self.subTest(vote=vote):
                response = self.client.get(
                    f'/questions/answervote/{self.alice_answer.id}/{vote}',
                    HTTP_REFERER=f'/questions/{self.q.id}'
                )
                self.assertRedirects(
                    response,
                    (
                        '/users/login?next=' +
                        '/questions/answervote/' +
                        f'{self.alice_answer.id}/{vote}'
                    ),
                    status_code=302, target_status_code=200)


class TestQuestionVoting(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.sam = User.objects.create_user(
            username='Sam',
            email='sam@pisem.net',
            password='sampassword'
        )
        cls.sam.save()
        cls.alice = User.objects.create_user(
            username='Alice',
            email='alice@wonderland.com',
            password='alicepass'
        )
        cls.alice.save()
        cls.bob = User.objects.create_user(
            username='Bob',
            email='bob@wonderland.com',
            password='bobpass'
        )
        cls.bob.save()
        cls.alice_question = Question(
            title='How to Django?',
            author=cls.alice,
            content='Lorem ipsum dolor est'
        )
        cls.alice_question.save()

    def test_question_upvote_basics(self):
        '''
        Sam and Bob can upvote Alice's question
        '''
        self.assertEqual(self.alice_question.votes, 0)  # no votes yet

        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            # Sam upvotes
            f'/questions/questionvote/{self.alice_question.id}/1',
            HTTP_REFERER=f'/questions/{self.alice_question.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.alice_question.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, 1)  # Sam's upvote counted

        self.client.force_login(self.bob)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.client.get(
            # Bob upvotes
            f'/questions/questionvote/{self.alice_question.id}/1',
            HTTP_REFERER=f'/questions/{self.alice_question.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.alice_question.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        self.assertTemplateUsed('questions/question.html')
        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, 2)  # Bob's upvote counted

    def test_question_downvote_basics(self):
        '''
        Sam and Bob can downvote Alice's question
        '''
        self.assertEqual(self.alice_question.votes, 0)  # no votes yet

        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            # Sam downvotes
            f'/questions/questionvote/{self.alice_question.id}/0',
            HTTP_REFERER=f'/questions/{self.alice_question.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.alice_question.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, -1)  # Sam's downvote counted

        self.client.force_login(self.bob)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.client.get(
            # Bob downvotes
            f'/questions/questionvote/{self.alice_question.id}/0',
            HTTP_REFERER=f'/questions/{self.alice_question.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.alice_question.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        self.assertTemplateUsed('questions/question.html')
        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, -2)  # Bob's downvote counted

    def test_question_vote_upvotes_and_downvotes(self):
        '''
        Sam can upvote, can downvote and change his mind
        '''
        self.assertEqual(self.alice_question.votes, 0)  # no votes yet

        self.client.force_login(self.sam)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            # Sam upvotes
            f'/questions/questionvote/{self.alice_question.id}/1',
            HTTP_REFERER=f'/questions/{self.alice_question.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.alice_question.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, 1)  # Sam's upvote counted

        for _ in range(2):
            '''
            Sam downvotes twice:
            * first, he canceles his previous upvote
            * second, he simply downvotes
            '''
            response = self.client.get(

                f'/questions/questionvote/{self.alice_question.id}/0',
                HTTP_REFERER=f'/questions/{self.alice_question.id}'
            )
            self.assertRedirects(
                response, f'/questions/{self.alice_question.id}',
                status_code=302, target_status_code=200)

        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, -1)  # downvoted

        response = self.client.get(
            # Sam upvotes again, aims to cancel his vote
            f'/questions/questionvote/{self.alice_question.id}/1',
            HTTP_REFERER=f'/questions/{self.alice_question.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.alice_question.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, 0)  # Sam resetted his vote

    def test_question_vote_author_restriction(self):
        '''
        Alice cannot upvote and downvote her own question
        '''
        self.assertEqual(self.alice_question.votes, 0)  # no votes yet

        self.client.force_login(self.alice)
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        response = self.client.get(
            # Alice tries to upvote her question herself
            f'/questions/questionvote/{self.alice_question.id}/1',
            HTTP_REFERER=f'/questions/{self.alice_question.id}'
        )
        self.assertRedirects(
            response, f'/questions/{self.alice_question.id}',
            status_code=302, target_status_code=200)
        self.assertTemplateUsed('questions/question.html')
        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, 0)  # nothing should change

        response = self.client.get(
            # Alice tries to downvote her question herself
            f'/questions/questionvote/{self.alice_question.id}/0',
            HTTP_REFERER=f'/questions/{self.alice_question.id}'
        )
        alice_question = Question.objects.get(id=self.alice_question.id)
        self.assertEqual(alice_question.votes, 0)  # no changes

    def test_question_vote_unauthorized(self):
        '''
        Not logged in user cannot vote for questions
        '''
        for vote in ('0', '1'):
            with self.subTest(vote=vote):
                response = self.client.get(
                    f'/questions/questionvote/{self.alice_question.id}/{vote}',
                    HTTP_REFERER=f'/questions/{self.alice_question.id}'
                )
                self.assertRedirects(
                    response,
                    (
                        '/users/login?next=' +
                        '/questions/questionvote/' +
                        f'{self.alice_question.id}/{vote}'
                    ),
                    status_code=302, target_status_code=200)
