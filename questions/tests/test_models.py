import random

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.lorem_ipsum import words, paragraphs
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from questions.models import Question, Answer, Tag, Voters


class TestQuestion(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
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
            email='bob@bobpost.org',
            password='bobpass'
        )
        cls.bob.save()
        cls.users = cls.sam, cls.alice, cls.bob

    def setUp(self):
        self.q = Question(
            title='How to Django?',
            author=self.sam,
            content='Lorem ipsum dolor est'
        )
        self.q.save()

    def test_making_question(self):
        self.assertEqual(self.q.title, 'How to Django?')
        self.assertEqual(self.q.author, self.sam)
        self.assertEqual(self.q.content, 'Lorem ipsum dolor est')

    def test_default_question_params(self):
        self.assertEqual(self.q.status, 0)
        self.assertEqual(self.q.votes, 0)

    def test_voting_changed(self):
        for i in (5, 8, -1, 0, 42, -18, 368):
            with self.subTest(i=i):
                self.q.votes = i
                self.q.save()
                self.assertEqual(self.q.votes, i)

    def test_trending_logic(self):
        '''
        Check if Question.trending() method returns asked number
        of trending questions in the right order (from max to min)
        '''
        def make_questions(range):
            '''
            Save to db a <range> of random questions with random ratings.
            '''
            questions = []
            for _ in range:
                questions.append(
                    Question(
                        title=words(
                            random.randint(3, 6),
                            common=False) + str(random.randint(-1000, 1000)),
                        author=self.users[random.randint(0, 2)],
                        content=paragraphs(random.randint(1, 3)),
                        status=random.randint(0, 1),
                        votes=random.randint(-100, 100)
                    )
                )
            Question.objects.bulk_create(questions)
            return questions

        r = range(settings.TRENDING_QUESTIONS_NUMBER + random.randint(15, 40))
        qws = make_questions(r)

        self.assertGreaterEqual(
            len(qws),
            settings.TRENDING_QUESTIONS_NUMBER + 15)
        self.assertGreaterEqual(
            Question.objects.all().count(),
            settings.TRENDING_QUESTIONS_NUMBER + 15)

        trending_qws = Question.trending()
        self.assertEqual(len(trending_qws), settings.TRENDING_QUESTIONS_NUMBER)

        last_rating = trending_qws[0].votes  # rating of the top No 1 question
        for qw in trending_qws[1:]:
            self.assertLessEqual(qw.votes, last_rating)


