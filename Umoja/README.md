# Umoja Farmers Connect

A Django-based web platform that connects farmers and brokers to facilitate agricultural produce trading, optimize transportation, and ensure fair pricing for agricultural products in Kenya.

## 🌾 About

Umoja Farmers Connect brings together farmers and brokers to enable direct trading of agricultural produce. The platform facilitates bidding on produce listings, manages payment transactions through M-Pesa (via Payhero), and helps optimize transportation routes for efficient delivery.

**Umoja** means "unity" in Swahili, reflecting our core belief that together, we can build a more efficient and equitable agricultural supply chain.

## ✨ Features

### For Farmers
- Create and manage produce listings (maize, beans, tomatoes, potatoes, etc.)
- View and manage bids from brokers
- Accept or reject bids
- Track payment status
- Manage profile with farm details, location, and payment preferences
- View nearby brokers

### For Brokers
- Browse marketplace of available produce listings
- Place bids on farmer listings
- Manage bidding history and accepted bids
- Create and manage transportation routes
- Complete payments via M-Pesa STK Push (Payhero integration)
- Track payment history
- Dashboard with key metrics and recent activity

### General Features
- User authentication and registration with role-based access (Farmer/Broker/Admin)
- Real-time bidding system
- Integrated M-Pesa payment processing via Payhero API
- Payment webhook handling for automatic payment confirmation
- Interactive maps using Leaflet for location visualization
- Responsive design with Bootstrap 5
- Secure payment processing
- Payment history tracking

## 🛠️ Technologies Used

- **Backend**: Django (Python web framework)
- **Database**: SQLite (default, can be configured for PostgreSQL/MySQL)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Payment Gateway**: Payhero API (M-Pesa STK Push)
- **Maps**: Leaflet.js
- **Environment Management**: python-decouple

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Umoja
```

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install django
pip install python-decouple
pip install pillow  # For image handling
```

Or create a `requirements.txt` file and install:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory:

```env
# Django Settings
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Payhero API Configuration
PAYHERO_API_KEY=your_payhero_api_key
PAYHERO_SECRET_KEY=your_payhero_secret_key
PAYHERO_ACCOUNT_ID=3425
PAYHERO_BASIC_AUTH_TOKEN=your_basic_auth_token
PAYHERO_BASE_URL=https://backend.payhero.co.ke
PAYHERO_CHANNEL_ID=4630
PAYHERO_WEBHOOK_SECRET=your_webhook_secret

# Optional: Login/Logout URLs
LOGIN_URL=/login/
LOGIN_REDIRECT_URL=/dashboard/
LOGOUT_REDIRECT_URL=/
```

**Important**: Replace all placeholder values with your actual credentials from Payhero.

### 5. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Collect Static Files

```bash
python manage.py collectstatic
```

### 8. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## 📁 Project Structure

```
Umoja/
├── Umoja/              # Django project settings
│   ├── settings.py     # Main settings file
│   ├── urls.py         # Root URL configuration
│   └── wsgi.py         # WSGI configuration
├── umoja/              # Main Django app
│   ├── models.py       # Database models
│   ├── views.py        # View functions
│   ├── forms.py        # Form definitions
│   ├── urls.py         # App URL patterns
│   └── migrations/     # Database migrations
├── templates/          # HTML templates
│   ├── index.html      # Homepage
│   ├── components/     # Reusable components
│   └── pages/          # Page templates
│       ├── auth/       # Authentication pages
│       ├── broker/     # Broker-specific pages
│       ├── farmer/     # Farmer-specific pages
│       └── payments/   # Payment pages
├── static/             # Static files
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   ├── icons/          # Icons (favicon)
│   └── images/         # Images
├── media/              # User-uploaded files
│   ├── products/       # Product images
│   └── profiles/       # Profile pictures
└── manage.py           # Django management script
```

## 🔐 Configuration

### Payhero API Setup

1. Sign up for a Payhero account at https://payhero.co.ke
2. Obtain your API credentials:
   - API Key
   - Secret Key
   - Basic Auth Token
   - Account ID
   - Channel ID
   - Webhook Secret

3. Configure your webhook URL in Payhero dashboard:
   ```
   https://yourdomain.com/webhook/payhero/
   ```

4. Update the `.env` file with your credentials

### Database Configuration

By default, the project uses SQLite. To use PostgreSQL or MySQL, update `DATABASES` in `Umoja/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'umoja_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🎯 Usage

### For Farmers

1. Register/Login with a "Farmer" account
2. Navigate to "My Products" from the dashboard
3. Create a new product listing with details (produce type, quantity, price, location)
4. Wait for brokers to place bids
5. Review bids and accept the best offer
6. Track payment status after broker completes payment

### For Brokers

1. Register/Login with a "Broker" account
2. Browse the marketplace for available produce
3. Place bids on listings
4. Manage your bids from "My Bids"
5. When a bid is accepted, complete payment via M-Pesa STK Push
6. Mark bid as collected and completed after delivery

## 🔄 Payment Flow

1. Broker places a bid on a farmer's listing
2. Farmer accepts the bid
3. Broker initiates payment via the payment page
4. System redirects to phone number entry page
5. Broker enters M-Pesa phone number
6. STK Push is sent to the phone
7. Broker completes payment on their phone
8. Payhero webhook confirms payment
9. Payment status is updated automatically

## 🧪 Testing

Test Payhero connection:
```
http://127.0.0.1:8000/admin/test-payhero/
```

## 🐛 Troubleshooting

### Payment Issues
- Ensure Payhero credentials are correctly configured in `.env`
- Check that webhook URL is accessible and correctly configured in Payhero dashboard
- Verify phone number format (should be in format: 254712345678)

### Database Issues
- Run migrations: `python manage.py migrate`
- If issues persist, delete `db.sqlite3` and re-run migrations

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Ensure `DEBUG=True` in settings for development

## 📝 License

[Specify your license here]

## 👥 Contributors

[Add contributor information]

## 📧 Support

For support, email [your-email] or open an issue in the repository.

## 🙏 Acknowledgments

- Payhero for payment gateway integration
- Django community for excellent documentation
- Bootstrap team for the UI framework

---

**Made with ❤️ for Kenyan farmers and brokers**

