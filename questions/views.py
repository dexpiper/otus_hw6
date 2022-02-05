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
        tags = Tag.objects.filter(questions=question_id)
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


def make_question(request):
    return render(request, 'questions/make_question.html')


def save_question(request):
    try:
        username = request.POST['username']
        question_title = request.POST['title']
        question_content = request.POST['content']
        question_tags = request.POST['tags'].split()
    except (KeyError, ObjectDoesNotExist):
        raise
    try:
        question = Question(
            author=User.objects.get(username=username),
            title=question_title,
            content=question_content
        )
        question.save()
    except ObjectDoesNotExist:
        raise
    if question_tags:
        for tag in question_tags:
            tag = tag.strip()
            try:
                old_tag = Tag.objects.get(title=tag)
            except ObjectDoesNotExist:
                pass
            else:
                old_tag.questions.add(question)
                continue
            try:
                t = Tag.objects.create(title=tag)
                t.questions.add(question)
            except (KeyError, TypeError, ObjectDoesNotExist):
                raise
    return HttpResponseRedirect(
        reverse('questions:question', args=(question.id,)))


def search_tag(request, tag_id):
    queryset = Tag.objects.get(id=tag_id).questions.all()
    context = {'queryset': queryset}
    return render(request, 'questions/tag.html', context)


def alter_flag(request, answer_id):
    answer = Answer.objects.get(pk=answer_id)
    qw = answer.question
    if answer.answer_flag == 1:
        answer.answer_flag = 0
        qw.status = 0
        answer.save()
        qw.save()
    else:
        if qw.status == 0:
            answer.answer_flag = 1
            qw.status = 1
            qw.save()
            answer.save()
        elif qw.status == 1:
            prev_answer = qw.answer_set.get(answer_flag=1)
            prev_answer.answer_flag = 0
            answer.answer_flag = 1
            prev_answer.save()
            answer.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
