from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Category, Book_Info, BookLoan, Reservation, School_Type, Specialization, BookReservationJournal
from django.db.models import Q, F, Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LogoutView
from django.contrib import messages 
from django.utils import timezone
from django.core.paginator import Paginator
from .forms import UserEditForm, ProfileEditForm



# Create your views here.

def main_page(request):
    categories = Category.objects.all()[:6]
    new_books = Book_Info.objects.filter(available=True).order_by('-created')[:6]
    stats = {
        'books_count': Book_Info.objects.filter(available=True).count(),
        'pdf_count': Book_Info.objects.filter(available=True, pdf_file__isnull=False).count(),
        'authors_count': Book_Info.objects.filter(available=True).values('author').distinct().count(),
        'available_count': Book_Info.objects.filter(available=True, available_copies__gt=0).count(),
    }
    return render(request, 'main/main_page.html', {
        'categories': categories,
        'new_books': new_books,
        'stats': stats,
    })

@login_required(login_url='login')
def index(request, category_slug=None):
    categories = Category.objects.all()
    school_types = School_Type.objects.all()
    specializations = Specialization.objects.all()
    books = Book_Info.objects.filter(available=True)

    saved_books_ids = []
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile is not None:
            saved_books_ids = list(profile.saved_books.values_list('id', flat=True))

    category = None
    query = request.GET.get('q')
    sort_by = request.GET.get('sort', 'title')
    
    # Get filter parameters
    selected_school_types = request.GET.getlist('school_type')
    selected_specializations = request.GET.getlist('specialization')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        books = books.filter(category=category)
    
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(description__icontains=query) |
            Q(isbn__icontains=query)
        )
    
    # Apply filters
    if selected_school_types:
        books = books.filter(school_type__id__in=selected_school_types)
    
    if selected_specializations:
        books = books.filter(specialization__id__in=selected_specializations)
    
    # Sorting
    if sort_by == 'author':
        books = books.order_by('author', 'title')
    elif sort_by == 'year':
        books = books.order_by('-publication_date', 'title')
    else:
        books = books.order_by('title')
    
    return render(request, 'main/product/list.html', {
        'category': category,
        'categories': categories,
        'school_types': school_types,
        'specializations': specializations,
        'books': books,
        'query': query,
        'sort_by': sort_by,
        'selected_school_types': [int(x) for x in selected_school_types],
        'selected_specializations': [int(x) for x in selected_specializations],
        'saved_books_ids': saved_books_ids,
    })

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

    is_saved = False
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile is not None:
            is_saved = profile.saved_books.filter(id=book.id).exists()

    return render(request, 'main/book_detail.html', {
        'book': book,
        'is_reserved': is_reserved,
        'user_loans': user_loans,
        'similar_books': similar_books,
        'checked_out': checked_out,
        'is_saved': is_saved,
    })

@login_required(login_url='login')
def toggle_saved_book(request, book_id):
    book = get_object_or_404(Book_Info, id=book_id)
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(request, 'Профиль не найден.')
        return redirect('main:book_detail', book_id=book_id)

    if profile.saved_books.filter(id=book.id).exists():
        profile.saved_books.remove(book)
        messages.success(request, f'Книга "{book.title}" удалена из сохранённых.')
    else:
        profile.saved_books.add(book)
        messages.success(request, f'Книга "{book.title}" сохранена.')

    referrer = request.META.get('HTTP_REFERER')
    if referrer:
        return redirect(referrer)
    return redirect('main:book_detail', book_id=book_id)

@login_required
def profile(request):
    """Страница профиля пользователя"""
    user = request.user
    try:
        profile = user.profile
    except:
        # If profile doesn't exist, create it
        from .models import Profile
        profile = Profile.objects.create(user=user)
    
    # Получаем сохранённые книги
    saved_books = profile.saved_books.all()
    
    context = {
        'user': user,
        'profile': profile,
        'saved_books': saved_books,
    }
    
    return render(request, 'main/profile.html', context)  # ← БЕЗ ПАПКИ profile


@login_required
def profile_edit(request):
    """Редактирование профиля пользователя"""
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлён!')
            return redirect('main:profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user': user,
        'profile': profile,
    }
    
    return render(request, 'main/profile_edit.html', context)  # ← БЕЗ ПАПКИ profile


