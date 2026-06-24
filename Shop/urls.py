from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Categories
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    
    # Cart
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    
    # Orders
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_history, name='order_history'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
]
