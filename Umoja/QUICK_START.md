# Quick Start Guide

## Running the Project

### Step 1: Install Dependencies
```bash
pip install django pillow
```

### Step 2: Run Migrations
```bash
python3 manage.py migrate
```

### Step 3: Start Server
```bash
python3 manage.py runserver
```

### Step 4: Access Application
Open your browser and go to: **http://127.0.0.1:8000/**

## Payment Functionality

✅ **YES - Brokers CAN make payments to farmers!**

### Payment Flow:
1. Broker places a bid on a farmer's listing
2. Farmer accepts the bid
3. Broker goes to "My Bids" page
4. Broker clicks "Make Payment" on the accepted bid
5. Broker enters:
   - Payment method (M-Pesa/Stripe/Manual)
   - Transaction ID
6. Payment is recorded and tracked
7. When broker marks bid as "collected", payment is automatically released to farmer

### Payment URL:
- **Create Payment**: `/payments/bid/<bid_id>/create/`
- **Payment History**: `/payments/`

## Color Theme

The project now uses a **dark green nature theme**:
- Main color: `#1B5E20` (Dark forest green)
- All buttons, links, and accents use this dark green
- Perfect for an agricultural/farming platform!

## First Time Setup

1. **Create Admin User** (optional):
   ```bash
   python3 manage.py createsuperuser
   ```

2. **Register as Farmer or Broker**:
   - Go to http://127.0.0.1:8000/register/
   - Choose your role
   - Fill in details

3. **Start Using**:
   - Farmers: Create listings → Receive bids → Accept bids → Get paid
   - Brokers: Browse marketplace → Place bids → Make payments → Collect produce

## Troubleshooting

**Port already in use?**
```bash
python3 manage.py runserver 8001
```

**Database errors?**
```bash
python3 manage.py migrate --run-syncdb
```

**Static files not loading?**
```bash
python3 manage.py collectstatic
```

