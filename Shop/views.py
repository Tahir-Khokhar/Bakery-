from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Product, Category, Order, OrderItem, Customer, InventoryLog
from .form import UserRegistrationForm, CustomerProfileForm, OrderForm, AddToCartForm, ProductFilterForm

from django.contrib.auth.models import User
from decimal import Decimal

# Home View
def home(request):
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:6]
    categories = Category.objects.all()
    new_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'new_products': new_products,
    }
    return render(request, 'bakery/home.html', context)  # Uses render() to return the HTML response


# Product Views
def product_list(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    
    # Filter form
    filter_form = ProductFilterForm(request.GET)
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        search = filter_form.cleaned_data.get('search')
        min_price = filter_form.cleaned_data.get('min_price')
        max_price = filter_form.cleaned_data.get('max_price')
        
        if category:
            products = products.filter(category=category)
        if search:
            products = products.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    
    context = {
        'products': products_page,
        'categories': categories,
        'filter_form': filter_form,
    }
    return render(request, 'bakery/product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    related_products = Product.objects.filter(
        category=product.category, is_available=True
    ).exclude(id=product.id)[:4]
    
    cart_form = AddToCartForm()
    
    context = {
        'product': product,
        'related_products': related_products,
        'cart_form': cart_form,
    }
    return render(request, 'bakery/product_detail.html', context)

# Category Views
def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category, is_available=True)
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'bakery/category_detail.html', context)

# Cart Views
@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')
    
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        subtotal = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })
        total += subtotal
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'bakery/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            cart = request.session.get('cart', {})
            cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
            request.session['cart'] = cart
            messages.success(request, 'Product added to cart successfully!')
    
    return redirect('product_detail', product_id=product_id)

@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, 'Product removed from cart!')
    return redirect('view_cart')

@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        cart = request.session.get('cart', {})
        if quantity > 0:
            cart[str(product_id)] = quantity
        else:
            del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, 'Cart updated!')
    return redirect('view_cart')

# Order Views
@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty!')
        return redirect('product_list')
    
    customer = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
    )[0]
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = customer
            order.save()
            
            total = Decimal('0.00')
            for product_id, quantity in cart.items():
                product = get_object_or_404(Product, id=product_id)
                if product.stock_quantity >= quantity:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                    total += product.price * quantity
                    
                    # Update stock
                    product.stock_quantity -= quantity
                    product.save()
                    
                    # Log inventory change
                    InventoryLog.objects.create(
                        product=product,
                        quantity_change=-quantity,
                        reason=f"Order #{order.id}",
                        created_by=request.user
                    )
                else:
                    messages.error(request, f'Not enough stock for {product.name}')
                    order.delete()
                    return redirect('view_cart')
            
            order.total_amount = total
            order.save()
            
            # Clear cart
            request.session['cart'] = {}
            
            messages.success(request, f'Order #{order.id} placed successfully!')
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm(initial={'delivery_address': customer.address})
    
    cart_items = []
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': product.price * quantity
        })
    
    total = sum(item['subtotal'] for item in cart_items)
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'total': total,
        'customer': customer,
    }
    return render(request, 'bakery/checkout.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.customer.user != request.user and not request.user.is_staff:
        messages.error(request, 'You are not authorized to view this order.')
        return redirect('home')
    
    context = {'order': order}
    return render(request, 'bakery/order_detail.html', context)

@login_required
def order_history(request):
    customer = Customer.objects.get(user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-order_date')
    
    context = {'orders': orders}
    return render(request, 'bakery/order_history.html', context)

# Authentication Views
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create customer profile
            Customer.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone='',
                address='',
                city='',
                postal_code=''
            )
            
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    context = {'form': form}
    return render(request, 'registration/register.html', context)

@login_required
def profile(request):
    customer = get_object_or_404(Customer, user=request.user)
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = CustomerProfileForm(instance=customer)
    
    context = {'form': form, 'customer': customer}
    return render(request, 'bakery/profile.html', context)
