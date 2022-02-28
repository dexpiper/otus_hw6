from django import forms


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
