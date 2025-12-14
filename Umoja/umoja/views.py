from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import json
import csv
import requests
import hmac
import hashlib
from .models import UserProfile, Route, Bid, Payment, Review, FarmerProduct, Contract

# Home and Auth Views
def index(request):
    """Landing page"""
    return render(request, 'index.html')

def register_view(request):
    """User registration"""
    if request.method == 'POST':
        username = request.POST.get('email')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('userType')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        location = request.POST.get('location')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Email already registered')
            return redirect('register')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name
        )
        
        UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone,
            location=location
        )
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')
    
    return render(request, 'pages/auth/register.html')

def login_view(request):
    """User login"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            profile = user.profile
            
            if profile.user_type == 'broker':
                return redirect('broker_dashboard')
            elif profile.user_type == 'farmer':
                return redirect('farmer_dashboard')
            elif profile.user_type == 'admin':
                return redirect('admin:index')
            else:
                return redirect('index')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'pages/auth/login.html')

def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('index')

# Broker Views
@login_required
def broker_dashboard(request):
    """Broker dashboard with quick KPIs"""
    if request.user.profile.user_type != 'broker':
        return redirect('farmer_dashboard')
    
    today = timezone.now().date()
    
    # Quick KPIs
    active_bids = Bid.objects.filter(broker=request.user, status__in=['pending', 'accepted']).count()
    active_routes = Route.objects.filter(broker=request.user, status='active').count()
    pending_payments = Payment.objects.filter(
        bid__broker=request.user,
        status__in=['pending', 'paid']
    ).count()
    current_pickups = Bid.objects.filter(
        broker=request.user,
        status='accepted'
    ).count()
    
    # Today's routes
    today_routes = Route.objects.filter(
        broker=request.user,
        date=today
    ).order_by('time')[:5]
    
    # Recent bids
    recent_bids = Bid.objects.filter(broker=request.user).order_by('-created_at')[:5]
    
    context = {
        'active_bids': active_bids,
        'active_routes': active_routes,
        'pending_payments': pending_payments,
        'current_pickups': current_pickups,
        'today_routes': today_routes,
        'recent_bids': recent_bids,
    }
    
    return render(request, 'pages/broker/dashboard.html', context)

@login_required
def broker_routes(request):
    """Manage routes"""
    if request.user.profile.user_type != 'broker':
        return redirect('farmer_dashboard')
    
    routes = Route.objects.filter(broker=request.user).order_by('-created_at')
    
    # Apply filters if present
    status = request.GET.get('status')
    date = request.GET.get('date')
    search = request.GET.get('search')
    
    if status:
        routes = routes.filter(status=status)
    
    if date:
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            routes = routes.filter(date=date_obj)
        except ValueError:
            pass
    
    if search:
        routes = routes.filter(
            Q(name__icontains=search) |
            Q(origin__icontains=search) |
            Q(destination__icontains=search)
        )
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="routes.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Origin', 'Destination', 'Date', 'Time', 
                         'Capacity', 'Available', 'Price/kg', 'Status'])
        
        for route in routes:
            writer.writerow([
                route.id, route.name, route.origin, route.destination,
                route.date, route.time, route.capacity, route.available_capacity,
                route.price_per_kg, route.get_status_display()
            ])
        
        return response
    
    context = {'routes': routes}
    return render(request, 'pages/broker/routes.html', context)

@login_required
def create_route(request):
    """Create new route"""
    if request.user.profile.user_type != 'broker':
        return redirect('farmer_dashboard')
    
    if request.method == 'POST':
        try:
            route = Route.objects.create(
                broker=request.user,
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                origin=request.POST.get('origin'),
                destination=request.POST.get('destination'),
                date=request.POST.get('date'),
                time=request.POST.get('time'),
                capacity=int(request.POST.get('capacity', 0)),
                available_capacity=int(request.POST.get('capacity', 0)),
                price_per_kg=float(request.POST.get('price_per_kg', 0)),
                status='active'
            )
            
            messages.success(request, 'Route created successfully')
            return redirect('broker_routes')
        except Exception as e:
            messages.error(request, f'Error creating route: {str(e)}')
            return redirect('broker_routes')
    
    # If GET request, redirect to routes page
    return redirect('broker_routes')

@login_required
def edit_route(request, route_id):
    """Edit route"""
    route = get_object_or_404(Route, id=route_id, broker=request.user)
    
    if request.method == 'POST':
        try:
            route.name = request.POST.get('name', route.name)
            route.description = request.POST.get('description', route.description)
            route.origin = request.POST.get('origin', route.origin)
            route.destination = request.POST.get('destination', route.destination)
            route.date = request.POST.get('date', route.date)
            route.time = request.POST.get('time', route.time)
            
            # Handle capacity changes carefully
            new_capacity = int(request.POST.get('capacity', route.capacity))
            if new_capacity < route.capacity - route.available_capacity:
                messages.error(request, 'Cannot reduce capacity below booked amount')
                return redirect('edit_route', route_id=route_id)
            
            route.capacity = new_capacity
            route.price_per_kg = float(request.POST.get('price_per_kg', route.price_per_kg))
            route.status = request.POST.get('status', route.status)
            route.save()
            
            messages.success(request, 'Route updated successfully')
            return redirect('broker_routes')
        except Exception as e:
            messages.error(request, f'Error updating route: {str(e)}')
            return redirect('edit_route', route_id=route_id)
    
    return render(request, 'pages/broker/edit_route.html', {'route': route})

@login_required
def delete_route(request, route_id):
    """Delete route"""
    if request.method == 'POST':
        route = get_object_or_404(Route, id=route_id, broker=request.user)
        
        # Check if there are bookings
        if route.bookings.exists():
            messages.error(request, 'Cannot delete route with existing bookings')
            return redirect('broker_routes')
        
        route.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Route deleted successfully')
    
    return redirect('broker_routes')

@login_required
def route_details(request, route_id):
    """View route details"""
    route = get_object_or_404(Route, id=route_id)
    
    # Permission: brokers can only view their own route
    if request.user.profile.user_type == 'broker' and route.broker != request.user:
        messages.error(request, 'Unauthorized access')
        return redirect('broker_routes')
    
    # Build list of [lat, lng] coordinates for map
    coords = []
    # 1) If Route.stops is a list of dicts like [{'lat':..,'lng':..}, ...]
    try:
        if isinstance(route.stops, list) and route.stops:
            for s in route.stops:
                if isinstance(s, dict) and 'lat' in s and 'lng' in s:
                    coords.append([float(s['lat']), float(s['lng'])])
                elif isinstance(s, str) and ',' in s:
                    lat, lng = s.split(',', 1)
                    coords.append([float(lat.strip()), float(lng.strip())])
    except Exception:
        coords = []
    # 2) If no stops, try parsing origin/destination as "lat,lng"
    if not coords:
        def parse_pair(value):
            if not value:
                return None
            if isinstance(value, str) and ',' in value:
                parts = [p.strip() for p in value.split(',')]
                if len(parts) >= 2:
                    try:
                        return [float(parts[0]), float(parts[1])]
                    except ValueError:
                        return None
            return None
        o = parse_pair(route.origin)
        d = parse_pair(route.destination)
        if o:
            coords.append(o)
        if d:
            coords.append(d)
    # 3) Fallback: if still empty, try to extract numeric pairs anywhere in stops/raw text
    if not coords and route.stops:
        try:
            # route.stops might be a JSON string of coordinates
            import re
            text = str(route.stops)
            matches = re.findall(r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)', text)
            for m in matches:
                coords.append([float(m[0]), float(m[1])])
        except Exception:
            pass

    # Get bids associated with this route
    bids = route.bids.all().order_by('-created_at')
    
    context = {
        'route': route,
        'bids': bids,
        'route_coords': coords,  # list of [lat, lng]
    }
    
    return render(request, 'pages/broker/route_details.html', context)

@login_required
def broker_marketplace(request):
    """Browse farmer produce listings - shows farmers with their listings"""
    if request.user.profile.user_type != 'broker':
        return redirect('farmer_dashboard')
    
    listings = FarmerProduct.objects.filter(status='active').select_related('farmer', 'farmer__profile').order_by('-created_at')
    
    # Apply filters
    produce_type = request.GET.get('produce_type')
    location = request.GET.get('location')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    available_from = request.GET.get('available_from')
    search = request.GET.get('search')
    
    if produce_type:
        listings = listings.filter(produce_type=produce_type)
    
    if location:
        listings = listings.filter(origin_text__icontains=location)
    
    if price_min:
        listings = listings.filter(price_expected__gte=price_min)
    
    if price_max:
        listings = listings.filter(price_expected__lte=price_max)
    
    if available_from:
        listings = listings.filter(available_from__gte=available_from)
    
    if search:
        listings = listings.filter(
            Q(produce_type__icontains=search) |
            Q(origin_text__icontains=search) |
            Q(notes__icontains=search) |
            Q(farmer__first_name__icontains=search) |
            Q(farmer__last_name__icontains=search) |
            Q(farmer__username__icontains=search)
        )
    
    # Get unique farmers from listings
    farmers = UserProfile.objects.filter(
        user_type='farmer',
        user__farmer_products__status='active'
    ).distinct().select_related('user')
    
    # Get active farmers count
    active_farmers_count = farmers.count()
    
    # Get total quantity available
    total_quantity = listings.aggregate(Sum('quantity_available'))['quantity_available__sum'] or 0
    
    # Get average price
    avg_price = listings.filter(price_expected__isnull=False).aggregate(Avg('price_expected'))['price_expected__avg'] or 0
    
    context = {
        'listings': listings,
        'farmers': farmers,
        'active_farmers_count': active_farmers_count,
        'total_quantity': total_quantity,
        'avg_price': avg_price,
        'produce_types': FarmerProduct.PRODUCE_TYPES,
        'user': request.user,
        'request': request,  # Pass the entire request object to the template
    }
    
    return render(request, 'pages/broker/marketplace.html', context)

@login_required
def listing_detail(request, listing_id):
    """View listing details and place bid"""
    listing = get_object_or_404(FarmerProduct, id=listing_id, status='active')
    
    # Get bids for this listing (only visible to listing owner)
    bids = []
    if request.user.is_authenticated and request.user == listing.farmer:
        bids = Bid.objects.filter(listing=listing).order_by('-created_at')
    
    # Get broker's routes for route selection
    broker_routes = []
    if request.user.is_authenticated and request.user.profile.user_type == 'broker':
        broker_routes = Route.objects.filter(broker=request.user, status='active')
    
    context = {
        'listing': listing,
        'bids': bids,
        'broker_routes': broker_routes,
    }
    
    return render(request, 'pages/broker/listing_detail.html', context)

@login_required
def place_bid(request, listing_id):
    """Place a bid on a listing"""
    if request.user.profile.user_type != 'broker':
        messages.error(request, 'Only brokers can place bids')
        return redirect('broker_marketplace')
    
    listing = get_object_or_404(FarmerProduct, id=listing_id, status='active')
    
    if request.method == 'POST':
        try:
            quantity_requested = float(request.POST.get('quantity_requested', 0))
            price_per_unit = float(request.POST.get('price_per_unit', 0))
            route_id = request.POST.get('route')
            notes = request.POST.get('notes', '')
            
            # Validate quantity
            if quantity_requested <= 0:
                messages.error(request, 'Quantity must be greater than 0')
                return redirect('listing_detail', listing_id=listing_id)
            
            if quantity_requested > listing.quantity_available:
                messages.error(request, f'Only {listing.quantity_available} {listing.get_unit_display()} available')
                return redirect('listing_detail', listing_id=listing_id)
            
            # Validate price
            if price_per_unit <= 0:
                messages.error(request, 'Price must be greater than 0')
                return redirect('listing_detail', listing_id=listing_id)
                
            if listing.price_expected and price_per_unit < listing.price_expected:
                messages.error(request, f'Bid price must be at least KES {listing.price_expected:.2f}')
                return redirect('listing_detail', listing_id=listing_id)
            
            # Calculate total price
            total_price = quantity_requested * price_per_unit
            
            # Create bid
            bid = Bid.objects.create(
                broker=request.user,
                listing=listing,
                quantity_requested=quantity_requested,
                price_per_unit=price_per_unit,
                total_price=total_price,
                notes=notes,
                status='pending'
            )
            
            # Link route if provided
            if route_id:
                try:
                    route = Route.objects.get(id=route_id, broker=request.user)
                    bid.route = route
                    bid.save()
                except Route.DoesNotExist:
                    pass
            
            messages.success(request, 'Bid placed successfully! The farmer will be notified.')
            return redirect('broker_bids')
            
        except Exception as e:
            messages.error(request, f'Error placing bid: {str(e)}')
            return redirect('listing_detail', listing_id=listing_id)
    
    return redirect('listing_detail', listing_id=listing_id)

@login_required
def broker_bids(request):
    """View and manage broker's bids"""
    if request.user.profile.user_type != 'broker':
        return redirect('farmer_dashboard')
    
    bids = Bid.objects.filter(broker=request.user).select_related('listing', 'listing__farmer', 'listing__farmer__profile', 'route').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        bids = bids.filter(status=status_filter)
    
    # Calculate stats
    all_bids = Bid.objects.filter(broker=request.user)
    pending_count = all_bids.filter(status='pending').count()
    accepted_count = all_bids.filter(status='accepted').count()
    rejected_count = all_bids.filter(status='rejected').count()
    completed_count = all_bids.filter(status='completed').count()
    
    context = {
        'bids': bids,
        'status_choices': Bid.STATUS_CHOICES,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'completed_count': completed_count,
    }
    
    return render(request, 'pages/broker/bids.html', context)

