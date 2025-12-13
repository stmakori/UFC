from django.contrib import admin
from .models import UserProfile, Route, Bid, Payment, Review, FarmerProduct, Contract

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'phone', 'location', 'is_verified', 'created_at')
    list_filter = ('user_type', 'is_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'location')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(FarmerProduct)
class FarmerProductAdmin(admin.ModelAdmin):
    list_display = ('produce_type', 'farmer', 'quantity_available', 'unit', 'quality', 'price_expected', 'origin_text', 'status', 'available_from', 'created_at')
    list_filter = ('produce_type', 'quality', 'unit', 'status', 'available_from', 'created_at')
    search_fields = ('farmer__username', 'farmer__email', 'produce_type', 'origin_text', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'reserved_quantity', 'available_quantity')
    
    fieldsets = (
        ('Listing Information', {
            'fields': ('farmer', 'produce_type', 'quantity_available', 'unit', 'quality')
        }),
        ('Pricing', {
            'fields': ('price_expected',)
        }),
        ('Location', {
            'fields': ('origin_text', 'origin_lat', 'origin_lng')
        }),
        ('Availability', {
            'fields': ('available_from', 'status', 'reserved_quantity', 'available_quantity')
        }),
        ('Details', {
            'fields': ('notes', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'broker', 'origin', 'destination', 'date', 'time', 'capacity_percentage', 'status')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('name', 'broker__username', 'origin', 'destination')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'booked_capacity', 'capacity_percentage')
    
    fieldsets = (
        ('Route Information', {
            'fields': ('broker', 'name', 'description')
        }),
        ('Location', {
            'fields': ('origin', 'destination', 'stops')
        }),
        ('Schedule', {
            'fields': ('date', 'time')
        }),
        ('Capacity', {
            'fields': ('capacity', 'available_capacity', 'booked_capacity', 'capacity_percentage')
        }),
        ('Pricing & Status', {
            'fields': ('price_per_kg', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'broker', 'listing', 'quantity_requested', 'price_per_unit', 'total_price', 'status', 'route', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('broker__username', 'listing__produce_type', 'listing__farmer__username', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    
    fieldsets = (
        ('Bid Details', {
            'fields': ('broker', 'listing', 'status')
        }),
        ('Offer Information', {
            'fields': ('quantity_requested', 'price_per_unit', 'total_price')
        }),
        ('Route & Notes', {
            'fields': ('route', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('bid', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('bid__id', 'bid__broker__username', 'bid__listing__farmer__username')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Contract Information', {
            'fields': ('bid', 'terms')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'bid', 'amount', 'currency', 'payment_method', 'transaction_id', 'status', 'timestamp')
    list_filter = ('status', 'payment_method', 'currency', 'timestamp')
    search_fields = ('transaction_id', 'bid__id', 'bid__broker__username', 'bid__listing__farmer__username')
    readonly_fields = ('timestamp', 'updated_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('bid', 'amount', 'currency', 'payment_method')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'status')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'updated_at')
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('bid', 'rating', 'get_farmer', 'get_broker', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('bid__id', 'bid__listing__farmer__username', 'bid__broker__username', 'comment')
    readonly_fields = ('created_at',)
    
    def get_farmer(self, obj):
        return obj.bid.listing.farmer.username
    get_farmer.short_description = 'Farmer'
    
    def get_broker(self, obj):
        return obj.bid.broker.username
    get_broker.short_description = 'Broker'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('bid', 'rating')
        }),
        ('Comments', {
            'fields': ('comment',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
