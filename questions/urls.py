from django.urls import path

from . import views

app_name = 'questions'
urlpatterns = [
    path('', views.index, name='index'),
    path('hot', views.index_hot, name='hot'),
    path('search', views.index_search, name='search'),
    path('<int:question_id>', views.question, name='question'),
    path('add', views.make_question, name='make_question'),
    path('save_question', views.save_question, name='save_question'),
    path('tag/<int:tag_id>', views.search_tag, name='searchtag'),
    path('alterflag/<int:answer_id>', views.alter_flag, name='alterflag'),
    path('answervote/<int:answer_id>/<int:upvote>', views.answer_vote,
         name='answervote'),
    path('questionvote/<int:question_id>/<int:upvote>', views.question_vote,
         name='questionvote')
]
