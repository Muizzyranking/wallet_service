# Wallet Service API

A robust backend wallet service built with Django and Django Ninja that enables users to deposit money via Paystack, manage wallet balances, view transaction history, and transfer funds between users. The service supports both JWT authentication (Google OAuth) and API key-based authentication for service-to-service access.

## 🚀 Features

### Authentication & Authorization
- **Google OAuth Integration** - Sign in with Google to generate JWT tokens
- **JWT Authentication** - Secure user authentication with access and refresh tokens
- **API Key System** - Service-to-service authentication with granular permissions
- **Permission-based Access** - API keys support `deposit`, `transfer`, and `read` permissions

### Wallet Operations
- **Paystack Deposits** - Initialize deposits and receive payment links
- **Webhook Integration** - Automatic wallet crediting via Paystack webhooks with signature validation
- **Wallet Transfers** - Send money to other users using their wallet numbers
- **Balance Management** - View current wallet balance
- **Transaction History** - Track all deposits and transfers

### Security Features
- **Webhook Signature Validation** - Verifies Paystack webhook authenticity
- **Idempotent Webhooks** - Prevents double-crediting from duplicate events
- **Atomic Transfers** - Ensures no partial deductions (all or nothing)
- **API Key Limits** - Maximum 5 active keys per user
- **API Key Expiration** - Keys expire based on configured duration (1H, 1D, 1M, 1Y)
- **Hashed API Keys** - Keys stored as SHA256 hashes for security

## 📋 Requirements

- Python 3.11+
- PostgreSQL (or SQLite for development)
- Paystack Account (test/live)
- Google OAuth Credentials

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd wallet_service
```

### 2. Install Dependencies with UV
```bash
# Install UV if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 3. Environment Configuration
Create a `.env` file in the project root:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=wallet_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Paystack
PAYSTACK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
PAYSTACK_PUBLIC_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx

# API Settings
API_KEY_PREFIX=sk_live_
API_KEY_LENGTH=32

# Application URL
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 4. Set Up Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
6. Copy Client ID and Client Secret to `.env`

### 5. Set Up Paystack
1. Sign up at [Paystack](https://dashboard.paystack.com/signup)
2. Get your test API keys from the dashboard
3. Add keys to `.env`

### 6. Database Setup
```bash
# Run migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Create superuser (optional)
uv run python manage.py createsuperuser
```

### 7. Run the Server
```bash
uv run python manage.py runserver
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Interactive API Docs
Visit `http://localhost:8000/api/docs` for the auto-generated OpenAPI documentation.

### Base URL
```
http://localhost:8000/api
```

---

## 🔐 Authentication Endpoints

### 1. Initiate Google Sign-In
```http
GET /auth/google
```

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```

### 2. Google OAuth Callback
```http
GET /auth/google/callback?code={code}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "wallet_number": "1234567890123",
    "profile_picture": "https://..."
  }
}
```

---

## 🔑 API Key Management

### 1. Create API Key
```http
POST /keys/create
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "name": "wallet-service",
  "permissions": ["deposit", "transfer", "read"],
  "expiry": "1M"
}
```

**Expiry Options:** `1H` (hour), `1D` (day), `1M` (month), `1Y` (year)

**Response:**
```json
{
  "api_key": "sk_live_abc123xyz...",
  "expires_at": "2025-01-10T12:00:00Z",
  "name": "wallet-service",
  "permissions": ["deposit", "transfer", "read"]
}
```

⚠️ **Important:** The API key is only shown once. Store it securely!

### 2. List API Keys
```http
GET /keys/list
Authorization: Bearer {jwt_token}
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "wallet-service",
    "prefix": "sk_live_abc1",
    "permissions": ["deposit", "transfer", "read"],
    "expires_at": "2025-01-10T12:00:00Z",
    "is_revoked": false,
    "is_expired": false,
    "is_active": true,
    "created_at": "2024-12-10T12:00:00Z",
    "last_used_at": "2024-12-10T14:30:00Z"
  }
]
```

### 3. Revoke API Key
```http
POST /keys/revoke
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "key_id": 1
}
```

**Response:**
```json
{
  "message": "API key revoked successfully"
}
```

### 4. Rollover Expired API Key
```http
POST /keys/rollover
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "expired_key_id": "123",
  "expiry": "1M"
}
```

**Response:**
```json
{
  "api_key": "sk_live_new123xyz...",
  "expires_at": "2025-02-10T12:00:00Z",
  "name": "wallet-service",
  "permissions": ["deposit", "transfer", "read"]
}
```

---

## 💰 Wallet Endpoints

### Authentication Options
All wallet endpoints support two authentication methods:
- **JWT:** `Authorization: Bearer {token}`
- **API Key:** `x-api-key: {api_key}`

### 1. Initiate Deposit
```http
POST /wallet/deposit
Authorization: Bearer {jwt_token}
# OR
x-api-key: {api_key_with_deposit_permission}
Content-Type: application/json

