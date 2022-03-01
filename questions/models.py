from django.db import models
from django.conf import settings as sett
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from .helpers import get_time_diff


QUESTION_STATUS = (
    (0, 'No_answer'),
    (1, 'Answered')
)

ANSWER_STATUS = (
    (0, 'Just_answer'),
    (1, 'Right_answer')
)

VOTE_STATUS = (
    (-1, 'Downvote'),
    (0, 'No_vote'),
    (1, 'Upvote')
)


class Question(models.Model):
    title = models.CharField(max_length=200, unique=True)
    author = models.ForeignKey(sett.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=QUESTION_STATUS, default=0)
    votes = models.IntegerField(default=0)

    def __str___(self):
        return self.title

    def get_answers_number(self):
        return Answer.objects.filter(question=self.id).count()

    def get_tags(self):
        return Tag.objects.filter(questions=self.id)

    @property
    def number_answers(self):
        return self.get_answers_number()

    @property
    def tags(self):
        return self.get_tags()

    @property
    def asked_ago(self):
        return get_time_diff(self.created_on)

    @classmethod
    def trending(cls):
        queryset = cls.objects.all().order_by('-votes')
        # return first X trending questions
        return queryset[:sett.TRENDING_QUESTIONS_NUMBER]


class Answer(models.Model):
    author = models.ForeignKey(sett.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    answer_flag = models.IntegerField(choices=ANSWER_STATUS, default=0)
    votes = models.IntegerField(default=0)

    @transaction.atomic
    def set_new_flag(self):
        """
        Question author marked the answer as 'best'. Set 'answer flag'
        for the answer (from 0 to 1) and set question status as 'answer
        given' (1).
        """
        qw = self.question
        self.answer_flag = 1
        qw.status = 1
        qw.save()
        self.save()

    @transaction.atomic
    def change_flag(self):
        """
        Question author changed his/her mind and marked another answer
        as best. Set 'answer flag' for the answer (from 0 to 1) and set
        question status as 'answer given' (1).
        """
        qw = self.question
        prev_answer = qw.answer_set.get(answer_flag=1)
        prev_answer.answer_flag = 0
        self.answer_flag = 1
        prev_answer.save()
        self.save()

    @transaction.atomic
    def delete_flag(self):
        """
        Question author decided to unlabel the answer as 'best answer'.
        Delete 'answer flag' for the answer (set 0) and change question
        status from 'answer given' (1) to 'no answer' (0).
        """
        qw = self.question
        self.answer_flag = 0
        qw.status = 0
        self.save()
        qw.save()


class Tag(models.Model):
    title = models.CharField(max_length=15, unique=True)
    questions = models.ManyToManyField(Question)

    def __str__(self):
        return self.title


class Voters(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    vote = models.IntegerField(choices=VOTE_STATUS, default=0)
    user_id = models.PositiveIntegerField()
