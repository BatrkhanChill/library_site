from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Book_Info, BookLoan, Reservation
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages 



# Create your views here.

def main_page(request, category_slug=None):
    return render(request, 'main/main_page.html')

def index(request, category_slug=None):
    categories = Category.objects.all()
    books = Book_Info.objects.filter(available=True)

    category = None

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        books = books.filter(category=category)
    return render(request, 'main/product/list.html', {'category': category,
                                               'categories': categories,
                                               'books': books})

def book_detail(request, book_id):
    book = get_object_or_404(Book_Info, id=book_id)
    is_reserved = False
    user_loans = []
    
    if request.user.is_authenticated:
        is_reserved = Reservation.objects.filter(
            user=request.user, 
            book=book, 
            status='pending'
        ).exists()
        user_loans = BookLoan.objects.filter(user=request.user, book=book, status='active')
    
    # Похожие книги (по категории и автору)
    similar_books = Book_Info.objects.filter(
        Q(category=book.category) | Q(author=book.author)
    ).exclude(id=book.id).distinct()[:3]
    
    checked_out = 0
    try:
        checked_out = book.total_copies - book.available_copies
    except Exception:
        checked_out = 0

    return render(request, 'main/book_detail.html', {
        'book': book,
        'is_reserved': is_reserved,
        'user_loans': user_loans,
        'similar_books': similar_books,
        'checked_out': checked_out,
    })

@login_required
def profile(request):
    active_loans = BookLoan.objects.filter(
        user=request.user, 
        status='active'
    ).select_related('book')
    
    overdue_loans = [loan for loan in active_loans if loan.is_overdue]
    reservations = Reservation.objects.filter(
        user=request.user, 
        status='pending'
    ).select_related('book')
    
    return render(request, 'main/profile.html', {
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'reservations': reservations,
    })

@login_required
def reserve_book(request, book_id):
    book = get_object_or_404(Book_Info, id=book_id)
    
    if book.available_copies > 0:
        # Проверяем, нет ли уже активной брони
        if not Reservation.objects.filter(user=request.user, book=book, status='pending').exists():
            Reservation.objects.create(user=request.user, book=book)
            messages.success(request, f'Книга "{book.title}" забронирована!')
        else:
            messages.warning(request, 'Вы уже забронировали эту книгу')
    else:
        messages.error(request, 'Книга временно недоступна')
    
    return redirect('book_detail', book_id=book_id)