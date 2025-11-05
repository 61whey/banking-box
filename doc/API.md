### Authentication
- `POST /auth/login` - Client login
- `POST /auth/bank-token` - Bank-to-bank token
- `GET /auth/me` - Current user info

### Accounts (OpenBanking Russia)
- `GET /accounts` - List accounts
- `GET /accounts/{id}` - Account details
- `GET /accounts/{id}/balances` - Balance information
- `GET /accounts/{id}/transactions` - Transaction history

### Consents
- `POST /account-consents/request` - Request consent
- `GET /account-consents/my-consents` - List consents
- `POST /account-consents/requests/{id}/approve` - Approve request
- `DELETE /account-consents/{id}` - Revoke consent

### Payments
- `POST /payments` - Create payment
- `GET /payments/{id}` - Payment status

### Products
- `GET /products` - Product catalog
- `POST /product-agreements` - Open deposit/loan/card
- `GET /product-agreements` - List agreements

### Admin
- `GET /admin/stats` - Bank statistics
- `GET /admin/capital` - Capital information
- `GET /admin/transfers` - Interbank transfers

### JWKS
- `GET /.well-known/jwks.json` - Public keys for RS256 verification
