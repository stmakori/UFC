# Umoja Farmer Connect

A multi-role marketplace and logistics app connecting farmers and brokers for efficient produce trading and collection.

## Features

- **Farmers**: Create produce listings, receive bids from brokers, accept/reject bids, and receive payments
- **Brokers**: Browse farmer listings, place bids, manage routes, and make payments
- **Payment System**: Integrated payment tracking with M-Pesa, Stripe, and manual payment options
- **Route Management**: Brokers can create and manage collection routes with GPS coordinates

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation & Setup

### 1. Navigate to Project Directory
```bash
cd /home/korr1e/Desktop/UFC/Umoja
```

### 2. Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies
```bash
pip install django pillow
```

Or if you have a requirements.txt:
```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python3 manage.py migrate
```

This will:
- Create the database tables
- Apply all migrations including the new bid system models

### 5. Create Superuser (Optional - for admin access)
```bash
python3 manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 6. Run the Development Server
```bash
python3 manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

## Usage

### Accessing the Application

1. **Home Page**: `http://127.0.0.1:8000/`
2. **Admin Panel**: `http://127.0.0.1:8000/admin/` (requires superuser)

### User Registration

1. Click "Register" on the home page
2. Choose your role: **Farmer** or **Broker**
3. Fill in your details and submit

### For Farmers

1. **Create Listings**: Go to "My Products" → "Add Product"
   - Enter produce type, quantity, quality, location (with optional GPS coordinates)
   - Set expected price (optional)
   - Mark available from date

2. **View Bids**: Go to "Incoming Bids"
   - See all bids placed by brokers on your listings
   - Accept or reject bids
   - View bid details including broker info and proposed price

3. **Receive Payments**: Payments are automatically tracked when brokers pay for accepted bids

### For Brokers

1. **Browse Marketplace**: Go to "Marketplace"
   - Search and filter farmer listings
   - View listing details

2. **Place Bids**: 
   - Click on a listing → "Place Bid"
   - Enter quantity, price per unit
   - Optionally link to a route for pickup
   - Submit bid

3. **Manage Bids**: Go to "My Bids"
   - View all your bids and their status
   - Cancel pending bids
   - Make payments for accepted bids

4. **Create Routes**: Go to "My Routes" → "Create Route"
   - Set origin, destination, stops (with coordinates)
   - Set date, time, capacity, and price per kg

5. **Make Payments**: 
   - When a bid is accepted, go to "My Bids"
   - Click "Make Payment" on accepted bids
   - Enter payment method (M-Pesa/Stripe/Manual) and transaction ID
   - Payment status will be tracked

## Payment Flow

1. **Broker places bid** → Status: `pending`
2. **Farmer accepts bid** → Status: `accepted`
3. **Broker creates payment** → Payment status: `paid`
4. **Broker marks as collected** → Bid status: `collected`, Payment status: `released`
5. **Broker marks as completed** → Bid status: `completed`

## Color Theme

The application uses a **dark green nature theme**:
- Primary: `#1B5E20` (Dark forest green)
- Secondary: `#2E7D32` (Medium dark green)
- Accent: `#388E3C` (Lighter green)

## Project Structure

```
Umoja/
├── umoja/              # Main app
│   ├── models.py       # Database models (FarmerProduct, Bid, Payment, etc.)
│   ├── views.py        # View functions
│   ├── urls.py         # URL routing
│   └── admin.py        # Admin configuration
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── media/              # User uploaded files
└── manage.py          # Django management script
```

## Troubleshooting

### Migration Issues
If you encounter migration errors:
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### Static Files Not Loading
```bash
python3 manage.py collectstatic
```

### Database Reset (Development Only)
```bash
rm db.sqlite3
python3 manage.py migrate
python3 manage.py createsuperuser
```

## Development Notes

- The project uses SQLite for development (no additional database setup needed)
- Media files are stored in the `media/` directory
- Static files are in the `static/` directory
- All user roles are managed through the `UserProfile` model

## Support

For issues or questions, check the code comments or Django documentation.

