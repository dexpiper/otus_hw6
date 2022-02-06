from django.urls import path

from . import views

app_name = 'questions'
urlpatterns = [
    path('', views.index, name='index'),
    path('hot', views.index_hot, name='hot'),
    path('<int:question_id>/', views.question, name='question'),
    path('make_answer/<int:question_id>/', views.answer_question,
         name='answer'),
    path('add', views.make_question, name='make_question'),
    path('save_question', views.save_question, name='save_question'),
    path('tag/<int:tag_id>', views.search_tag, name='searchtag'),
    path('alterflag/<int:answer_id>', views.alter_flag, name='alterflag')
]
