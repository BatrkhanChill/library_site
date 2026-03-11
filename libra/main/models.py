from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

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

    class Meta:
        ordering = ['title']
        indexes = [models.Index(fields=['id', 'slug'])]
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
    

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
    
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