{
  "amount": 500000
}
```

💡 **Note:** Amount is in **kobo** (1 NGN = 100 kobo). So 500000 kobo = 5000 NGN.

**Response:**
```json
{
  "reference": "TXN-ABC123XYZ456",
  "authorization_url": "https://checkout.paystack.com/...",
  "amount": 5000.00
}
```

**Flow:**
1. Call this endpoint to get payment link
2. Redirect user to `authorization_url`
3. User completes payment on Paystack
4. Paystack sends webhook to your server
5. Wallet is automatically credited

### 2. Check Deposit Status
```http
GET /wallet/deposit/{reference}/status
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "reference": "TXN-ABC123XYZ456",
  "status": "success",
  "amount": 5000.00
}
```

**Status Values:** `pending`, `success`, `failed`

⚠️ This endpoint does NOT credit the wallet. Only the webhook credits wallets.

### 3. Get Wallet Balance
```http
GET /wallet/balance
Authorization: Bearer {jwt_token}
# OR
x-api-key: {api_key_with_read_permission}
```

**Response:**
```json
{
  "balance": 15000.00
}
```

### 4. Transfer Funds
```http
POST /wallet/transfer
Authorization: Bearer {jwt_token}
# OR
x-api-key: {api_key_with_transfer_permission}
Content-Type: application/json

{
  "wallet_number": "1234567890123",
  "amount": 300000
}
```

💡 **Note:** Amount is in **kobo** (300000 kobo = 3000 NGN).

**Response:**
```json
{
  "status": "success",
  "message": "Transfer completed",
  "reference": "TXN-XYZ789ABC123",
  "amount": 3000.00
}
```

### 5. Transaction History
```http
GET /wallet/transactions
Authorization: Bearer {jwt_token}
# OR
x-api-key: {api_key_with_read_permission}
```

**Response:**
```json
{
  "transactions": [
    {
      "id": 1,
      "type": "deposit",
      "amount": 5000.00,
      "status": "success",
      "reference": "TXN-ABC123",
      "recipient_wallet_number": null,
      "created_at": "2025-12-10T10:00:00Z"
    },
    {
      "id": 2,
      "type": "transfer",
      "amount": 3000.00,
      "status": "success",
      "reference": "TXN-XYZ789",
      "recipient_wallet_number": "1234567890123",
      "created_at": "2025-12-10T11:00:00Z"
    }
  ],
  "count": 2
}
```

---

## 🔔 Webhook Configuration

### Paystack Webhook Setup

#### For Production:
1. Go to Paystack Dashboard → Settings → Webhooks
2. Add your webhook URL: `https://yourdomain.com/api/wallet/paystack/webhook`
3. Paystack will send events to this URL

#### For Local Development (using ngrok):
```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start your Django server
python manage.py runserver

# In another terminal, start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
# Add to Paystack: https://abc123.ngrok-free.app/api/wallet/paystack/webhook
```

### Webhook Endpoint
```http
POST /wallet/paystack/webhook
x-paystack-signature: {signature}
```

