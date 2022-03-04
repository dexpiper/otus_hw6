import random
from datetime import datetime, timezone, timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.lorem_ipsum import words, paragraphs
from django.conf import settings

from questions.models import Question, Answer
from questions.helpers import get_time_diff


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
    pass


class TestVoters(TestCase):
    pass


class TestTimediffHelper(TestCase):

    attempts = range(1000)

    def test_now(self):
        s = get_time_diff(datetime.now(timezone.utc))
        self.assertEqual(s, 'Just now')

    def test_seconds(self):
        for _ in self.attempts:
            random_seconds = random.randint(1, 58)
            with self.subTest(random_minutes=random_seconds):
                seconds_ago = (
                    datetime.now(timezone.utc)
                    - timedelta(seconds=random_seconds)
                )
                s = get_time_diff(seconds_ago)
                self.assertEqual(s, 'Just now')

    def test_minutes(self):
        for _ in self.attempts:
            random_minutes = random.randint(2, 58)
            with self.subTest(random_minutes=random_minutes):
                minutes_ago = (
                    datetime.now(timezone.utc)
                    - timedelta(minutes=random_minutes)
                )
                s = get_time_diff(minutes_ago)
                self.assertIn('minute(s) ago', s)
                int_result = int(s.split()[0])
                self.assertAlmostEqual(int_result, random_minutes, delta=0.8)

    def test_hours(self):
        for _ in self.attempts:
            random_hours = random.randint(1, 23)
            with self.subTest(random_hours=random_hours):
                hours_ago = (
                    datetime.now(timezone.utc)
                    - timedelta(hours=random_hours)
                )
                s = get_time_diff(hours_ago)
                self.assertIn('hour(s) ago', s)
                int_result = int(s.split()[0])
                self.assertAlmostEqual(int_result, random_hours, delta=0.8)

    def test_days(self):
        for _ in self.attempts:
            random_days = random.randint(1, 6)
            with self.subTest(random_days=random_days):
                days_ago = (
                    datetime.now(timezone.utc)
                    - timedelta(days=random_days)
                )
                s = get_time_diff(days_ago)
                self.assertIn('day(s) ago', s)
                int_result = int(s.split()[0])
                self.assertAlmostEqual(int_result, random_days, delta=0.5)

    def test_weeks(self):
        for _ in self.attempts:
            random_weeks = random.randint(1, 4)
            with self.subTest(random_weeks=random_weeks):
                weeks_ago = (
                    datetime.now(timezone.utc)
                    - timedelta(weeks=random_weeks)
                )
                s = get_time_diff(weeks_ago)
                self.assertIn('week(s) ago', s)
                int_result = int(s.split()[0])
                self.assertAlmostEqual(int_result, random_weeks, delta=0.5)

    def test_months(self):
        for _ in self.attempts:
            random_months = random.randint(1, 12)
            with self.subTest(random_months=random_months):
                months_ago = (
                    datetime.now(timezone.utc)
                    - timedelta(days=random_months*30)
                )
                s = get_time_diff(months_ago)
                self.assertIn('month(s) ago', s)
                int_result = int(s.split()[0])
                self.assertAlmostEqual(int_result, random_months, delta=0.2)

    def test_years(self):
        for _ in self.attempts:
            random_years = random.randint(1, 20)
            with self.subTest(random_years=random_years):
                years_ago = (
                    datetime.now(timezone.utc)
                    - timedelta(days=random_years*365)
                )
                s = get_time_diff(years_ago)
                self.assertIn('year(s) ago', s)
                int_result = int(s.split()[0])
                self.assertAlmostEqual(int_result, random_years, delta=0.1)
