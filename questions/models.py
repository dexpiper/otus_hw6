from django.db import models
from django.conf import settings as sett


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

    def __str___(self):
        return self.title


class Answer(models.Model):
    author = models.ForeignKey(sett.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    answer_flag = models.IntegerField(choices=ANSWER_STATUS, default=0)


class Tag(models.Model):
    title = models.CharField(max_length=15, unique=True)
    questions = models.ManyToManyField(Question)
