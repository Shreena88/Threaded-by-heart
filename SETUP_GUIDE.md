# Threaded by Heart - Setup Guide

## Overview
Your crochet e-commerce website now includes:
- User authentication (login/logout)
- Razorpay payment integration for Indian Rupees (₹)
- Secure checkout process
- Session management

## Prerequisites

1. **Python Dependencies**: Install the new requirements
   ```bash
   pip install -r requirements.txt
   ```

2. **Razorpay Account**: 
   - Sign up at [Razorpay](https://razorpay.com/)
   - Get your API keys from the dashboard
   - Update the `.env` file with your actual keys

## Configuration

### 1. Environment Variables (.env)
Update your `.env` file with:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=crochet
PORT=5000

# Razorpay Configuration (Replace with your actual keys)
RAZORPAY_KEY_ID=rzp_test_your_key_id_here
RAZORPAY_KEY_SECRET=your_secret_key_here

# Session Secret Key (Generate a secure random string)
SECRET_KEY=your_secure_secret_key_here
```

### 2. Database Setup
The application will automatically create the required tables:
- `users` - for user authentication
- `customer` - for customer information
- `order` - for orders with payment tracking
- `product` - for products
- `category` - for product categories
- `order_product` - for order items

## New Features

### 1. User Authentication
- **Registration**: Users can create accounts at `/register.html`
- **Login**: Users can login at `/login.html`
- **Session Management**: Users stay logged in across pages
- **Logout**: Users can logout from any page

### 2. Payment Integration
- **Razorpay Integration**: Secure payment processing
- **Indian Rupees**: All prices displayed in ₹
- **Payment Verification**: Server-side payment verification
- **Order Tracking**: Orders linked to payment IDs

### 3. Enhanced Security
- **Password Hashing**: Using bcrypt for secure password storage
- **Session Management**: Flask-Session for secure sessions
- **Authentication Required**: Checkout requires login

## Usage Flow

1. **User Registration/Login**:
   - New users register at `register.html`
   - Existing users login at `login.html`
   - Navigation shows welcome message and logout option

2. **Shopping**:
   - Browse products on `shop.html`
   - Add items to cart
   - View cart at `cart.html`

3. **Checkout Process**:
   - Must be logged in to access checkout
   - Fill delivery details at `checkout.html`
   - Click "Proceed to Payment"
   - Complete payment via Razorpay
   - Order confirmation and redirect to home

## Testing

### Test Payment
Use Razorpay test credentials:
- **Test Card**: 4111 1111 1111 1111
- **CVV**: Any 3 digits
- **Expiry**: Any future date

### Test User Flow
1. Register a new account
2. Login with the account
3. Add products to cart
4. Proceed to checkout
5. Complete test payment
6. Verify order in database

## File Structure

```
├── app.py                 # Main Flask application with auth & payment
├── requirements.txt       # Updated dependencies
├── .env                  # Environment configuration
├── login.html            # User login page
├── register.html         # User registration page
├── home.html             # Updated with auth navigation
├── shop.html             # Updated with auth navigation
├── cart.html             # Updated with auth navigation
├── checkout.html         # Updated with payment integration
└── SETUP_GUIDE.md        # This guide
```

## Security Notes

1. **Never commit real API keys** to version control
2. **Use strong secret keys** for session management
3. **Enable HTTPS** in production
4. **Regularly update dependencies**
5. **Monitor payment transactions**

## Troubleshooting

### Common Issues

1. **Payment fails**: Check Razorpay keys and test mode
2. **Login doesn't work**: Verify database connection and user table
3. **Session issues**: Check SECRET_KEY configuration
4. **CORS errors**: Ensure credentials are included in requests

### Database Issues
If you encounter database errors, ensure:
- MySQL server is running
- Database credentials are correct
- Database `crochet` exists
- User has proper permissions

## Production Deployment

Before going live:
1. Switch to Razorpay live keys
2. Enable HTTPS
3. Set secure session cookies
4. Configure proper CORS origins
5. Set up database backups
6. Monitor error logs

## Support

For issues with:
- **Razorpay**: Check their documentation at https://razorpay.com/docs/
- **Flask**: Refer to Flask documentation
- **Database**: Check MySQL documentation

Your crochet e-commerce website is now ready with secure authentication and payment processing in Indian Rupees!