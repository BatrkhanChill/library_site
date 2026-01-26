from django.contrib import admin
from models import Category, Book_Info

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Book_Info)
class BookInfoAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'price', 'available', 'created', 'updated']
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'author', 'isbn']
    prepopulated_fields = {'slug': ('title',)}