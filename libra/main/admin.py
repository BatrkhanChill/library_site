from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Book_Info, School_Type, Specialization, BookReservationJournal, Reservation

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(School_Type)
class SchoolTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Book_Info)
class BookInfoAdmin(admin.ModelAdmin):
    list_filter = ['available', 'created', 'updated', 'category', 'school_type', 'specialization']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'author', 'isbn', 'target_group']
    list_display = ['title', 'author', 'price', 'available', 'school_type', 'specialization', 'target_group', 'pdf_file']
    fields = ['title', 'slug', 'author', 'description', 'isbn', 'publication_date', 'price', 'available', 'total_copies', 'available_copies', 'category', 'school_type', 'specialization', 'target_group', 'image', 'pdf_file']


@admin.register(BookReservationJournal)
class BookReservationJournalAdmin(admin.ModelAdmin):
    """
    Admin interface for book reservation journal
    Only admins can access and modify this
    """
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        # Only admins can add
        return request.user.is_staff
    
    def has_change_permission(self, request, obj=None):
        # Only admins can change
        return request.user.is_staff
    
    # Mark book as returned action
    def mark_as_returned(self, request, queryset):
        updated = queryset.filter(status='reserved').update(
            status='returned',
            returned_date=timezone.now()
        )
        self.message_user(request, f'{updated} книг(и) отмечены как возвращённые')
    mark_as_returned.short_description = "Отметить как возвращённую"
    
    actions = [mark_as_returned]
    
    # Display status with color coding
    def status_display(self, obj):
        if obj.status == 'reserved':
            color = 'orange'
            label = 'Зарезервирована'
        else:
            color = 'green'
            label = 'Возвращена'
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            label,
        )
    status_display.short_description = 'Статус'
    
    # Display expiration status
    def expiration_status(self, obj):
        if obj.status == 'returned':
            return format_html('<span style="color: green;">✓ Возвращена</span>')
        if obj.is_expired:
            return format_html('<span style="color: red; font-weight: bold;">⚠ Просрочена</span>')
        return format_html('<span style="color: blue;">Активна</span>')
    expiration_status.short_description = 'Статус срока'
    
    list_display = [
        'id',
        'student_name',
        'group_name',
        'book',
        'reservation_datetime',
        'expiration_date',
        'status_display',
        'expiration_status',
    ]
    
    list_filter = [
        'status',
        'reservation_datetime',
        'group_name',
        'book__category',
    ]
    
    search_fields = [
        'student_name',
        'group_name',
        'book__title',
        'notes',
    ]
    
    readonly_fields = [
        'created_by',
        'reservation_datetime',
        'returned_date',
        'is_expired',
        'status_display',
    ]
    
    fieldsets = (
        ('Информация о студенте', {
            'fields': ('student_name', 'group_name')
        }),
        ('Информация о бронировании', {
            'fields': (
                'book',
                'reservation_datetime',
                'expiration_date',
                'returned_date',
            )
        }),
        ('Статус', {
            'fields': ('status', 'status_display', 'is_expired')
        }),
        ('Дополнительное', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Non-superusers only see their own entries, superusers see all
        if not request.user.is_superuser:
            queryset = queryset.filter(created_by=request.user)
        return queryset
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on new entries
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'book', 'reservation_date', 'status']
    list_filter = ['status', 'reservation_date']
    search_fields = ['user__username', 'book__title']
    readonly_fields = ['reservation_date', 'user']