@login_required
def cancel_reservation(request, reservation_id):
    """Отмена бронирования книги"""
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    
    if reservation.status == 'pending':
        reservation.status = 'cancelled'
        # Вернуть копию в доступные
        if reservation.book.available_copies < reservation.book.total_copies:
            reservation.book.available_copies += 1
            reservation.book.save()
        reservation.save()
        messages.success(request, f'Бронирование книги "{reservation.book.title}" отменено.')
    else:
        messages.error(request, 'Невозможно отменить это бронирование.')
    
    return redirect('main:profile')


@login_required
def loan_history(request):
    """Полная история выдач пользователя"""
    loans = BookLoan.objects.filter(user=request.user).select_related('book').order_by('-loan_date')
    
    context = {
        'loans': loans,
        'total_loans': loans.count(),
    }
    
    return render(request, 'main/loan_history.html', context)  # ← БЕЗ ПАПКИ profile


@login_required
def reserve_book(request, book_id):
    """Бронирование книги"""
    book = get_object_or_404(Book_Info, id=book_id)

    if book.available_copies <= 0:
        messages.error(request, 'Книга временно недоступна')
        return redirect('main:book_detail', book_id=book_id)

    existing_reservation = Reservation.objects.filter(user=request.user, book=book).first()
    if existing_reservation is not None:
        if existing_reservation.status in ['pending', 'ready']:
            messages.warning(request, 'Вы уже забронировали эту книгу')
            return redirect('main:book_detail', book_id=book_id)

        # Если предыдущая бронь просрочена или отменена, обновляем её
        existing_reservation.status = 'pending'
        existing_reservation.reservation_date = timezone.now()
        existing_reservation.save()
        messages.success(request, f'Книга "{book.title}" снова забронирована!')
        return redirect('main:book_detail', book_id=book_id)

    try:
        if book.available_copies <= 0:
            messages.error(request, 'Книга временно недоступна')
            return redirect('main:book_detail', book_id=book_id)

        Reservation.objects.create(user=request.user, book=book)
        book.available_copies = max(book.available_copies - 1, 0)
        book.save()
        messages.success(request, f'Книга "{book.title}" забронирована!')
    except Exception as e:
        messages.error(request, 'Не удалось создать бронь. Попробуйте позже.')
        # Опционально: логировать e здесь

    return redirect('main:book_detail', book_id=book_id)


def register(request):
    """Registration page."""
    if request.user.is_authenticated:
        return redirect('main:index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Регистрация прошла успешно. Вы вошли в систему.')
            return redirect('main:index')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме регистрации.')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def logout_and_register(request):
    """Log out then redirect to registration to avoid 405 and show register page."""
    auth_logout(request)
    messages.info(request, 'Вы вышли из системы. Пожалуйста, зарегистрируйтесь или войдите снова.')
    return redirect('main:register')


def create_reservation(request):
    """Admin-only view to create new book reservations."""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет доступа к этой функции.')
        return redirect('main:index')
    
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        group_name = request.POST.get('group_name')
        teacher_name = request.POST.get('teacher_name', '')
        quantity = request.POST.get('quantity')
        book_id = request.POST.get('book')
        reservation_datetime_str = request.POST.get('reservation_datetime')
        expiration_date_str = request.POST.get('expiration_date')
        notes = request.POST.get('notes', '')
        
        try:
            book = Book_Info.objects.get(id=book_id)
            quantity = int(quantity)
            
            # Validate quantity against available copies
            if quantity <= 0:
                messages.error(request, 'Количество должно быть больше 0.')
                return redirect('main:reservation_journal')
            
            if quantity > book.available_copies:
                messages.error(request, f'Недостаточно доступных копий. Доступно: {book.available_copies}, запрошено: {quantity}.')
                return redirect('main:reservation_journal')
            
            # Reserve copies
            book.available_copies = max(book.available_copies - quantity, 0)
            book.save()
            
            # Parse datetime strings
            from datetime import datetime
            reservation_datetime = datetime.fromisoformat(reservation_datetime_str.replace('T', ' '))
            expiration_date = datetime.fromisoformat(expiration_date_str.replace('T', ' '))
            
            # Create the reservation
            BookReservationJournal.objects.create(
                book=book,
                student_name=student_name,
                group_name=group_name,
                teacher_name=teacher_name,
                quantity=quantity,
                reservation_datetime=reservation_datetime,
                expiration_date=expiration_date,
                notes=notes,
                created_by=request.user
            )
            
            messages.success(request, f'Бронь для "{student_name}" на книгу "{book.title}" ({quantity} шт.) создана успешно!')
            return redirect('main:reservation_journal')
            
        except Book_Info.DoesNotExist:
            messages.error(request, 'Выбранная книга не найдена.')
        except ValueError as e:
            messages.error(request, f'Ошибка в формате данных: {e}')
        except Exception as e:
            messages.error(request, f'Ошибка при создании брони: {e}')
    
    return redirect('main:reservation_journal')


