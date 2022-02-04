from .models import Question, Answer, Tag
from users.models import User
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.http import HttpResponseRedirect
from django.urls import reverse

#  from django.http import HttpResponse


def index(request):
    queryset = Question.objects.all()
    context = {'queryset': queryset}
    return render(request, 'questions/index.html', context)


def question(request, question_id, fallback=False):
    try:
        qw = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404('No such question :(')
    try:
        answer_query = Answer.objects.filter(question=question_id)
    except ObjectDoesNotExist:
        answer_query = None
    try:
        tags = []
        query_tags = Tag.objects.filter(questions=question_id)
        if len(query_tags):
            tags = [tag.title for tag in query_tags]
    except ObjectDoesNotExist:
        pass
    context = {
        'question': qw, 'answer_query': answer_query, 'tags': tags
    }
    if not fallback:
        return render(request, 'questions/question.html', context)
    else:
        return [request, 'questions/question.html', context]


def answer_question(request, question_id):
    qw = Question.objects.get(pk=question_id)
    try:
        answer_text = request.POST['answer_text']
    except (KeyError, Answer.DoesNotExist):
        r = question(request, question_id, fallback=True)
        r[2].update({'error_message': 'Error occured! Try again please'})
        return render(request=r[0], template_name=r[1], context=r[2])
    else:
        answer = Answer(author=User.objects.get(username='Sammy'), question=qw,
                        content=answer_text)
        answer.save()
        return HttpResponseRedirect(
            reverse('questions:question', args=(qw.id,)))
