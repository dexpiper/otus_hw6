from questions.models import Question


def get_trends(request):
    return {
        'trending': Question.trending()
    }