class TestAnswers(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # users
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
            email='bob@bobpost.org',
            password='bobpass'
        )
        cls.bob.save()
        cls.users = cls.sam, cls.alice, cls.bob

        # questions
        cls.qw1 = Question(
            title='How to Django?',
            author=cls.sam,
            content='Lorem ipsum dolor est'
        )
        cls.qw1.save()
        cls.qw2 = Question(
            title='How not to Django?',
            author=cls.alice,
            content='Lorem dolor ipsum est'
        )
        cls.qw2.save()
        cls.qw3 = Question(
            title='How to OTUS?',
            author=cls.bob,
            content='Ipsum lorem dolor ne est'
        )
        cls.qw3.save()
        cls.questions = cls.qw1, cls.qw2, cls.qw3

    def setUp(self):
        self.ans = Answer(
            author=self.alice,
            question=self.qw1,
            content='If lorem ipsum or dolor est, do django'
        )
        self.ans.save()

    def test_answer_basic_creation(self):
        self.assertEqual(self.ans.author, self.alice)
        self.assertEqual(self.ans.question.id, self.qw1.id)
        self.assertEqual(self.ans.content,
                         'If lorem ipsum or dolor est, do django')

    def test_default_params(self):
        self.assertEqual(self.ans.answer_flag, 0)
        self.assertEqual(self.ans.votes, 0)

    def test_set_new_flag(self):
        '''
        Sam markes Alice's answer as the best
        '''
        self.assertEqual(self.qw1.status, 0)
        self.ans.set_new_flag()
        self.assertEqual(self.qw1.status, 1)
        self.assertEqual(self.ans.answer_flag, 1)

    def test_change_flag(self):
        '''
        Sam changes his mind: Bob's answer is better than Alice's
        '''
        # do the same
        self.assertEqual(self.qw1.status, 0)
        self.ans.set_new_flag()
        self.assertEqual(self.qw1.status, 1)
        self.assertEqual(self.ans.answer_flag, 1)
        # get better answer
        another_good_answer = Answer(
            author=self.bob,
            question=self.qw1,
            content='Believe you can and you re halfway there'
        )
        another_good_answer.save()
        self.assertEqual(another_good_answer.answer_flag, 0)
        # change flag and check
        another_good_answer.change_flag()
        self.assertEqual(self.qw1.status, 1)
        self.assertEqual(another_good_answer.answer_flag, 1)  # new one
        self.assertEqual(
            self.qw1.answer_set.get(answer_flag=1), another_good_answer
        )
        answers = self.qw1.answer_set.all()
        self.assertEqual(len(answers), 2)
        # only single one may be the best answer
        for answer in answers:
            best_answers = 0
            if answer.answer_flag == 1:
                best_answers += 1
        self.assertEqual(best_answers, 1)
        self.assertIn(self.ans, answers)
        self.assertIn(another_good_answer, answers)

        # go to db and update old answer data (self.ans)
        old_answer = Answer.objects.get(pk=self.ans.id)
        self.assertEqual(old_answer.answer_flag, 0)

    def test_delete_flag(self):
        '''
        Sam changes his mind and delete 'best' mark from Alice's answer
        '''
        # do the same
        self.assertEqual(self.qw1.status, 0)
        self.ans.set_new_flag()
        self.assertEqual(self.qw1.status, 1)
        self.assertEqual(self.ans.answer_flag, 1)
        # and delete flag
        self.ans.delete_flag()
        self.assertEqual(self.qw1.status, 0)
        self.assertEqual(self.ans.answer_flag, 0)

    def test_question_answers_number(self):
        self.assertEqual(self.qw2.get_answers_number(), 0)
        answer1 = Answer(
            author=self.bob,
            question=self.qw2,
            content='Believe you can and you re halfway there'
        )
        answer1.save()
        self.assertEqual(self.qw2.get_answers_number(), 1)

        answer2 = Answer(
            author=self.alice,
            question=self.qw2,
            content='Do that and do not do this'
        )
        answer2.save()
        self.assertEqual(self.qw2.get_answers_number(), 2)

        # add five new answers
        for i in range(5):
            answers_lot = []
            answers_lot.append(
                Answer(
                    author=self.users[random.randint(0, 2)],
                    question=self.qw2,
                    content=paragraphs(random.randint(1, 3))
                )
            )
            Answer.objects.bulk_create(answers_lot)
        self.assertEqual(self.qw2.get_answers_number(), 7)  # 2 + 5 = 7


class TestTag(TestCase):

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

    def setUp(self):
        self.tag = Tag(
            title='Python'
        )
        self.tag.save()

    def test_tag_creation(self):
        self.assertEqual(self.tag.title, 'Python')
        self.assertTrue(self.tag.questions.all().count() == 0)

    def test_tag_add_question(self):
        self.tag.questions.add(self.q)
        self.assertTrue(self.tag.questions.all().count() == 1)
        self.assertEqual(self.tag.questions.get(pk=self.q.id), self.q)

    def test_tag_add_multiple_questions(self):
        for i in range(3):
            q = Question(
                    title=words(4, False) + str(i),
                    author=self.sam,
                    content=(paragraphs(1, False))
                )
            q.save()
            self.tag.questions.add(q)
        self.assertTrue(self.tag.questions.all().count() == 3)

    def test_tag_return_title_as_str(self):
        self.assertEqual(str(self.tag), 'Python')


