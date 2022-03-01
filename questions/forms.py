from django import forms

from .models import Question, Answer


class AnswerForm(forms.Form):
    content = forms.CharField(max_length=10000, required=True,
                              widget=forms.Textarea,
                              help_text='Try to be clear and polite')

    def __init__(self, *args, **kwargs):
        self.question_id = kwargs.pop('question_id', None)
        super(AnswerForm, self).__init__(*args, **kwargs)

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if Answer.objects.filter(question=self.question_id,
                                 content=content).count():
            raise forms.ValidationError(
                u'There is an answer with exactly the same text'
                u' for this question!'
            )


class QuestionForm(forms.Form):
    title = forms.CharField(max_length=60, required=True,
                            help_text='Nice title should be informative')
    content = forms.CharField(max_length=10000, required=True,
                              widget=forms.Textarea,
                              help_text='Short questions make good answers')
    tags = forms.CharField(max_length=60, required=False)

    def clean_tags(self):
        provided_tags = self.cleaned_data.get('tags')
        if not provided_tags:
            return ''
        tags = provided_tags.split()
        if len(tags) > 3:
            raise forms.ValidationError(
                'You can only provide up to 3 tags'
            )
        return tags

    def clean_title(self):
        provided_title = self.cleaned_data.get('title')
        if Question.objects.filter(title=provided_title).count():
            raise forms.ValidationError(
                u'A question with this title already exists'
            )
        return provided_title
