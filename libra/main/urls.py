from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('book/<int:book_id>/reserve/', views.reserve_book, name='reserve_book'),
    path('<int:id>/<slug:slug>/', views.book_detail, name='book_detail'),
    path('<slug:category_slug>/', views.index, name='book_list_by_category'),
]