class TestVoters(TestCase):

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
            email='alice@wonderland.net',
            password='alicepassword'
        )
        cls.alice.save()
        cls.q = Question(
            title='How to Django?',
            author=cls.sam,
            content='Lorem ipsum dolor est'
        )
        cls.q.save()
        cls.a = Answer(
            author=cls.sam,
            question=cls.q,
            content=words(10, common=False)
        )
        cls.a.save()

    def test_basic_votes_creation_question(self):
        vote = Voters(content_object=self.q, user_id=self.sam.id)
        vote.save()
        object_ct = ContentType.objects.get_for_model(self.q)
        self.assertEqual(
            Voters.objects.filter(
                content_type=object_ct,
                object_id=self.q.id,
                user_id=self.sam.id
            ).count(), 1)
        retrieved_vote = Voters.objects.get(
            content_type=object_ct,
            object_id=self.q.id,
            user_id=self.sam.id
        )
        self.assertEqual(retrieved_vote.user_id,
                         self.sam.id)
        self.assertEqual(retrieved_vote.object_id,
                         self.q.id)
        self.assertEqual(retrieved_vote.vote, 0)

    def test_register_q_upvote(self):
        Voters.register_vote(self.q, self.sam.id, vote=1)
        object_ct = ContentType.objects.get_for_model(self.q)
        retrieved_vote = Voters.objects.get(
            content_type=object_ct,
            object_id=self.q.id,
            user_id=self.sam.id
        )
        self.assertEqual(retrieved_vote.vote, 1)

    def test_register_q_downvote(self):
        Voters.register_vote(self.q, self.sam.id, vote=0)
        object_ct = ContentType.objects.get_for_model(self.q)
        retrieved_vote = Voters.objects.get(
            content_type=object_ct,
            object_id=self.q.id,
            user_id=self.sam.id
        )
        self.assertEqual(retrieved_vote.vote, -1)

    def test_register_ans_upvote(self):
        Voters.register_vote(self.a, self.sam.id, vote=1)
        object_ct = ContentType.objects.get_for_model(self.a)
        retrieved_vote = Voters.objects.get(
            content_type=object_ct,
            object_id=self.a.id,
            user_id=self.sam.id
        )
        self.assertEqual(retrieved_vote.vote, 1)

    def test_register_ans_downvote(self):
        Voters.register_vote(self.a, self.sam.id, vote=0)
        object_ct = ContentType.objects.get_for_model(self.a)
        retrieved_vote = Voters.objects.get(
            content_type=object_ct,
            object_id=self.a.id,
            user_id=self.sam.id
        )
        self.assertEqual(retrieved_vote.vote, -1)

    def test_register_assert_integrity_answers(self):
        '''
        Check that user upvote and downvote only in corridor (-1, 0, 1)
        '''
        def check(object: Answer or Question):
            first_upvote = Voters.register_vote(object, self.sam.id, vote=1)
            second_upvote = Voters.register_vote(object, self.sam.id, vote=1)
            self.assertTrue(first_upvote)
            self.assertFalse(second_upvote)
            object_ct = ContentType.objects.get_for_model(object)
            retrieved_vote = Voters.objects.get(
                content_type=object_ct,
                object_id=object.id,
                user_id=self.sam.id
            )
            self.assertEqual(retrieved_vote.vote, 1)  # now vote is 1
            self.assertEqual(object.votes, 1)

            first_downvote = Voters.register_vote(object, self.sam.id, vote=0)
            second_downvote = Voters.register_vote(object, self.sam.id, vote=0)
            third_downvote = Voters.register_vote(object, self.sam.id, vote=0)
            self.assertTrue(first_downvote)
            self.assertTrue(second_downvote)
            self.assertFalse(third_downvote)
            retrieved_vote = Voters.objects.get(
                content_type=object_ct,
                object_id=object.id,
                user_id=self.sam.id
            )
            self.assertEqual(retrieved_vote.vote, -1)  # now vote is -1
            self.assertEqual(object.votes, -1)

            first_upvote = Voters.register_vote(object, self.sam.id, vote=1)
            second_upvote = Voters.register_vote(object, self.sam.id, vote=1)
            third_upvote = Voters.register_vote(object, self.sam.id, vote=1)
            self.assertTrue(first_upvote)
            self.assertTrue(second_upvote)
            self.assertFalse(third_upvote)
            retrieved_vote = Voters.objects.get(
                content_type=object_ct,
                object_id=object.id,
                user_id=self.sam.id
            )
            self.assertEqual(retrieved_vote.vote, 1)  # vote again is 1
            self.assertEqual(object.votes, 1)

            alice_voted = Voters.register_vote(object, self.alice.id, vote=1)
            self.assertTrue(alice_voted)  # Alice still can vote after Sam
            self.assertEqual(object.votes, 2)

        for obj in (self.q, self.a):     # for Questions and for Answers
            with self.subTest(obj=obj):
                check(obj)
