from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    USER_TYPES = (
        ('farmer', 'Farmer'),
        ('broker', 'Broker'),
        ('admin', 'Admin'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    phone = models.CharField(max_length=15)
    location = models.CharField(max_length=255)
    
    # Profile fields for farmer profile page
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    id_number = models.CharField(max_length=20, null=True, blank=True)
    farm_name = models.CharField(max_length=255, null=True, blank=True)
    farm_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gps_coordinates = models.CharField(max_length=100, null=True, blank=True)
    
    # Payment information
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    mpesa_number = models.CharField(max_length=15, null=True, blank=True)
    payment_preference = models.CharField(max_length=20, default='mpesa')
    
    # Account status
    is_verified = models.BooleanField(default=False)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
    
    @property
    def masked_account_number(self):
        """Return masked account number for security"""
        if self.account_number:
            if len(self.account_number) > 4:
                return '*' * (len(self.account_number) - 4) + self.account_number[-4:]
            return self.account_number
        return ''

class FarmerProduct(models.Model):
    """Farmer produce listing"""
    PRODUCE_TYPES = (
        ('maize', 'Maize'),
        ('beans', 'Beans'),
        ('tomatoes', 'Tomatoes'),
        ('potatoes', 'Potatoes'),
        ('cabbage', 'Cabbage'),
        ('onions', 'Onions'),
        ('carrots', 'Carrots'),
        ('wheat', 'Wheat'),
        ('rice', 'Rice'),
        ('other', 'Other'),
    )
    
    QUALITY_CHOICES = (
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('organic', 'Organic'),
        ('grade_a', 'Grade A'),
        ('grade_b', 'Grade B'),
    )
    
    UNIT_CHOICES = (
        ('kg', 'Kilograms (kg)'),
        ('ton', 'Tons'),
        ('bag', 'Bags'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('expired', 'Expired'),
    )
    
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmer_products')
    produce_type = models.CharField(max_length=50, choices=PRODUCE_TYPES)
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2)  # available quantity
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    quality = models.CharField(max_length=20, choices=QUALITY_CHOICES, default='standard')
    price_expected = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # optional expected price per unit
    origin_text = models.CharField(max_length=255)  # location text description
    origin_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # latitude
    origin_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # longitude
    available_from = models.DateField()
    notes = models.TextField(blank=True)  # renamed from description
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Farmer Product'
        verbose_name_plural = 'Farmer Products'
    
    def __str__(self):
        return f"{self.get_produce_type_display()} - {self.quantity_available}{self.unit} by {self.farmer.username}"
    
    @property
    def total_value(self):
        """Calculate total value if price_expected is set"""
        if self.price_expected:
            return self.quantity_available * self.price_expected
        return None
    
    @property
    def is_available(self):
        """Check if product is still available"""
        return self.status == 'active' and self.available_from <= timezone.now().date()
    
    @property
    def reserved_quantity(self):
        """Calculate quantity reserved by accepted bids"""
        from django.db.models import Sum
        return self.bids.filter(status='accepted').aggregate(
            total=Sum('quantity_requested')
        )['total'] or 0
    
    @property
    def available_quantity(self):
        """Calculate available quantity after reservations"""
        return self.quantity_available - self.reserved_quantity
        
    def user_has_bid(self, user):
        """Check if the given user has placed a bid on this listing"""
        if not user.is_authenticated:
            return False
        return self.bids.filter(broker=user).exists()
    
    def get_user_bid(self, request=None):
        """Get the current user's bid on this listing, if any"""
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        try:
            return self.bids.get(broker=request.user)
        except Bid.DoesNotExist:
            return None
            
    def has_user_bid(self, request=None):
        """Check if the current user has placed a bid on this listing"""
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        return self.bids.filter(broker=request.user).exists()
        
    # Keep the old method for backward compatibility
    def user_bid(self, user):
        if not user.is_authenticated:
            return None
        try:
            return self.bids.get(broker=user)
        except Bid.DoesNotExist:
            return None

class Route(models.Model):
    """Broker collection route"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    broker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routes')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    origin = models.CharField(max_length=255)  # origin location text
    destination = models.CharField(max_length=255)  # destination location text
    stops = models.JSONField(default=list)  # List of stop coordinates [{'lat': float, 'lng': float}, ...]
    date = models.DateField()
    time = models.TimeField()
    capacity = models.IntegerField()  # in kg
    available_capacity = models.IntegerField()
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def booked_capacity(self):
        """Calculate total booked capacity"""
        return self.capacity - self.available_capacity
    
    @property
    def capacity_percentage(self):
        """Calculate percentage of capacity booked"""
        try:
            if self.capacity == 0:
                return 0
            booked = self.capacity - self.available_capacity
            return int((booked / self.capacity) * 100)
        except (TypeError, ValueError, ZeroDivisionError):
            return 0
    
    def __str__(self):
        return f"{self.name} - {self.broker.username}"

class Bid(models.Model):
    """Broker bid/offer to buy farmer produce"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('collected', 'Collected'),
        ('completed', 'Completed'),
    )
    
    broker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    listing = models.ForeignKey('FarmerProduct', on_delete=models.CASCADE, related_name='bids')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='bids')
    quantity_requested = models.DecimalField(max_digits=10, decimal_places=2)  # quantity broker wants to buy
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)  # broker's offered price per unit
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # computed: quantity_requested * price_per_unit
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bid by {self.broker.username} for {self.listing}"
        
    def get_status_class(self):
        """Return the appropriate Bootstrap class for the bid status"""
        status_classes = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary',
            'collected': 'info',
            'completed': 'primary'
        }
        return status_classes.get(self.status, 'secondary')

    def get_status_icon(self):
        """Return the appropriate Bootstrap icon for the bid status"""
        status_icons = {
            'pending': 'bi-hourglass-split',
            'accepted': 'bi-check-circle',
            'rejected': 'bi-x-circle',
            'cancelled': 'bi-slash-circle',
            'collected': 'bi-truck',
            'completed': 'bi-check-circle-fill'
        }
        return status_icons.get(self.status, 'bi-question-circle')

    def get_status_display(self):
        """Return a more user-friendly status display"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status).title()

    def save(self, *args, **kwargs):
        """Auto-calculate total_price"""
        if not self.total_price or self._state.adding:
            self.total_price = self.quantity_requested * self.price_per_unit
        super().save(*args, **kwargs)

class Payment(models.Model):
    """Payment/Payout record for accepted bids"""
    PAYMENT_METHODS = (
        ('stripe', 'Stripe'),
        ('mpesa', 'M-Pesa'),
        ('manual', 'Manual'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    )
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='mpesa')
    currency = models.CharField(max_length=3, default='KES')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Payment #{self.id} - {self.amount} {self.currency} ({self.status})"

class Contract(models.Model):
    """Contract record when a bid is accepted (optional - bid.status='accepted' can serve as contract)"""
    bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name='contract')
    created_at = models.DateTimeField(auto_now_add=True)
    terms = models.TextField(blank=True)  # optional contract terms
    
    def __str__(self):
        return f"Contract for Bid #{self.bid.id}"

class Review(models.Model):
    """Review/rating for completed transactions"""
    bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for Bid #{self.bid.id} - {self.rating} stars"
