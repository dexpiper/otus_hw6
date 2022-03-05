import random
from datetime import datetime, timezone, timedelta

from django.test import TestCase
from django.contrib.auth.models import User

from questions.models import Question, Tag
from questions.helpers import get_time_diff, save_tags


class TestSaveTagHelper(TestCase):

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
        self.python_tag = Tag(
            title='Python'
        )
        self.python_tag.save()

    def test_all_new_tags(self):
        try:
            save_tags('Otus Lorem Ipsum'.split(), self.q, Tag)
            Tag.objects.get(title='Otus')
            Tag.objects.get(title='Lorem')
            Tag.objects.get(title='Ipsum')
        except Tag.DoesNotExist:
            self.fail('Save_tags did not created tags')
        self.assertEqual(self.q.tags.all().count(), 3)

    def test_mixed_new_and_old_tags(self):
        self.assertEqual(self.python_tag.title, 'Python')
        save_tags('Python Getting Rock'.split(), self.q, Tag)
        try:
            Tag.objects.get(title='Python')
            Tag.objects.get(title='Getting')
            Tag.objects.get(title='Rock')
        except Tag.DoesNotExist:
            self.fail('Save_tags did not created tags')
        self.assertEqual(self.q.tags.all().count(), 3)
        self.assertEqual(self.python_tag,
                         Tag.objects.get(title='Python'))

    def test_only_old_tags(self):
        self.assertEqual(self.python_tag.title, 'Python')
        lorem_tag = Tag(title='Lorem')
        lorem_tag.save()
        ipsum_tag = Tag(title='Ipsum')
        ipsum_tag.save()
        save_tags('Python Lorem Ipsum'.split(), self.q, Tag)
        try:
            Tag.objects.get(title='Python')
            Tag.objects.get(title='Lorem')
            Tag.objects.get(title='Ipsum')
        except Tag.DoesNotExist:
            self.fail('Save_tags did not created tags')
        self.assertEqual(self.q.tags.all().count(), 3)


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
