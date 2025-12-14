# Umoja Farmers Connect

A Django-based marketplace platform connecting farmers and brokers for efficient agricultural produce trading in Kenya.

## 🌾 Overview

Umoja Farmers Connect is a web application that facilitates direct connections between farmers and brokers, enabling fair produce trading, transparent pricing, and streamlined payment processing. The platform helps farmers find buyers for their produce while allowing brokers to discover quality agricultural products.

## ✨ Features

### For Farmers
- **Product Listings**: Create and manage produce listings with details like quantity, quality, price, and location
- **Bid Management**: Receive and review bids from brokers, accept or reject offers
- **Payment Tracking**: Monitor payment status for accepted bids
- **Nearby Brokers**: Discover brokers operating in your area
- **Dashboard**: View statistics, active listings, and bid status

### For Brokers
- **Marketplace**: Browse available produce listings from farmers
- **Bid Placement**: Place bids on farmer listings with quantity and price
- **Route Management**: Create and manage collection routes with GPS coordinates
- **Payment Integration**: Make payments via M-Pesa (Payhero integration) or manual methods
- **Bid Tracking**: Monitor bid status and manage accepted bids

### Payment System
- **M-Pesa Integration**: STK Push payments via Payhero API
- **Payment History**: Track all transactions
- **Payment Details**: View comprehensive payment information
- **Webhook Support**: Automatic payment status updates

## 🛠️ Technology Stack

- **Backend**: Django 6.0
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Payment Gateway**: Payhero (M-Pesa STK Push)
- **Python**: 3.8+

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Umoja
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies
```bash
pip install django pillow python-decouple requests
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Payhero Configuration (for M-Pesa payments)
PAYHERO_API_KEY=your_api_key
PAYHERO_SECRET_KEY=your_secret_key
PAYHERO_ACCOUNT_ID=your_account_id
PAYHERO_BASIC_AUTH_TOKEN=your_basic_auth_token
PAYHERO_BASE_URL=https://api.payhero.com
PAYHERO_CHANNEL_ID=your_channel_id
PAYHERO_WEBHOOK_SECRET=your_webhook_secret
```

### 5. Database Setup
```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## 📁 Project Structure

```
Umoja/
├── umoja/                  # Main Django app
│   ├── models.py          # Database models (FarmerProduct, Bid, Payment, Route, etc.)
│   ├── views.py           # View functions and business logic
│   ├── urls.py            # URL routing
│   ├── admin.py           # Django admin configuration
│   ├── forms.py           # Form definitions
│   ├── templatetags/      # Custom template tags
│   └── migrations/        # Database migrations
├── templates/             # HTML templates
│   ├── index.html         # Home page
│   ├── pages/             # Page templates
│   └── components/        # Reusable components
├── static/                # Static files (CSS, JS, images)
├── media/                 # User uploaded files
├── Umoja/                 # Django project settings
│   ├── settings.py        # Project settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI configuration
└── manage.py              # Django management script
```

## 🔑 Key Models

- **UserProfile**: Extended user information (user type, location, phone)
- **FarmerProduct**: Produce listings created by farmers
- **Bid**: Bids placed by brokers on farmer listings
- **Payment**: Payment records for accepted bids
- **Route**: Collection routes created by brokers
- **Review**: Reviews and ratings

## 🔄 User Workflow

### Farmer Workflow
1. Register/Login as Farmer
2. Create produce listing (type, quantity, quality, price, location)
3. Receive bids from brokers
4. Review and accept/reject bids
5. Receive payment notifications
6. Track completed transactions

### Broker Workflow
1. Register/Login as Broker
2. Browse marketplace for available produce
3. Place bids on listings
4. Wait for farmer acceptance
5. Make payment for accepted bids
6. Create routes for collection
7. Track bid status and payments

## 🔐 Security Features

- User authentication and authorization
- Role-based access control (Farmer/Broker)
- CSRF protection
- Secure payment processing
- Webhook signature validation

## 🌐 API Integration

### Payhero M-Pesa Integration
- STK Push for mobile payments
- Webhook support for payment status updates
- Transaction tracking and verification

## 🧪 Testing

To test the payment integration:
1. Access `/admin/test-payhero/` (superuser only)
2. Verify Payhero settings
3. Test STK Push with a valid phone number

## 📝 Environment Variables

All sensitive configuration is managed through environment variables using `python-decouple`. See `.env.example` for required variables.

## 🐛 Troubleshooting

### Migration Issues
```bash
python manage.py makemigrations
python manage.py migrate
```

### Static Files Not Loading
```bash
python manage.py collectstatic
```

### Database Reset (Development Only)
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Umoja Development Team

## 🙏 Acknowledgments

- Django community
- Bootstrap team
- Payhero for payment integration

## 📞 Support

For issues or questions, please open an issue on GitHub or contact the development team.

---

**Note**: This is a development version. For production deployment, ensure:
- Set `DEBUG=False`
- Configure proper database (PostgreSQL recommended)
- Set up proper static file serving
- Configure secure HTTPS
- Set up proper logging
- Review and harden security settings
