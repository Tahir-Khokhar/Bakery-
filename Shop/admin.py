from django.contrib import admin

# Register your models here.

admin.site.site_header = "Bakery Admin"
admin.site.site_title = "Bakery Project"
admin.site.index_title = "Welcome to Bakery"


from django.contrib import admin
from .models import Category, Product, Customer, Order, OrderItem, InventoryLog

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    # prepopulated_fields can only reference real model fields.
    # prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'is_available', 'is_featured']
    list_filter = ['category', 'is_available', 'is_featured']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock_quantity', 'is_available']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'order_date', 'status', 'total_amount', 'is_paid']
    list_filter = ['status', 'is_paid', 'order_date']
    search_fields = ['customer__first_name', 'customer__last_name', 'id']
    readonly_fields = ['total_amount', 'order_date']
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_delivered']

    def mark_as_paid(self, request, queryset):
        queryset.update(is_paid=True)
    mark_as_paid.short_description = "Mark selected orders as paid"

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = "Mark selected orders as delivered"

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ['city']

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_change', 'reason', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name']
