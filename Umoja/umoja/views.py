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
            
            if quantity_requested > listing.available_quantity:
                messages.error(request, f'Only {listing.available_quantity} {listing.unit} available')
                return redirect('listing_detail', listing_id=listing_id)
            
            # Validate price
            if price_per_unit <= 0:
                messages.error(request, 'Price must be greater than 0')
                return redirect('listing_detail', listing_id=listing_id)
                
            if listing.price_expected and price_per_unit < listing.price_expected:
                messages.error(request, f'Bid price must be at least KES {listing.price_expected:.2f}')
                return redirect('listing_detail', listing_id=listing_id)
            
            # Create bid
            bid = Bid.objects.create(
                broker=request.user,
                listing=listing,
                quantity_requested=quantity_requested,
                price_per_unit=price_per_unit,
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
    
    context = {
        'active_listings': active_listings,
        'incoming_bids': incoming_bids,
        'accepted_bids': accepted_bids,
        'total_revenue': total_revenue,
        'recent_bids': recent_bids,
    }
    
    return render(request, 'pages/farmer/dashboard.html', context)

@login_required
def farmer_products(request):
    """Manage farmer produce listings"""
    if request.user.profile.user_type != 'farmer':
        return redirect('broker_dashboard')
    
    if request.method == 'POST':
        # Handle listing creation
        try:
            listing = FarmerProduct.objects.create(
                farmer=request.user,
                produce_type=request.POST.get('produce_type'),
                quantity_available=float(request.POST.get('quantity_available', 0)),
                unit=request.POST.get('unit', 'kg'),
                quality=request.POST.get('quality', 'standard'),
                price_expected=float(request.POST.get('price_expected', 0)) if request.POST.get('price_expected') else None,
                origin_text=request.POST.get('origin_text', ''),
                origin_lat=float(request.POST.get('origin_lat')) if request.POST.get('origin_lat') else None,
                origin_lng=float(request.POST.get('origin_lng')) if request.POST.get('origin_lng') else None,
                available_from=request.POST.get('available_from'),
                notes=request.POST.get('notes', ''),
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
        'total_listings': total_listings,
        'active_listings': active_listings,
        'pending_bids': pending_bids,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'pages/farmer/products.html', context)

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
        if bid.quantity_requested > bid.listing.available_quantity:
            messages.error(request, 'Insufficient quantity available')
            return redirect('farmer_bids')
        
        # Accept the bid
        bid.status = 'accepted'
        bid.save()
        
        # Optionally create a contract
        Contract.objects.get_or_create(bid=bid)
        
        # Reject other pending bids for the same listing if quantity would be exceeded
        other_bids = Bid.objects.filter(
            listing=bid.listing,
            status='pending'
        ).exclude(id=bid.id)
        
        for other_bid in other_bids:
            # Check if accepting this would exceed available quantity
            total_reserved = bid.listing.reserved_quantity + other_bid.quantity_requested
            if total_reserved > bid.listing.quantity_available:
                other_bid.status = 'rejected'
                other_bid.save()
        
        messages.success(request, 'Bid accepted successfully!')
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
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('farmer_profile')
    
    return redirect('farmer_profile')

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

def initiate_payhero_payment(bid, callback_url):
    """Initiate Payhero payment and return payment URL"""
    try:
        headers = {
            'Authorization': f'Bearer {settings.PAYHERO_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'amount': float(bid.total_price),
            'currency': 'KES',
            'reference': f'BID-{bid.id}-{int(timezone.now().timestamp())}',
            'callback_url': callback_url,
            'description': f'Payment for {bid.listing.get_produce_type_display()} - Bid #{bid.id}',
            'customer': {
                'name': bid.broker.get_full_name() or bid.broker.username,
                'email': bid.broker.email,
                'phone': bid.broker.profile.phone or ''
            }
        }
        
        response = requests.post(
            f'{settings.PAYHERO_BASE_URL}/payments',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'payment_url': result.get('payment_url'),
                'transaction_id': result.get('transaction_id'),
                'reference': data['reference']
            }
        else:
            return {
                'success': False,
                'error': response.text or 'Payment initiation failed'
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error: {str(e)}'
        }

@login_required
def create_payment(request, bid_id):
    """Create payment record for accepted bid - with Payhero integration"""
    if request.method == 'POST':
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
        
        try:
            payment_method = request.POST.get('payment_method', 'mpesa')
            transaction_id = request.POST.get('transaction_id', '')
            use_payhero = request.POST.get('use_payhero', 'false') == 'true'
            
            # If using Payhero and credentials are configured
            if use_payhero and hasattr(settings, 'PAYHERO_API_KEY') and settings.PAYHERO_API_KEY != 'your_payhero_api_key_here':
                callback_url = request.build_absolute_uri(f'/webhook/payhero/')
                payhero_result = initiate_payhero_payment(bid, callback_url)
                
                if payhero_result['success']:
                    # Create pending payment record
                    payment = Payment.objects.create(
                        bid=bid,
                        amount=bid.total_price,
                        payment_method=payment_method,
                        currency='KES',
                        status='pending',  # Will be updated via webhook
                        transaction_id=payhero_result.get('transaction_id') or payhero_result.get('reference')
                    )
                    
                    # Store payment URL in session for redirect
                    request.session['payhero_payment_url'] = payhero_result['payment_url']
                    request.session['payment_id'] = payment.id
                    
                    messages.info(request, 'Redirecting to Payhero payment page...')
                    return redirect('payhero_payment_redirect')
                else:
                    messages.error(request, f'Payhero payment failed: {payhero_result.get("error", "Unknown error")}')
                    return redirect('broker_bids')
            else:
                # Manual payment recording (fallback)
                payment = Payment.objects.create(
                    bid=bid,
                    amount=bid.total_price,
                    payment_method=payment_method,
                    currency='KES',
                    status='paid',
                    transaction_id=transaction_id or f"TXN-{bid.id}-{timezone.now().timestamp()}"
                )
                
                messages.success(request, 'Payment recorded successfully')
                return redirect('broker_bids')
            
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
        transaction_id = data.get('transaction_id') or data.get('reference', '')
        status = data.get('status', '').lower()
        amount = data.get('amount')
        
        # Find payment by transaction ID
        try:
            # Try to extract bid ID from reference
            reference = data.get('reference', '')
            if 'BID-' in reference:
                bid_id = int(reference.split('-')[1])
                payment = Payment.objects.filter(bid_id=bid_id).first()
            else:
                payment = Payment.objects.filter(transaction_id=transaction_id).first()
            
            if not payment:
                return JsonResponse({'error': 'Payment not found'}, status=404)
            
            # Update payment status based on webhook
            if status == 'success' or status == 'completed' or status == 'paid':
                payment.status = 'paid'
                payment.save()
                
                # Optionally mark bid as collected if payment is successful
                if payment.bid.status == 'accepted':
                    # Payment successful, bid can proceed
                    pass
                    
            elif status == 'failed' or status == 'cancelled':
                payment.status = 'failed'
                payment.save()
            elif status == 'pending':
                payment.status = 'pending'
                payment.save()
            
            return JsonResponse({'success': True, 'message': 'Webhook processed'})
            
        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Payment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error processing payment: {str(e)}'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
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