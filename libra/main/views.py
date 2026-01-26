from django.shortcuts import render, get_object_or_404
from .models import Category, Book_Info

# Create your views here.
def index(request, category_slug=None):
    categories = Category.objects.all()
    books = Book_Info.objects.filter(available=True)

    category = None
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        books = books.filter(category=category)
    return render(request, 'main/index.html', {'category': category,
                                               'categories': categories,
                                               'books': books})