from django.db.models import Q
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator

from .models import Question, Answer, Tag, QuestionVoters, AnswerVoters

from hasker.helpers import render_with_error
from hasker.signals import question_answered


def index(request, pages=20):
    queryset = Question.objects.all().order_by('-created_on', 'title')
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'trending': Question.trending(),
        'page_obj': page_obj
    }
    return render(request, 'questions/index.html', context)


def index_hot(request, pages=20):
    queryset = Question.objects.all().order_by('-votes', 'title')
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'trending': Question.trending(),
        'page_obj': page_obj
    }
    return render(request, 'questions/hot_questions.html', context)


def index_search(request, pages=20):
    search: str = request.POST.get('search', None)
    if search.startswith('tag:'):
        tag_name = search[4:].strip()
        try:
            tag = Tag.objects.get(title=tag_name)
        except ObjectDoesNotExist:
            context = {'error_message': f'No tag {tag_name} found',
                       'trending': Question.trending()}
            return render(request, 'questions/search.html', context)
        return search_tag(request, tag_id=tag.id)
    if len(search) > 30:
        search = search[:30]
    queryset = Question.objects.select_related().filter(
            Q(title__icontains=search)
          | Q(content__icontains=search)                        # noqa E131
          | Q(answer__content__icontains=search)                # noqa E131
        ).distinct().order_by('-votes', '-created_on')
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'trending': Question.trending(),
        'page_obj': page_obj,
        'searchstring': search
    }
    return render(request, 'questions/search.html', context)


def question(request, question_id, fallback=False):
    try:
        qw = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404('No such question :(')
    try:
        answer_query = Answer.objects.filter(question=question_id).order_by(
            '-votes', '-answer_flag')
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
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            reverse('users:login', args=()))
    qw = Question.objects.get(pk=question_id)
    try:
        answer_text = request.POST['answer_text']
    except (KeyError, Answer.DoesNotExist):
        r = question(request, question_id, fallback=True)
        r[2].update({'error_message': 'Error occured! Try again please'})
        return render(request=r[0], template_name=r[1], context=r[2])
    else:
        answer = Answer(author=request.user, question=qw,
                        content=answer_text)
        answer.save()
        question_answered.send(sender=answer_question, qw_author=qw.author)
        return HttpResponseRedirect(
            reverse('questions:question', args=(qw.id,)))


def make_question(request, fallback=False):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            reverse('users:login', args=()))
    if not fallback:
        return render(request, 'questions/make_question.html', {})
    else:
        return [request, 'questions/make_question.html', {}]


def save_question(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            reverse('users:login', args=()))
    question_title = request.POST.get('title', None)
    question_content = request.POST.get('content', None)
    question_tags = request.POST.get('tags', None)
    question_id = request.POST.get('question_id', None)  # normally None
    if not all((question_title, question_content)):
        return render_with_error(make_question, request,
                                 errormsg='Please fill in title and content',
                                 question_id=question_id or None,
                                 question_title=question_title,
                                 question_content=question_content)
    if question_id:
        question = Question.objects.get(pk=question_id)
        question.title = question_title
        question.content = question_content
        question.save()
    else:
        question = Question(
                author=request.user,
                title=question_title,
                content=question_content
            )
        question.save()
    if question_tags:
        question_tags = question_tags.split()
        if len(question_tags) > 3:
            return render_with_error(
                make_question, request,
                errormsg='You can only provide up to 3 tags',
                question_title=question_title,
                question_content=question_content,
                question_id=question.id
            )
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
            except (KeyError, TypeError, ValueError, ObjectDoesNotExist):
                return render_with_error(
                    make_question, request,
                    errormsg='Error with tag creation. Please try again.'
                )
    return HttpResponseRedirect(
        reverse('questions:question', args=(question.id,)))


def search_tag(request, tag_id, pages=20):
    tag = Tag.objects.get(id=tag_id)
    queryset = tag.questions.all()
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'trending': Question.trending(),
        'page_obj': page_obj,
        'tag': tag
    }
    return render(request, 'questions/tag.html', context)


def alter_flag(request, answer_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            reverse('users:login', args=()))
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


def answer_vote(request, answer_id, upvote=1):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            reverse('users:login', args=()))
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


def question_vote(request, question_id, upvote=1):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            reverse('users:login', args=()))
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