@login_required
def broker_bid_detail(request, bid_id):
    """View detailed information about a specific bid"""
    if request.user.profile.user_type != 'broker':
        return redirect('farmer_dashboard')
    
    bid = get_object_or_404(Bid, id=bid_id, broker=request.user)
    
    context = {
        'bid': bid,
    }
    
    return render(request, 'pages/broker/bid_detail.html', context)

@login_required
def cancel_bid(request, bid_id):
    """Cancel a pending bid"""
    if request.method == 'POST':
        bid = get_object_or_404(Bid, id=bid_id, broker=request.user)
        
        if bid.status != 'pending':
            messages.error(request, 'Only pending bids can be cancelled')
            return redirect('broker_bids')
        
        bid.status = 'cancelled'
        bid.save()
        
        messages.success(request, 'Bid cancelled successfully')
    
    return redirect('broker_bids')

# Analytics removed - dashboard shows quick KPIs instead

# Farmer Views
@login_required
def farmer_dashboard(request):
    """Farmer dashboard"""
    if request.user.profile.user_type != 'farmer':
        return redirect('broker_dashboard')
    
    # Statistics
    active_listings = FarmerProduct.objects.filter(farmer=request.user, status='active').count()
    
    # Get all bids for farmer's listings
    farmer_listings = FarmerProduct.objects.filter(farmer=request.user)
    incoming_bids = Bid.objects.filter(
        listing__in=farmer_listings,
        status='pending'
    ).count()
    
    accepted_bids = Bid.objects.filter(
        listing__in=farmer_listings,
        status='accepted'
    ).count()
    
    # Total revenue from completed payments
    total_revenue = Payment.objects.filter(
        bid__listing__in=farmer_listings,
        status='released'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Recent bids
    recent_bids = Bid.objects.filter(
        listing__in=farmer_listings
    ).select_related('broker', 'listing').order_by('-created_at')[:5]
    
    # Get nearby brokers
    farmer_location = request.user.profile.location
    brokers = UserProfile.objects.filter(user_type='broker').select_related('user')
    
    # Filter by location if farmer has location set
    if farmer_location:
        brokers = brokers.filter(location__icontains=farmer_location.split(',')[0])
    
    # Get brokers with active routes
    brokers_with_routes = []
    for broker in brokers[:6]:  # Limit to 6 brokers
        active_routes = Route.objects.filter(broker=broker.user, status='active').count()
        if active_routes > 0:
            brokers_with_routes.append({
                'broker': broker,
                'active_routes': active_routes,
            })
    
    context = {
        'active_listings': active_listings,
        'incoming_bids': incoming_bids,
        'accepted_bids': accepted_bids,
        'total_revenue': total_revenue,
        'recent_bids': recent_bids,
        'nearby_brokers': brokers_with_routes,
    }
    
    return render(request, 'pages/farmer/dashboard.html', context)

@login_required
def farmer_products(request):
    """Manage farmer produce listings"""
    if request.user.profile.user_type != 'farmer':
        return redirect('broker_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Handle delete
        if action == 'delete':
            product_id = request.POST.get('product_id')
            try:
                product = get_object_or_404(FarmerProduct, id=product_id, farmer=request.user)
                product.delete()
                messages.success(request, 'Product deleted successfully!')
                return redirect('farmer_products')
            except Exception as e:
                messages.error(request, f'Error deleting product: {str(e)}')
                return redirect('farmer_products')
        
        # Handle edit
        elif action == 'edit':
            product_id = request.POST.get('product_id')
            try:
                product = get_object_or_404(FarmerProduct, id=product_id, farmer=request.user)
                
                # Validate required fields
                quantity_available = request.POST.get('quantity_available')
                if not quantity_available or float(quantity_available) <= 0:
                    raise ValueError('Quantity must be greater than 0')
                
                price_expected = request.POST.get('price_expected')
                if not price_expected or float(price_expected) <= 0:
                    raise ValueError('Price must be greater than 0')
                
                origin_text = request.POST.get('origin_text', '').strip()
                if not origin_text:
                    raise ValueError('Location/Origin is required')
                
                # Update product
                product.produce_type = request.POST.get('produce_type')
                product.quantity_available = float(quantity_available)
                product.unit = request.POST.get('unit', 'kg')
                product.quality = request.POST.get('quality', 'standard')
                product.price_expected = float(price_expected)
                product.origin_text = origin_text
                product.origin_lat = float(request.POST.get('origin_lat')) if request.POST.get('origin_lat') else None
                product.origin_lng = float(request.POST.get('origin_lng')) if request.POST.get('origin_lng') else None
                product.available_from = request.POST.get('available_from')
                product.notes = request.POST.get('notes', '').strip()
                
                # Handle image upload
                if request.FILES.get('image'):
                    product.image = request.FILES['image']
                
                product.save()
                messages.success(request, 'Product updated successfully!')
                return redirect('farmer_products')
            except Exception as e:
                messages.error(request, f'Error updating product: {str(e)}')
                return redirect('farmer_products')
        
        # Handle listing creation
        else:
            try:
                # Validate required fields
                quantity_available = request.POST.get('quantity_available')
                if not quantity_available or float(quantity_available) <= 0:
                    raise ValueError('Quantity must be greater than 0')
                
                price_expected = request.POST.get('price_expected')
                if not price_expected or float(price_expected) <= 0:
                    raise ValueError('Price must be greater than 0')
                
                origin_text = request.POST.get('origin_text', '').strip()
                if not origin_text:
                    raise ValueError('Location/Origin is required')
                
                listing = FarmerProduct.objects.create(
                    farmer=request.user,
                    produce_type=request.POST.get('produce_type'),
                    quantity_available=float(quantity_available),
                    unit=request.POST.get('unit', 'kg'),
                    quality=request.POST.get('quality', 'standard'),
                    price_expected=float(price_expected),
                    origin_text=origin_text,
                    origin_lat=float(request.POST.get('origin_lat')) if request.POST.get('origin_lat') else None,
                    origin_lng=float(request.POST.get('origin_lng')) if request.POST.get('origin_lng') else None,
                    available_from=request.POST.get('available_from'),
                    notes=request.POST.get('notes', '').strip(),
                    status='active'
                )
                
                # Handle image upload
                if request.FILES.get('image'):
                    listing.image = request.FILES['image']
                    listing.save()
                
                messages.success(request, 'Listing created successfully!')
                return redirect('farmer_products')
            except Exception as e:
                messages.error(request, f'Error creating listing: {str(e)}')
    
    # Get farmer's listings
    listings = FarmerProduct.objects.filter(farmer=request.user).order_by('-created_at')
    
    # Statistics
    total_listings = listings.count()
    active_listings = listings.filter(status='active').count()
    pending_bids = Bid.objects.filter(
        listing__in=listings,
        status='pending'
    ).count()
    
    # Total revenue from released payments
    total_revenue = Payment.objects.filter(
        bid__listing__in=listings,
        status='released'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'listings': listings,
        'products': listings,  # Also provide as 'products' for template compatibility
        'total_listings': total_listings,
        'total_products': total_listings,  # For template compatibility
        'active_listings': active_listings,
        'active_products': active_listings,  # For template compatibility
        'pending_bids': pending_bids,
        'pending_orders': pending_bids,  # For template compatibility
        'total_revenue': total_revenue,
        'produce_types': FarmerProduct.PRODUCE_TYPES,
        'quality_choices': FarmerProduct.QUALITY_CHOICES,
        'unit_choices': FarmerProduct.UNIT_CHOICES,
    }
    
    return render(request, 'pages/farmer/products.html', context)

@login_required
def farmer_product_detail(request, product_id):
    """View detailed information about a farmer product"""
    if request.user.profile.user_type != 'farmer':
        return redirect('broker_dashboard')
    
    product = get_object_or_404(FarmerProduct, id=product_id, farmer=request.user)
    
    # Get bids for this product
    bids = Bid.objects.filter(listing=product).select_related('broker').order_by('-created_at')
    
    context = {
        'product': product,
        'bids': bids,
        'produce_types': FarmerProduct.PRODUCE_TYPES,
        'quality_choices': FarmerProduct.QUALITY_CHOICES,
        'unit_choices': FarmerProduct.UNIT_CHOICES,
    }
    
    return render(request, 'pages/farmer/product_detail.html', context)

@login_required
def delete_farmer_product(request, product_id):
    """Delete a farmer product"""
    if request.user.profile.user_type != 'farmer':
        return redirect('broker_dashboard')
    
    if request.method == 'POST':
        product = get_object_or_404(FarmerProduct, id=product_id, farmer=request.user)
        
        # Check if there are active bids
        active_bids = Bid.objects.filter(listing=product, status__in=['pending', 'accepted']).exists()
        if active_bids:
            messages.error(request, 'Cannot delete product with active bids. Please cancel or complete the bids first.')
            return redirect('farmer_products')
        
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('farmer_products')
    
    return redirect('farmer_products')

@login_required
def farmer_bids(request):
    """View incoming bids for farmer's listings (bid inbox)"""
    if request.user.profile.user_type != 'farmer':
        return redirect('broker_dashboard')
    
    # Get all listings owned by farmer
    farmer_listings = FarmerProduct.objects.filter(farmer=request.user)
    
    # Get all bids for these listings
    bids = Bid.objects.filter(
        listing__in=farmer_listings
    ).select_related('broker', 'listing', 'route').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        bids = bids.filter(status=status_filter)
    
    # Group bids by listing
    bids_by_listing = {}
    for bid in bids:
        listing_id = bid.listing.id
        if listing_id not in bids_by_listing:
            bids_by_listing[listing_id] = {
                'listing': bid.listing,
                'bids': []
            }
        bids_by_listing[listing_id]['bids'].append(bid)
    
    context = {
        'bids': bids,
        'bids_by_listing': bids_by_listing,
        'status_choices': Bid.STATUS_CHOICES,
    }
    
    return render(request, 'pages/farmer/bids.html', context)

@login_required
def accept_bid(request, bid_id):
    """Accept a bid"""
    if request.method == 'POST':
        bid = get_object_or_404(Bid, id=bid_id)
        
        # Check permission - only listing owner can accept
        if bid.listing.farmer != request.user:
            messages.error(request, 'Unauthorized')
            return redirect('farmer_bids')
        
        if bid.status != 'pending':
            messages.error(request, 'Only pending bids can be accepted')
            return redirect('farmer_bids')
        
        # Check if quantity is still available
        if bid.quantity_requested > bid.listing.quantity_available:
            messages.error(request, 'Insufficient quantity available')
            return redirect('farmer_bids')
        
        # Accept the bid
        bid.status = 'accepted'
        bid.save()
        
        # Reduce the product quantity by the accepted bid amount
        listing = bid.listing
        listing.quantity_available = listing.quantity_available - bid.quantity_requested
        
        # If quantity reaches zero or below, mark as sold
        if listing.quantity_available <= 0:
            listing.status = 'sold'
            listing.quantity_available = 0
        
        listing.save()
        
        # Optionally create a contract
        Contract.objects.get_or_create(bid=bid)
        
        # Reject other pending bids for the same listing if quantity would be exceeded
        other_bids = Bid.objects.filter(
            listing=bid.listing,
            status='pending'
        ).exclude(id=bid.id)
        
        for other_bid in other_bids:
            # Check if accepting this would exceed available quantity
            if other_bid.quantity_requested > listing.quantity_available:
                other_bid.status = 'rejected'
                other_bid.save()
        
        messages.success(request, f'Bid accepted successfully! Quantity reduced by {bid.quantity_requested} {listing.get_unit_display()}.')
        return redirect('farmer_bids')
    
    return redirect('farmer_bids')

@login_required
def reject_bid(request, bid_id):
    """Reject a bid"""
    if request.method == 'POST':
        bid = get_object_or_404(Bid, id=bid_id)
        
        # Check permission
        if bid.listing.farmer != request.user:
            messages.error(request, 'Unauthorized')
            return redirect('farmer_bids')
        
        if bid.status != 'pending':
            messages.error(request, 'Only pending bids can be rejected')
            return redirect('farmer_bids')
        
        bid.status = 'rejected'
        bid.save()
        
        messages.success(request, 'Bid rejected')
        return redirect('farmer_bids')
    
    return redirect('farmer_bids')

@login_required
def listing_bids(request, listing_id):
    """View all bids for a specific listing"""
    listing = get_object_or_404(FarmerProduct, id=listing_id)
    
    # Check permission - only listing owner can view bids
    if listing.farmer != request.user:
        messages.error(request, 'Unauthorized')
        return redirect('farmer_products')
    
    bids = Bid.objects.filter(listing=listing).select_related('broker', 'route').order_by('-created_at')
    
    context = {
        'listing': listing,
        'bids': bids,
    }
    
    return render(request, 'pages/farmer/listing_bids.html', context)

@login_required
def farmer_profile(request):
    """Farmer profile page"""
    if request.user.profile.user_type != 'farmer':
        return redirect('broker_dashboard')
    
    # Calculate statistics
    total_listings = FarmerProduct.objects.filter(farmer=request.user).count()
    completed_bids = Bid.objects.filter(
        listing__farmer=request.user,
        status='completed'
    ).count()
    
    total_bids = Bid.objects.filter(listing__farmer=request.user).count()
    success_rate = int((completed_bids / total_bids * 100)) if total_bids > 0 else 0
    
    # Calculate average rating
    reviews = Review.objects.filter(bid__listing__farmer=request.user)
    rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 4.5
    
    # Payment history
    payments = Payment.objects.filter(
        bid__listing__farmer=request.user
    ).select_related('bid').order_by('-timestamp')[:10]
    
    context = {
        'total_listings': total_listings,
        'completed_bids': completed_bids,
        'success_rate': success_rate,
        'rating': rating,
        'payments': payments,
    }
    
    return render(request, 'pages/farmer/profile.html', context)

@login_required
def update_profile(request):
    """Update user profile information"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        user = request.user
        profile = user.profile
        
        try:
            if form_type == 'personal':
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.email = request.POST.get('email', '')
                profile.phone = request.POST.get('phone', '')
                profile.id_number = request.POST.get('id_number', '')
                user.save()
                profile.save()
                messages.success(request, 'Personal information updated successfully')
                
            elif form_type == 'farm':
                profile.farm_name = request.POST.get('farm_name', '')
                farm_size = request.POST.get('farm_size', 0)
                profile.farm_size = float(farm_size) if farm_size else 0
                profile.location = request.POST.get('location', '')
                profile.gps_coordinates = request.POST.get('gps_coordinates', '')
                profile.save()
                messages.success(request, 'Farm information updated successfully')
                
            elif form_type == 'payment':
                profile.bank_name = request.POST.get('bank_name', '')
                profile.account_number = request.POST.get('account_number', '')
                profile.mpesa_number = request.POST.get('mpesa_number', '')
                profile.payment_preference = request.POST.get('payment_preference', 'mpesa')
                profile.save()
                messages.success(request, 'Payment information updated successfully')
            
            elif form_type == 'broker_phone':
                # For brokers: update phone number for M-Pesa payments
                profile.phone = request.POST.get('phone', '')
                profile.mpesa_number = request.POST.get('mpesa_number', '')
                profile.save()
                messages.success(request, 'Phone number updated successfully. You will receive M-Pesa payment prompts on this number.')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        
        # Redirect based on user type
        if request.user.profile.user_type == 'broker':
            return redirect('broker_dashboard')
        return redirect('farmer_profile')
    
    # Redirect based on user type
    if request.user.profile.user_type == 'broker':
        return redirect('broker_dashboard')
    return redirect('farmer_profile')

@login_required
def nearby_brokers(request):
    """View nearby brokers for farmers"""
    if request.user.profile.user_type != 'farmer':
        return redirect('broker_dashboard')
    
    # Get farmer's location
    farmer_location = request.user.profile.location
    
    # Get all brokers
    brokers = UserProfile.objects.filter(
        user_type='broker'
    ).select_related('user')
    
    # Filter by location if farmer has location set
    if farmer_location:
        brokers = brokers.filter(location__icontains=farmer_location.split(',')[0])
    
    # Get brokers with active routes
    brokers_with_routes = []
    for broker in brokers:
        active_routes = Route.objects.filter(broker=broker.user, status='active').count()
        if active_routes > 0:
            brokers_with_routes.append({
                'broker': broker,
                'active_routes': active_routes,
            })
    
    context = {
        'brokers': brokers_with_routes,
        'farmer_location': farmer_location,
    }
    
    return render(request, 'pages/farmer/nearby_brokers.html', context)

@login_required
def update_profile_picture(request):
    """Update profile picture"""
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        try:
            profile = request.user.profile
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            messages.success(request, 'Profile picture updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating profile picture: {str(e)}')
    else:
        messages.error(request, 'No image file provided')
    
    return redirect('farmer_profile')

@login_required
def update_notifications(request):
    """Update notification preferences"""
    if request.method == 'POST':
        try:
            profile = request.user.profile
            profile.email_notifications = 'email_notifications' in request.POST
            profile.sms_notifications = 'sms_notifications' in request.POST
            profile.save()
            messages.success(request, 'Notification preferences updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating preferences: {str(e)}')
    
    return redirect('farmer_profile')

@login_required
def password_change(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully')
            
            # Redirect based on user type
            if request.user.profile.user_type == 'farmer':
                return redirect('farmer_profile')
            else:
                return redirect('broker_dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'pages/auth/password_change.html', {'form': form})

# API Views
@login_required
def mark_collected(request, bid_id):
    """Mark bid as collected (broker confirms pickup)"""
    if request.method == 'POST':
        bid = get_object_or_404(Bid, id=bid_id)
        
        # Check permission - only broker can mark as collected
        if bid.broker != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        if bid.status != 'accepted':
            return JsonResponse({'error': 'Only accepted bids can be marked as collected'}, status=400)
        
        bid.status = 'collected'
        bid.save()
        
        # Release payment if exists
        payment = Payment.objects.filter(bid=bid, status='paid').first()
        if payment:
            payment.status = 'released'
            payment.save()
        
        return JsonResponse({'success': True, 'status': 'collected'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def mark_completed(request, bid_id):
    """Mark bid as completed"""
    if request.method == 'POST':
        bid = get_object_or_404(Bid, id=bid_id)
        
        # Check permission
        if bid.broker != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        if bid.status != 'collected':
            return JsonResponse({'error': 'Bid must be collected first'}, status=400)
        
        bid.status = 'completed'
        bid.save()
        
        return JsonResponse({'success': True, 'status': 'completed'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def initiate_payhero_payment(bid, callback_url, phone_number=None):
    """
    Initiate STK push payment with Payhero API v2.
    Based on Payhero API v2 documentation.
    """
    try:
        # Use provided phone number or fallback to profile
        phone = phone_number or bid.broker.profile.mpesa_number or bid.broker.profile.phone or ''
        
        if not phone:
            return {
                'success': False,
                'error': 'Phone number is required for M-Pesa payment'
            }
        
        # Format phone number (ensure it starts with 254 for Kenya)
        phone = str(phone).strip()
        # Remove any spaces, dashes, or plus signs
        phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        # If it starts with 0, replace with 254
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        # If it doesn't start with 254, add it
        elif not phone.startswith('254'):
            phone = '254' + phone
        
        print(f"Formatted phone number for Payhero: {phone}")
        
        # Generate unique reference
        payhero_ref = f"BID_{bid.id}_{int(timezone.now().timestamp())}"
        
        # Payhero API v2 headers
        headers = {
            'Authorization': settings.PAYHERO_BASIC_AUTH_TOKEN,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Payhero API v2 payment data
        payment_data = {
            'amount': int(float(bid.total_price)),  # Payhero expects integer amount
            'phone_number': phone,
            'channel_id': int(getattr(settings, 'PAYHERO_CHANNEL_ID', 3905)),
            'provider': 'm-pesa',
            'external_reference': payhero_ref,
            'customer_name': bid.broker.get_full_name() or bid.broker.username,
            'callback_url': callback_url
        }
        
        # Debug: Log the payment data being sent
        print(f"Payhero Payment Data: {payment_data}")
        print(f"Using Channel ID: {getattr(settings, 'PAYHERO_CHANNEL_ID', 3905)}")
        print(f"API URL: {settings.PAYHERO_BASE_URL}/api/v2/payments")
        
        # Make API call to Payhero v2 payments endpoint
        try:
            api_url = f'{settings.PAYHERO_BASE_URL}/api/v2/payments'
            print(f"Making API call to: {api_url}")
            print(f"Request headers: {headers}")
            print(f"Request data: {payment_data}")
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payment_data,
                timeout=30
            )
            
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text[:500]}")
            
            # If channel ID not found, try common channel IDs
            if response.status_code == 404 and "no rows in result set" in response.text.lower():
                print(f"Channel ID {getattr(settings, 'PAYHERO_CHANNEL_ID', 3905)} not found, trying common channel IDs...")
                
                common_channel_ids = [133, 911, 1, 2, 3, 100, 200, 300, 500, 1000]
                successful_channel = None
                
                for channel_id in common_channel_ids:
                    payment_data['channel_id'] = channel_id
                    print(f"Trying channel ID: {channel_id}")
                    
                    try:
                        test_response = requests.post(
                            f'{settings.PAYHERO_BASE_URL}/api/v2/payments',
                            headers=headers,
                            json=payment_data,
                            timeout=10
                        )
                        
                        if test_response.status_code == 201:
                            successful_channel = channel_id
                            response = test_response
                            print(f"Success with channel ID: {channel_id}")
                            break
                            
                    except requests.exceptions.RequestException:
                        continue
                
                if not successful_channel:
                    return {
                        'success': False,
                        'error': f'No working channel ID found. Please check your Payhero dashboard for the correct channel ID. Tried: {common_channel_ids}'
                    }
            
            if response.status_code == 201:  # Payhero returns 201 for successful creation
                try:
                    response_data = response.json()
                    print(f"Full Payhero API Response: {json.dumps(response_data, indent=2)}")
                    
                    # Check multiple possible success indicators
                    checkout_request_id = response_data.get('CheckoutRequestID') or response_data.get('checkout_request_id') or response_data.get('CheckoutRequestID')
                    is_success = (
                        response_data.get('success') == True or 
                        response_data.get('success') == 'true' or
                        checkout_request_id or 
                        response_data.get('status') == 'pending' or
                        response_data.get('status') == 'success' or
                        (response_data.get('message', '').lower().find('success') != -1) or
                        (response_data.get('message', '').lower().find('initiated') != -1)
                    )
                    
                    if is_success:
                        checkout_request_id = checkout_request_id or payhero_ref
                        return {
                            'success': True,
                            'transaction_id': checkout_request_id,
                            'reference': payhero_ref,
                            'checkout_request_id': checkout_request_id,
                            'message': response_data.get('message', 'STK Push initiated successfully'),
                            'full_response': response_data  # Include for debugging
                        }
                    else:
                        error_msg = response_data.get('message') or response_data.get('error') or 'Failed to initiate STK Push'
                        print(f"Payhero API returned success status but no valid indicators. Response: {response_data}")
                        return {
                            'success': False,
                            'error': error_msg,
                            'response_data': response_data  # Include for debugging
                        }
                except json.JSONDecodeError:
                    print(f"Invalid JSON response from Payhero: {response.text}")
                    return {
                        'success': False,
                        'error': f'Invalid response from Payhero API: {response.text[:200]}'
                    }
            else:
                # Log the full error response for debugging
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message') or error_data.get('error') or response.text or f'Payhero API error: {response.status_code}'
                    print(f"Payhero API Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    error_msg = response.text or f'Payhero API error: {response.status_code}'
                    print(f"Payhero API Error (non-JSON): {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code,
                    'response_text': response.text[:500]  # Include for debugging
                }
                
        except requests.exceptions.ConnectionError:
            # Fallback for development/testing when Payhero API is not available
            print('Payhero API not available. Simulating STK Push for development.')
            return {
                'success': True,
                'transaction_id': payhero_ref,
                'reference': payhero_ref,
                'checkout_request_id': payhero_ref,
                'message': 'STK Push simulated (Payhero API not available in development)',
                'simulated': True
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error connecting to Payhero: {str(e)}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Error initiating payment: {str(e)}'
        }

@login_required
def create_payment(request, bid_id):
    """Create payment record for accepted bid - with Payhero integration"""
    bid = get_object_or_404(Bid, id=bid_id)
    
    # Check permission - only broker can create payment
    if bid.broker != request.user:
        messages.error(request, 'Unauthorized')
        return redirect('broker_bids')
    
    if bid.status != 'accepted':
        messages.error(request, 'Payment can only be created for accepted bids')
        return redirect('broker_bids')
    
    # Check if payment already exists
    if Payment.objects.filter(bid=bid).exists():
        messages.error(request, 'Payment already exists for this bid')
        return redirect('broker_bids')
    
    # Handle GET request - show payment form
    if request.method == 'GET':
        phone_number = request.GET.get('phone_number', '')
        context = {
            'bid': bid,
            'phone_number': phone_number,
        }
        return render(request, 'pages/broker/create_payment.html', context)
    
    # Handle POST request - process payment
    if request.method == 'POST':
        try:
            payment_method = request.POST.get('payment_method', 'mpesa')
            transaction_id = request.POST.get('transaction_id', '')
            phone_number = request.POST.get('phone_number', '')
            use_payhero = request.POST.get('use_payhero', 'false') == 'true'
            
            # Update broker's phone number if provided
            if phone_number:
                request.user.profile.phone = phone_number
                request.user.profile.mpesa_number = phone_number
                request.user.profile.save()
            
            # Use phone number from profile if not provided
            if not phone_number:
                phone_number = request.user.profile.mpesa_number or request.user.profile.phone
            
            # Format phone number (ensure it starts with 254 for Kenya)
            if phone_number:
                phone_number = str(phone_number).strip()
                # Remove any spaces, dashes, or plus signs
                phone_number = phone_number.replace(' ', '').replace('-', '').replace('+', '')
                # If it starts with 0, replace with 254
                if phone_number.startswith('0'):
                    phone_number = '254' + phone_number[1:]
                # If it doesn't start with 254, add it
                elif not phone_number.startswith('254'):
                    phone_number = '254' + phone_number
            
            # Validate phone number
            if not phone_number:
                messages.error(request, 'Phone number is required for M-Pesa payment. Please enter your M-Pesa phone number.')
                return redirect('create_payment', bid_id=bid_id)
            
            # If using Payhero and credentials are configured
            # Validate Payhero credentials
            if use_payhero:
                if not hasattr(settings, 'PAYHERO_BASIC_AUTH_TOKEN') or not settings.PAYHERO_BASIC_AUTH_TOKEN:
                    messages.error(request, 'Payhero payment is not configured. Please contact support.')
                    print("ERROR: PAYHERO_BASIC_AUTH_TOKEN not set in settings")
                    return redirect('broker_bids')
                
                # Check if it's a placeholder value
                placeholder_values = ['your_payhero_api_key_here', 'your_actual_webhook_secret', '', None]
                if settings.PAYHERO_BASIC_AUTH_TOKEN in placeholder_values:
                    messages.error(request, 'Payhero credentials not configured. Please set PAYHERO_BASIC_AUTH_TOKEN in your environment variables or .env file.')
                    print(f"ERROR: PAYHERO_BASIC_AUTH_TOKEN appears to be a placeholder: {settings.PAYHERO_BASIC_AUTH_TOKEN}")
                    return redirect('broker_bids')
                
                # Proceed with Payhero payment
                callback_url = request.build_absolute_uri(f'/webhook/payhero/')
                
                # Debug logging
                print(f"=== PAYMENT INITIATION DEBUG ===")
                print(f"Bid ID: {bid.id}")
                print(f"Amount: {bid.total_price}")
                print(f"Phone Number: {phone_number}")
                print(f"Callback URL: {callback_url}")
                print(f"Payhero Base URL: {settings.PAYHERO_BASE_URL}")
                print(f"Channel ID: {getattr(settings, 'PAYHERO_CHANNEL_ID', 3905)}")
                print(f"Has Auth Token: {bool(settings.PAYHERO_BASIC_AUTH_TOKEN)}")
                
                payhero_result = initiate_payhero_payment(bid, callback_url, phone_number)
                
                print(f"Payhero Result: {payhero_result}")
                
                if payhero_result['success']:
                    # Create pending payment record
                    payment = Payment.objects.create(
                        bid=bid,
                        amount=bid.total_price,
                        payment_method='mpesa',
                        currency='KES',
                        status='pending',  # Will be updated via webhook
                        transaction_id=payhero_result.get('checkout_request_id') or payhero_result.get('transaction_id') or payhero_result.get('reference')
                    )
                    
                    # Show success message
                    if payhero_result.get('simulated'):
                        messages.warning(request, f'Payhero API not available. Simulating STK Push to {phone_number}. In production, this would send a real STK push.')
                        messages.info(request, f'Payment reference: {payhero_result.get("reference")}. Status will be updated when webhook is received.')
                    else:
                        messages.success(request, f'STK Push sent to {phone_number}. Please check your phone and enter your M-Pesa PIN to complete the payment.')
                        messages.info(request, f'Payment reference: {payhero_result.get("reference")}')
                        if payhero_result.get('checkout_request_id'):
                            messages.info(request, f'Checkout Request ID: {payhero_result.get("checkout_request_id")}')
                    
                    return redirect('payment_detail', payment_id=payment.id)
                else:
                    error_msg = payhero_result.get("error", "Unknown error")
                    messages.error(request, f'Payhero payment failed: {error_msg}')
                    print(f"PAYMENT ERROR: {error_msg}")
                    return redirect('create_payment', bid_id=bid_id)
            else:
                # For M-Pesa: Create payment and trigger STK Push
                # In production, integrate with Safaricom Daraja API for STK Push
                # For now, create pending payment and show instructions
                
                # Generate transaction ID
                transaction_id = transaction_id or f"MPESA-{bid.id}-{int(timezone.now().timestamp())}"
                
                payment = Payment.objects.create(
                    bid=bid,
                    amount=bid.total_price,
                    payment_method='mpesa',
                    currency='KES',
                    status='pending',  # Will be updated when user confirms on phone
                    transaction_id=transaction_id
                )
                
                # TODO: Integrate with Safaricom Daraja API STK Push
                # In production, you would call the Daraja API here:
                # from safaricom_daraja import initiate_stk_push
                # stk_response = initiate_stk_push(
                #     phone_number=phone_number,
                #     amount=float(bid.total_price),
                #     account_reference=f"BID-{bid.id}",
                #     transaction_desc=f"Payment for {bid.listing.get_produce_type_display()}",
                #     callback_url=request.build_absolute_uri('/webhook/mpesa/')
                # )
                # if stk_response.get('ResponseCode') == '0':
                #     # STK Push initiated successfully
                #     payment.transaction_id = stk_response.get('CheckoutRequestID')
                #     payment.save()
                
                # For now, show message that prompt should be received
                if phone_number:
                    messages.info(request, f'M-Pesa payment prompt should be sent to {phone_number}. Please check your phone and enter your M-Pesa PIN to complete the payment.')
                    messages.warning(request, 'If you do not receive the prompt within 30 seconds, the M-Pesa API integration may need to be configured. You can still manually confirm the payment from the payment details page after completing it via your phone.')
                else:
                    messages.error(request, 'Phone number is required for M-Pesa payment. Please add your phone number in your profile.')
                    return redirect('broker_bids')
                
                return redirect('payment_detail', payment_id=payment.id)
            
        except Exception as e:
            messages.error(request, f'Error creating payment: {str(e)}')
            return redirect('broker_bids')
    
    return redirect('broker_bids')

@login_required
def payhero_payment_redirect(request):
    """Redirect user to Payhero payment page"""
    payment_url = request.session.pop('payhero_payment_url', None)
    if payment_url:
        return redirect(payment_url)
    else:
        messages.error(request, 'Payment URL not found. Please try again.')
        return redirect('broker_bids')

@csrf_exempt
def payhero_webhook(request):
    """Handle Payhero webhook notifications"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Validate webhook signature
        signature = request.headers.get('X-Payhero-Signature', '')
        payload = request.body
        
        if hasattr(settings, 'PAYHERO_WEBHOOK_SECRET') and settings.PAYHERO_WEBHOOK_SECRET:
            expected_signature = hmac.new(
                settings.PAYHERO_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # Parse webhook data
        data = json.loads(payload)
        
        # Payhero v2 webhook format
        checkout_request_id = data.get('CheckoutRequestID') or data.get('checkout_request_id', '')
        merchant_request_id = data.get('MerchantRequestID', '')
        result_code = data.get('ResultCode', '')
        result_desc = data.get('ResultDesc', '')
        mpesa_receipt_number = data.get('MpesaReceiptNumber', '')
        transaction_date = data.get('TransactionDate', '')
        phone_number = data.get('PhoneNumber', '')
        amount = data.get('Amount', '')
        
        # Also check for external_reference or reference
        external_reference = data.get('external_reference') or data.get('reference', '')
        transaction_id = checkout_request_id or mpesa_receipt_number or external_reference
        
        # Find payment by transaction ID or reference
        try:
            payment = None
            
            # Try to find by checkout_request_id first
            if checkout_request_id:
                payment = Payment.objects.filter(transaction_id=checkout_request_id).first()
            
            # Try to find by external reference (BID_xxx format)
            if not payment and external_reference:
                if 'BID_' in external_reference:
                    try:
                        bid_id = int(external_reference.split('_')[1])
                        payment = Payment.objects.filter(bid_id=bid_id, status='pending').first()
                    except (ValueError, IndexError):
                        pass
            
            # Try to find by M-Pesa receipt number
            if not payment and mpesa_receipt_number:
                payment = Payment.objects.filter(transaction_id=mpesa_receipt_number).first()
            
            if not payment:
                print(f"Payment not found for webhook data: {data}")
                return JsonResponse({'error': 'Payment not found'}, status=404)
            
            # Update payment status based on webhook result code
            # Payhero/Safaricom ResultCode: 0 = success, other = failure
            if result_code == '0' or result_code == 0:
                # Payment successful
                payment.status = 'paid'
                if mpesa_receipt_number:
                    payment.transaction_id = mpesa_receipt_number
                payment.save()
                
                print(f"Payment {payment.id} marked as paid via webhook. Receipt: {mpesa_receipt_number}")
                return JsonResponse({'status': 'success', 'message': 'Payment updated successfully'})
            else:
                # Payment failed
                payment.status = 'failed'
                payment.save()
                
                print(f"Payment {payment.id} marked as failed via webhook. Result: {result_desc}")
                return JsonResponse({'status': 'failed', 'message': f'Payment failed: {result_desc}'})
            
        except Payment.DoesNotExist:
            print(f"Payment not found for webhook data: {data}")
            return JsonResponse({'error': 'Payment not found'}, status=404)
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return JsonResponse({'error': f'Error processing payment: {str(e)}'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return JsonResponse({'error': f'Webhook error: {str(e)}'}, status=500)

@login_required
def payment_history(request):
    """View payment history"""
    if request.user.profile.user_type == 'broker':
        payments = Payment.objects.filter(bid__broker=request.user).select_related('bid', 'bid__listing', 'bid__listing__farmer', 'bid__listing__farmer__profile').order_by('-timestamp')
    elif request.user.profile.user_type == 'farmer':
        payments = Payment.objects.filter(bid__listing__farmer=request.user).select_related('bid', 'bid__broker', 'bid__listing').order_by('-timestamp')
    else:
        payments = Payment.objects.none()
    
    # Calculate totals
    total_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    released_amount = payments.filter(status='released').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'payments': payments,
        'total_amount': total_amount,
        'released_amount': released_amount,
    }
    
    return render(request, 'pages/payments/history.html', context)

@login_required
def payment_detail(request, payment_id):
    """View detailed information about a specific payment"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Check permission
    if request.user.profile.user_type == 'broker':
        if payment.bid.broker != request.user:
            messages.error(request, 'Unauthorized')
            return redirect('payment_history')
    elif request.user.profile.user_type == 'farmer':
        if payment.bid.listing.farmer != request.user:
            messages.error(request, 'Unauthorized')
            return redirect('payment_history')
    else:
        messages.error(request, 'Unauthorized')
        return redirect('payment_history')
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'pages/payments/payment_detail.html', context)

@login_required
def test_payhero_connection(request):
    """Test Payhero API connection - for debugging"""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can access this test page')
        return redirect('broker_dashboard')
    
    from django.conf import settings
    import requests
    import json
    
    results = {
        'settings_check': {},
        'api_test': {},
        'errors': []
    }
    
    # Check settings
    results['settings_check'] = {
        'base_url': getattr(settings, 'PAYHERO_BASE_URL', 'NOT SET'),
        'has_auth_token': bool(getattr(settings, 'PAYHERO_BASIC_AUTH_TOKEN', None)),
        'auth_token_preview': str(getattr(settings, 'PAYHERO_BASIC_AUTH_TOKEN', ''))[:20] + '...' if getattr(settings, 'PAYHERO_BASIC_AUTH_TOKEN', None) else 'NOT SET',
        'channel_id': getattr(settings, 'PAYHERO_CHANNEL_ID', 'NOT SET'),
        'webhook_secret_set': bool(getattr(settings, 'PAYHERO_WEBHOOK_SECRET', None)),
    }
    
    # Check for placeholder values
    auth_token = getattr(settings, 'PAYHERO_BASIC_AUTH_TOKEN', '')
    placeholder_values = ['your_payhero_api_key_here', 'your_actual_webhook_secret', '', None]
    if auth_token in placeholder_values:
        results['errors'].append('PAYHERO_BASIC_AUTH_TOKEN appears to be a placeholder value')
    
    # Test API connection
    if request.method == 'POST':
        try:
            headers = {
                'Authorization': settings.PAYHERO_BASIC_AUTH_TOKEN,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            test_data = {
                'amount': 1,
                'phone_number': request.POST.get('test_phone', '254712345678'),
                'channel_id': int(getattr(settings, 'PAYHERO_CHANNEL_ID', 3905)),
                'provider': 'm-pesa',
                'external_reference': 'TEST_CONNECTION',
                'customer_name': 'Test User',
                'callback_url': request.build_absolute_uri('/webhook/payhero/')
            }
            
            api_url = f'{settings.PAYHERO_BASE_URL}/api/v2/payments'
            
            response = requests.post(
                api_url,
                headers=headers,
                json=test_data,
                timeout=30
            )
            
            results['api_test'] = {
                'status_code': response.status_code,
                'response_headers': dict(response.headers),
                'success': response.status_code == 201,
            }
            
            try:
                results['api_test']['response_body'] = response.json()
            except:
                results['api_test']['response_body'] = response.text[:500]
            
            if response.status_code == 201:
                messages.success(request, 'Payhero API connection successful!')
            elif response.status_code == 401:
                results['errors'].append('Authentication failed - check PAYHERO_BASIC_AUTH_TOKEN')
                messages.error(request, 'Authentication failed - check your credentials')
            elif response.status_code == 404:
                results['errors'].append('Endpoint not found - check API URL or channel ID')
                messages.warning(request, 'Endpoint not found - check API URL or channel ID')
            else:
                results['errors'].append(f'Unexpected response: {response.status_code}')
                messages.warning(request, f'Unexpected response: {response.status_code}')
                
        except requests.exceptions.ConnectionError:
            results['errors'].append('Cannot reach Payhero API - check network connection')
            messages.error(request, 'Cannot reach Payhero API - check network connection')
        except Exception as e:
            results['errors'].append(str(e))
            messages.error(request, f'Error: {str(e)}')
    
    context = {
        'results': results,
    }
    
    return render(request, 'pages/admin/test_payhero.html', context)

@login_required
def confirm_payment(request, payment_id):
    """Manually confirm payment completion (for when M-Pesa prompt is received)"""
    if request.method == 'POST':
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Check permission - only broker can confirm their own payment
        if payment.bid.broker != request.user:
            messages.error(request, 'Unauthorized')
            return redirect('payment_history')
        
        if payment.status != 'pending':
            messages.error(request, 'Payment is not pending')
            return redirect('payment_detail', payment_id=payment_id)
        
        # Update payment status to paid
        payment.status = 'paid'
        payment.save()
        
        messages.success(request, 'Payment confirmed successfully!')
        return redirect('payment_detail', payment_id=payment_id)
    
    return redirect('payment_detail', payment_id=payment_id)