This endpoint:
- Validates Paystack signature using your secret key
- Credits wallet on successful payment
- Is idempotent (won't credit twice for same transaction)

---

## 🧪 Testing

### Manual Webhook Testing
For testing without ngrok, you can manually process a pending deposit:

**Create `apps/wallet/management/commands/test_webhook.py`:**
```python
from django.core.management.base import BaseCommand
from apps.wallet.services import WalletService

class Command(BaseCommand):
    help = 'Manually process a pending deposit'

    def add_arguments(self, parser):
        parser.add_argument('reference', type=str)

    def handle(self, *args, **options):
        try:
            txn = WalletService.process_successful_deposit(options['reference'])
            self.stdout.write(self.style.SUCCESS(f'✅ Credited: {txn.amount} NGN'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
```

**Usage:**
```bash
python manage.py test_webhook TXN-ABC123XYZ456
```

### Complete Test Flow
```bash
# 1. Sign in with Google
curl http://localhost:8000/api/auth/google

# 2. Create API Key
curl -X POST http://localhost:8000/api/keys/create \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-key",
    "permissions": ["deposit", "transfer", "read"],
    "expiry": "1M"
  }'

# 3. Initiate Deposit
curl -X POST http://localhost:8000/api/wallet/deposit \
  -H "x-api-key: {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500000}'

# 4. Complete payment at the authorization_url

# 5. Check Balance
curl http://localhost:8000/api/wallet/balance \
  -H "x-api-key: {api_key}"

# 6. Transfer Funds
curl -X POST http://localhost:8000/api/wallet/transfer \
  -H "x-api-key: {api_key}" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_number": "1234567890123",
    "amount": 300000
  }'

# 7. View Transactions
curl http://localhost:8000/api/wallet/transactions \
  -H "x-api-key: {api_key}"
```

---

## 📁 Project Structure

```
wallet_service/
├── manage.py
├── pyproject.toml
├── .env
├── README.md
│
├── config/                      # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── authentication/          # Google OAuth + JWT
│   │   ├── models.py           # UserProfile with wallet_number
│   │   ├── schemas.py
│   │   ├── services.py         # Google OAuth logic
│   │   ├── jwt_utils.py        # JWT token generation
│   │   └── api.py              # Auth endpoints
│   │
│   ├── api_keys/                # API Key management
│   │   ├── models.py           # APIKey model
│   │   ├── schemas.py
│   │   ├── services.py         # Key generation/validation
│   │   ├── utils.py            # Hashing utilities
│   │   ├── permissions.py      # Permission validators
│   │   ├── authentication.py   # Auth backends
│   │   └── api.py              # API key endpoints
│   │
│   ├── wallet/                  # Wallet operations
│   │   ├── models.py           # Wallet, Transaction models
│   │   ├── schemas.py
│   │   ├── services.py         # Business logic
│   │   ├── paystack.py         # Paystack integration
│   │   ├── webhook.py          # Webhook validation
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── api.py              # Wallet endpoints
│   │
│   └── core/                    # Shared utilities
│       ├── exceptions.py       # APIException
│       └── ...
```

---

## 🔒 Security Considerations

1. **Environment Variables:** Never commit `.env` to version control
2. **API Keys:** Only shown once during creation - store securely
3. **Webhook Signature:** Always validated using Paystack secret key
4. **Atomic Transactions:** Database transactions ensure consistency
5. **Idempotent Webhooks:** Duplicate events won't credit wallet twice
6. **Permission Checks:** API keys restricted by assigned permissions
7. **Balance Validation:** Transfers blocked if insufficient balance
8. **Key Expiration:** Expired keys automatically rejected

---

## 🐛 Common Issues

### Issue: "Invalid or expired token"
**Solution:** Refresh your JWT token using the refresh endpoint or sign in again.

### Issue: Webhook signature validation fails
**Solution:** Ensure you're using `PAYSTACK_SECRET_KEY` (not a separate webhook secret).

### Issue: "Maximum of 5 active API keys allowed"
**Solution:** Revoke unused API keys before creating new ones.

### Issue: "Insufficient balance" on transfer
**Solution:** Deposit more funds or reduce transfer amount.

### Issue: Can't find wallet number
**Solution:** Wallet number is auto-generated during user creation. Check user profile or `/wallet/balance` response.

---

## 🚀 Deployment

### Environment Variables
Update `.env` for production:
```bash
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
SECRET_KEY=strong-random-secret-key
PAYSTACK_SECRET_KEY=sk_live_xxxxx  # Use live keys
```

### Database
Use PostgreSQL in production:
```bash
DB_NAME=wallet_production
DB_USER=wallet_user
DB_PASSWORD=strong-password
DB_HOST=db.example.com
```

### Webhook URL
Update Paystack webhook URL to production domain:
```
https://yourdomain.com/api/wallet/paystack/webhook
```

---

## 📝 License

MIT License

---

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📧 Support

For issues and questions, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ using Django, Django Ninja, and Paystack**