def is_admin(user):
    """Check if user is staff/admin"""
    return user.is_staff


@user_passes_test(is_admin)
def reservation_journal(request):
    """Admin-only page for reservation journal with book availability"""
    # Get all reservations
    reservations = BookReservationJournal.objects.all().select_related('book', 'created_by').order_by('-reservation_datetime')

    # Auto-update late reserved records to expired
    now = timezone.now()
    for reservation in reservations.filter(status='reserved', expiration_date__lt=now):
        reservation.status = 'expired'
        reservation.save()

    # Refresh queryset after status updates
    reservations = BookReservationJournal.objects.all().select_related('book', 'created_by').order_by('-reservation_datetime')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    group_filter = request.GET.get('group', '')
    book_filter = request.GET.get('book', '')
    
    # Apply filters
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    if group_filter:
        reservations = reservations.filter(group_name__icontains=group_filter)
    if book_filter:
        reservations = reservations.filter(book__title__icontains=book_filter)
    
    # Pagination
    paginator = Paginator(reservations, 10)  # Show 10 reservations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all books with availability info
    books_with_availability = Book_Info.objects.all().values(
        'id', 'title', 'author', 'isbn', 'total_copies', 'available_copies'
    ).order_by('title')
    
    # Get unique groups
    groups = BookReservationJournal.objects.values_list('group_name', flat=True).distinct().order_by('group_name')
    
    # Statistics
    total_reservations = BookReservationJournal.objects.count()
    active_reservations = BookReservationJournal.objects.filter(status='reserved').count()
    returned_reservations = BookReservationJournal.objects.filter(status='returned').count()
    total_books = Book_Info.objects.count()
    total_available_copies = Book_Info.objects.aggregate(Sum('available_copies'))['available_copies__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        'reservations': page_obj,  # Keep for backward compatibility
        'books_with_availability': books_with_availability,
        'groups': groups,
        'status_filter': status_filter,
        'group_filter': group_filter,
        'book_filter': book_filter,
        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
        'returned_reservations': returned_reservations,
        'total_books': total_books,
        'total_available_copies': total_available_copies,
    }
    
    return render(request, 'main/admin_reservation_journal.html', context)


@user_passes_test(is_admin)
def return_book(request, reservation_id):
    """AJAX view to mark a book reservation as returned."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не разрешен.'})
    
    try:
        reservation = BookReservationJournal.objects.get(id=reservation_id)
        
        if reservation.status == 'returned':
            return JsonResponse({'success': False, 'error': 'Книга уже отмечена как возвращенная.'})
        
        # Mark as returned
        reservation.status = 'returned'
        reservation.returned_date = timezone.now()
        reservation.save()

        # Return reserved copies back to general availability
        if reservation.book.available_copies + reservation.quantity <= reservation.book.total_copies:
            reservation.book.available_copies += reservation.quantity
            reservation.book.save()
        
        # Format returned date for display
        returned_date = reservation.returned_date.strftime('%d.%m.%Y %H:%M')
        
        return JsonResponse({
            'success': True,
            'message': 'Книга отмечена как возвращенная.',
            'returned_date': returned_date
        })
        
    except BookReservationJournal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Бронирование не найдено.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Ошибка: {str(e)}'})