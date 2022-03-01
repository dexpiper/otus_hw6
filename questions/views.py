from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings

from .models import Question, Answer, Tag, QuestionVoters, AnswerVoters

from hasker.signals import question_answered
from .forms import QuestionForm, AnswerForm
from .helpers import save_tags


num_pages = settings.ELEMENTS_PER_PAGE


def index(request, pages=num_pages):
    queryset = Question.objects.all().order_by('-created_on', 'title')
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'questions/index.html', context)


def index_hot(request, pages=num_pages):
    queryset = Question.objects.all().order_by('-votes', 'title')
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'questions/hot_questions.html', context)


def search_tag(request, tag_id, pages=num_pages):
    tag = Tag.objects.get(id=tag_id)
    queryset = tag.questions.all()
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'tag': tag
    }
    return render(request, 'questions/tag.html', context)


def index_search(request, pages=num_pages):
    """
    Search question by search phrase or by tag
    """
    search: str = request.POST.get('search', None)
    if search.startswith('tag:'):
        tag_name = search[4:].strip()
        try:
            tag = Tag.objects.get(title=tag_name)
        except ObjectDoesNotExist:
            context = {'error_message': f'No tag {tag_name} found'}
            return render(request, 'questions/search.html', context)
        return search_tag(request, tag_id=tag.id)

    queryset = Question.objects.select_related().filter(
            Q(title__icontains=search)
          | Q(content__icontains=search)                        # noqa E131
          | Q(answer__content__icontains=search)                # noqa E131
        ).distinct().order_by('-votes', '-created_on')
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'searchstring': search
    }
    return render(request, 'questions/search.html', context)


def show_question(request, question_id):
    """
    Show question page or post a new answer for a question
    """
    qw = get_object_or_404(Question, pk=question_id)
    context = {'question': qw}
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('users:login')
        form = AnswerForm(request.POST, question_id=question_id)
        if form.is_valid():
            content = request.POST.get('content', None)
            answer = Answer(author=request.user, question=qw,
                            content=content)
            answer.save()
            # send a signal for question author about new answer
            question_answered.send(sender=show_question, question=qw)
    else:
        form = AnswerForm()

    answer_query = Answer.objects.filter(question=question_id).order_by(
        '-votes', '-answer_flag', '-created_on')
    tags = Tag.objects.filter(questions=question_id)
    context.update({'answer_query': answer_query, 'tags': tags, 'form': form})
    return render(request, 'questions/question.html', context)


@login_required
def make_question(request):
    context = {}
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data.get('title')
            content = form.cleaned_data.get('content')
            tags = form.cleaned_data.get('tags')
            question = Question(
                author=request.user,
                title=title,
                content=content
            )
            question.save()
            save_tags(tags, question, Tag)
            return redirect('questions:question', question_id=question.id)
    else:
        form = QuestionForm()
    context['form'] = form
    return render(request, 'questions/make_question.html', context)


@login_required
def alter_flag(request, answer_id):
    answer = Answer.objects.get(pk=answer_id)
    qw = answer.question
    if not qw.author.id == request.user.id:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    if qw.author.id == answer.author.id:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
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


@login_required
def answer_vote(request, answer_id, upvote=1):
    answer = Answer.objects.get(pk=answer_id)
    if answer.author.id == request.user.id:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    voters_number = AnswerVoters.objects.filter(
        entity_id=answer, user_id=request.user).count()
    if not voters_number:
        user_vote = AnswerVoters(entity_id=answer,
                                 user_id=request.user)
    else:
        user_vote = AnswerVoters.objects.get(
            entity_id=answer, user_id=request.user)
    if upvote:
        if user_vote.vote in (0, -1):
            answer.votes += 1
            user_vote.vote += 1
            user_vote.save()
        else:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        if user_vote.vote in (0, 1):
            answer.votes -= 1
            user_vote.vote -= 1
            user_vote.save()
        else:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
    answer.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def question_vote(request, question_id, upvote=1):
    qw = Question.objects.get(pk=question_id)
    if qw.author.id == request.user.id:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    voters_number = QuestionVoters.objects.filter(
        entity_id=question_id, user_id=request.user).count()
    if not voters_number:
        user_vote = QuestionVoters(entity_id=qw,
                                   user_id=request.user)
    else:
        user_vote = QuestionVoters.objects.get(
            entity_id=qw, user_id=request.user)
    if upvote:
        if user_vote.vote in (0, -1):
            qw.votes += 1
            user_vote.vote += 1
            user_vote.save()
        else:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        if user_vote.vote in (0, 1):
            qw.votes -= 1
            user_vote.vote -= 1
            user_vote.save()
        else:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
    qw.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
