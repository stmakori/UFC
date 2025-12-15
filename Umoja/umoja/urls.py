from django.urls import path
from . import views

urlpatterns = [
    # Home and Auth
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Broker URLs
    path('broker/dashboard/', views.broker_dashboard, name='broker_dashboard'),
    path('broker/marketplace/', views.broker_marketplace, name='broker_marketplace'),
    path('broker/listings/<int:listing_id>/', views.listing_detail, name='listing_detail'),
    path('broker/listings/<int:listing_id>/bid/', views.place_bid, name='place_bid'),
    path('broker/bids/', views.broker_bids, name='broker_bids'),
    path('broker/bids/<int:bid_id>/', views.broker_bid_detail, name='broker_bid_detail'),
    path('broker/bids/<int:bid_id>/cancel/', views.cancel_bid, name='cancel_bid'),
    path('broker/routes/', views.broker_routes, name='broker_routes'),
    path('broker/routes/create/', views.create_route, name='create_route'),
    path('broker/routes/<int:route_id>/edit/', views.edit_route, name='edit_route'),
    path('broker/routes/<int:route_id>/delete/', views.delete_route, name='delete_route'),
    path('broker/routes/<int:route_id>/', views.route_details, name='route_details'),
    
    # Farmer URLs
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer/products/', views.farmer_products, name='farmer_products'),
    path('farmer/products/<int:product_id>/', views.farmer_product_detail, name='farmer_product_detail'),
    path('farmer/products/<int:product_id>/delete/', views.delete_farmer_product, name='delete_farmer_product'),
    path('farmer/bids/', views.farmer_bids, name='farmer_bids'),
    path('farmer/bids/<int:bid_id>/accept/', views.accept_bid, name='accept_bid'),
    path('farmer/bids/<int:bid_id>/reject/', views.reject_bid, name='reject_bid'),
    path('farmer/listings/<int:listing_id>/bids/', views.listing_bids, name='listing_bids'),
    path('farmer/profile/', views.farmer_profile, name='farmer_profile'),
    path('farmer/nearby-brokers/', views.nearby_brokers, name='nearby_brokers'),
    
    # Payment URLs
    path('payments/', views.payment_history, name='payment_history'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/confirm/', views.confirm_payment, name='confirm_payment'),
    path('payments/bid/<int:bid_id>/create/', views.create_payment, name='create_payment'),
    path('payments/initiate/<str:payment_type>/<int:reference_id>/', views.initiate_payhero_payment, name='initiate_payhero_payment'),
    path('payments/payhero/redirect/', views.payhero_payment_redirect, name='payhero_payment_redirect'),
    path('webhook/payhero/', views.payhero_webhook, name='payhero_webhook'),
    
    # Profile Management URLs
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/picture/', views.update_profile_picture, name='update_profile_picture'),
    path('profile/notifications/', views.update_notifications, name='update_notifications'),
    path('password/change/', views.password_change, name='password_change'),
    
    # API URLs
    path('api/bids/<int:bid_id>/collect/', views.mark_collected, name='mark_collected'),
    path('api/bids/<int:bid_id>/complete/', views.mark_completed, name='mark_completed'),
    
    # Admin/Test URLs
    path('admin/test-payhero/', views.test_payhero_connection, name='test_payhero'),
]