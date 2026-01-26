from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    

    def __str__(self):
        return self.name

class Book_Info(models.Model):
    category = models.ForeignKey(Category, related_name='books',
                                on_delete=models.CASCADE)
    title = models.CharField(max_length=200, db_index=True)
    author = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    isbn = models.CharField(max_length=13, unique=True)
    publication_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='books/%Y/%m/%d', blank=True)

    class Meta:
        ordering = ['title']
        index_together = (('id', 'slug'),)
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
    

    def __str__(self):
        return self.title