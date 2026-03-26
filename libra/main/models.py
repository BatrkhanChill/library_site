from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("main:book_list_by_category", args=[self.slug])


class School_Type(models.Model):
    """Тип школы/уровень образования"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = 'Тип школы'
        verbose_name_plural = 'Типы школ'
    
    def __str__(self):
        return self.name


class Specialization(models.Model):
    """Специализация книги"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
    
    def __str__(self):
        return self.name
    

class Book_Info(models.Model):
    category = models.ForeignKey(Category, related_name='books',
                                on_delete=models.CASCADE)
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    isbn = models.CharField(max_length=13, unique=True)
    publication_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    total_copies = models.PositiveIntegerField(default=1, verbose_name='Всего экземпляров')
    available_copies = models.PositiveIntegerField(default=1, verbose_name='Доступно экземпляров')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='books/%Y/%m/%d', blank=True)
    pdf_file = models.FileField(upload_to='books/pdf/%Y/%m/%d', blank=True, null=True, verbose_name='PDF файл')
    school_type = models.ForeignKey(School_Type, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', verbose_name='Тип школы')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', verbose_name='Специализация')
    target_group = models.CharField(max_length=100, blank=True, verbose_name='Целевая группа', help_text='Например: ОДН-201, Преподаватели')

    class Meta:
        ordering = ['title']
        indexes = [models.Index(fields=['id', 'slug'])]
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
    

    def __str__(self):
        return f"{self.title} - {self.author}"
    
    @property
    def is_available(self):
        return getattr(self, 'available_copies', 0) > 0

class BookLoan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('returned', 'Возвращена'),
        ('overdue', 'Просрочена'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    book = models.ForeignKey(Book_Info, on_delete=models.CASCADE, verbose_name="Книга")
    loan_date = models.DateField(default=timezone.now, verbose_name="Дата выдачи")
    due_date = models.DateField(verbose_name="Срок возврата")
    return_date = models.DateField(null=True, blank=True, verbose_name="Дата возврата")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = "Выдача книги"
        verbose_name_plural = "Выдачи книг"
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status == 'active'

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book_Info, on_delete=models.CASCADE)
    reservation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'В ожидании'),
        ('ready', 'Готов к выдаче'),
        ('cancelled', 'Отменена'),
    ], default='pending')
    
    class Meta:
        unique_together = ['user', 'book']

class BookReservationJournal(models.Model):
    """
    Журнал бронирования книг для администраторов
    """
    STATUS_CHOICES = [
        ('reserved', 'Зарезервирована'),
        ('returned', 'Возвращена'),
        ('expired', 'Просрочена'),
    ]
    
    book = models.ForeignKey(Book_Info, on_delete=models.CASCADE, verbose_name="Книга")
    student_name = models.CharField(max_length=150, verbose_name="Имя студента")
    group_name = models.CharField(max_length=100, verbose_name="Группа")
    teacher_name = models.CharField(max_length=150, blank=True, verbose_name="Имя преподавателя")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    reservation_datetime = models.DateTimeField(default=timezone.now, verbose_name="Дата и время бронирования")
    expiration_date = models.DateTimeField(verbose_name="Дата и время окончания")
    returned_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата возврата")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reserved', verbose_name="Статус")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_reservations', verbose_name="Создано")
    
    class Meta:
        verbose_name = "Бронь в журнале"
        verbose_name_plural = "Брони в журнале"
        ordering = ['-reservation_datetime']
    
    def __str__(self):
        return f"{self.student_name} - {self.book.title} ({self.quantity} шт.)"
    
    @property
    def is_expired(self):
        return self.expiration_date < timezone.now() and self.status == 'reserved'

class Profile(models.Model):
    """
    Модель профиля пользователя, расширяющая стандартную модель User
    """
    # Связь с пользователем (один к одному)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    
    # Дополнительные поля для профиля
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    student_id = models.CharField(max_length=50, blank=True, verbose_name="Студенческий билет №")
    group_name = models.CharField(max_length=50, blank=True, verbose_name="Группа")
    avatar = models.ImageField(upload_to='avatars/%Y/%m/%d', blank=True, null=True, verbose_name="Аватар")
    
    # Дополнительная информация
    bio = models.TextField(blank=True, verbose_name="О себе")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram")
    instagram = models.CharField(max_length=100, blank=True, verbose_name="Instagram")
    
    # Системные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    def __str__(self):
        return f"Профиль пользователя {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('main:profile')
    
    @property
    def full_name(self):
        """Возвращает полное имя пользователя"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.last_name} {self.user.first_name}"
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Сигнал: автоматически создаёт профиль при создании пользователя"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сигнал: автоматически сохраняет профиль при сохранении пользователя"""
    instance.profile.save()