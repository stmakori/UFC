# Payhero Payment Integration Setup Guide

## 🔑 Setting Up Payhero Credentials

### Method 1: Environment Variables (Recommended)

1. **Create a `.env` file** in your project root:
   ```bash
   PAYHERO_API_KEY=your_actual_api_key
   PAYHERO_SECRET_KEY=your_actual_secret_key
   PAYHERO_BASE_URL=https://api.payhero.com
   PAYHERO_WEBHOOK_SECRET=your_actual_webhook_secret
   ```

2. **Install python-decouple** (optional but recommended):
   ```bash
   pip install python-decouple
   ```

3. **Update `Umoja/settings.py`** to use environment variables:
   ```python
   from decouple import config
   
   PAYHERO_API_KEY = config('PAYHERO_API_KEY', default='')
   PAYHERO_SECRET_KEY = config('PAYHERO_SECRET_KEY', default='')
   PAYHERO_BASE_URL = config('PAYHERO_BASE_URL', default='https://api.payhero.com')
   PAYHERO_WEBHOOK_SECRET = config('PAYHERO_WEBHOOK_SECRET', default='')
   ```

### Method 2: Direct Configuration (Current Setup)

Your Payhero credentials are configured in `Umoja/settings.py`:

```python
PAYHERO_API_KEY = os.environ.get('PAYHERO_API_KEY', 'your_payhero_api_key_here')
PAYHERO_SECRET_KEY = os.environ.get('PAYHERO_SECRET_KEY', 'your_payhero_secret_key_here')
PAYHERO_BASE_URL = os.environ.get('PAYHERO_BASE_URL', 'https://api.payhero.com')
PAYHERO_WEBHOOK_SECRET = os.environ.get('PAYHERO_WEBHOOK_SECRET', 'your_webhook_secret_here')
```

**Replace the placeholder values with your actual Payhero credentials.**

## 🔧 Where to Get Payhero Credentials

1. **Log into your Payhero dashboard**
2. **Navigate to API settings** or **Developer section**
3. **Generate API credentials**:
   - API Key
   - Secret Key
   - Webhook Secret (for validating incoming webhooks)

## 📡 Integration Points

### 1. Payment Initiation

The `initiate_payhero_payment()` function in `umoja/views.py` handles payment initiation:

- Creates payment request with Payhero API
- Returns payment URL for redirect
- Handles errors gracefully

### 2. Payment Flow

1. **Broker clicks "Pay" button** on accepted bid
2. **Payment modal opens** with Payhero option (checked by default)
3. **If Payhero is selected**:
   - Payment is initiated via Payhero API
   - User is redirected to Payhero payment page
   - Payment status is set to 'pending'
4. **If Payhero is unchecked**:
   - Manual payment recording (fallback)
   - Transaction ID can be entered manually

### 3. Webhook Validation

The `payhero_webhook()` function in `umoja/views.py`:

- Validates webhook signature using HMAC SHA256
- Updates payment status based on webhook data
- Handles success, failed, and pending statuses

**Webhook URL**: `https://yourdomain.com/webhook/payhero/`

## 🧪 Testing Your Integration

1. **Update credentials** in `settings.py` or `.env` file
2. **Test payment flow**:
   - Accept a bid as a farmer
   - As broker, click "Pay" on the accepted bid
   - Check if Payhero payment page loads
   - Complete test payment
3. **Monitor logs** for API responses
4. **Verify transaction status** updates in payment history

## 🔒 Security Best Practices

1. **Never commit credentials** to version control
   - Add `.env` to `.gitignore`
   - Use environment variables in production
2. **Validate webhook signatures** always
3. **Use HTTPS** for all Payhero communications
4. **Rotate API keys** regularly
5. **Monitor webhook endpoints** for suspicious activity

## 📞 Payhero Support

- **Documentation**: Check Payhero's API documentation
- **Support**: Contact Payhero support for integration help
- **Testing**: Use Payhero's sandbox environment for testing

## 🚀 Next Steps

1. **Get your Payhero credentials** from dashboard
2. **Update the settings.py file** or create `.env` file
3. **Test the payment flow** with a test bid
4. **Configure webhook URL** in Payhero dashboard
5. **Deploy to production** with secure credentials

## 📝 Payment Status Flow

- **Pending**: Payment initiated, awaiting confirmation
- **Paid**: Payment successful (via webhook)
- **Released**: Funds released to farmer (after collection)
- **Failed**: Payment failed or cancelled
- **Refunded**: Payment refunded

## 🔄 Manual Payment Fallback

If Payhero is unavailable or unchecked:
- Broker can manually record payment
- Transaction ID can be entered
- Payment status set to 'paid' immediately
- Useful for cash payments or other methods

Your Umoja Farmer Connect application is ready for Payhero integration!

