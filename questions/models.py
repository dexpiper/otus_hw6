from django.db import models
from django.conf import settings as sett

from .helpers import get_time_diff


QUESTION_STATUS = (
    (0, 'No_answer'),
    (1, 'Answered')
)

ANSWER_STATUS = (
    (0, 'Just_answer'),
    (1, 'Right_answer')
)


# Create your models here.
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
        return queryset[:6]


class Answer(models.Model):
    author = models.ForeignKey(sett.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    answer_flag = models.IntegerField(choices=ANSWER_STATUS, default=0)
    votes = models.IntegerField(default=0)


class Tag(models.Model):
    title = models.CharField(max_length=15, unique=True)
    questions = models.ManyToManyField(Question)
