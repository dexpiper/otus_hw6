from django.urls import path

from . import views

app_name = 'questions'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:question_id>/', views.question, name='question'),
    path('make_answer/<int:question_id>/', views.answer_question,
         name='answer')
]
