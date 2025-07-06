# Banking & Finance API Documentation

## Overview


## Base URL
```
http://localhost:8000
```

## Authentication

The API uses JWT Bearer token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

## API Endpoints

Base path: `/auth`

- `POST /register` - Register new user
  - Body: `{username, email, password, first_name, last_name}`
- `POST /login` - User login
  - Body: `{username, password}`
- `POST /logout` - Logout current user
- `GET /me` - Get current user profile

### Accounts
Base path: `/accounts`

- `GET /` - List all user accounts
- `POST /` - Create new account
  - Body: `{name, account_type, initial_balance}`
- `GET /{account_id}` - Get account details
- `PUT /{account_id}` - Update account
- `DELETE /{account_id}` - Delete account
- `GET /summary` - Get financial summary across all accounts

### Transactions
Base path: `/transactions`

- `GET /` - List transactions with filters
  - Query params: `account_id, category_id, start_date, end_date, min_amount, max_amount`
- `POST /` - Create new transaction
  - Body: `{account_id, amount, category_id, description, merchant_id}`
- `GET /{transaction_id}` - Get transaction details
- `PUT /{transaction_id}` - Update transaction
- `DELETE /{transaction_id}` - Delete transaction
- `POST /transfer` - Transfer between accounts
  - Body: `{from_account_id, to_account_id, amount, description}`
- `GET /stats` - Get transaction statistics

### Budgets
Base path: `/budgets`

- `GET /` - List user budgets
- `POST /` - Create new budget
  - Body: `{category_id, amount, period, start_date}`
- `GET /{budget_id}` - Get budget with current spending
- `PUT /{budget_id}` - Update budget
- `DELETE /{budget_id}` - Delete budget
- `GET /summary` - Get budget summary with alerts

### Goals
Base path: `/goals`

- `GET /` - List financial goals
- `POST /` - Create new goal
  - Body: `{name, target_amount, target_date, account_id}`
- `GET /{goal_id}` - Get goal details
- `PUT /{goal_id}` - Update goal
- `DELETE /{goal_id}` - Delete goal
- `POST /{goal_id}/contribute` - Add contribution to goal
  - Body: `{amount, note}`
- `GET /summary` - Get goals summary

### Categories
Base path: `/categories`

- `GET /` - List all categories (system + custom)
- `POST /` - Create custom category
  - Body: `{name, type, icon, color}`
- `GET /system` - Get system categories only
- `GET /{category_id}` - Get category details
- `PUT /{category_id}` - Update custom category
- `DELETE /{category_id}` - Delete custom category

### Contacts & Messages
Base paths: `/contacts`, `/conversations`, `/messages`

#### Contacts
- `GET /contacts` - List user contacts
- `POST /contacts` - Send contact request
  - Body: `{recipient_username}`
- `PUT /contacts/{contact_id}/status` - Accept/decline/block contact
  - Body: `{status}`
- `GET /contacts/requests` - Get pending contact requests

#### Conversations
- `GET /conversations` - List user conversations
- `POST /conversations` - Create new conversation
  - Body: `{participant_ids, name}`
- `GET /conversations/{conversation_id}` - Get conversation details

#### Messages
- `POST /messages` - Send message
  - Body: `{conversation_id, content, transaction_id}`
- `GET /messages/{conversation_id}` - Get conversation messages
- `PUT /messages/{message_id}/read` - Mark message as read

### Cards
Base path: `/cards`

- `GET /` - List user cards
- `POST /` - Add new card
  - Body: `{name, last_four, card_type, expiry_month, expiry_year}`
- `GET /{card_id}` - Get card details
- `PUT /{card_id}` - Update card
- `POST /{card_id}/freeze` - Toggle card freeze status
- `DELETE /{card_id}` - Remove card

### Business Features
Base path: `/business`

- `POST /invoices` - Create invoice
  - Body: `{client_name, items, due_date}`
- `GET /invoices` - List invoices
- `GET /invoices/{invoice_id}` - Get invoice details
- `POST /expenses` - Log business expense
  - Body: `{amount, category, description, receipt_url}`
- `GET /expenses` - List business expenses
- `GET /reports/expense` - Generate expense report
  - Query params: `start_date, end_date`

### Subscriptions
Base path: `/subscriptions`

- `GET /` - List detected subscriptions
- `PUT /{subscription_id}` - Update subscription info
  - Body: `{name, amount, frequency}`
- `GET /analysis` - Get subscription cost analysis
- `POST /{subscription_id}/reminder` - Set cancellation reminder
  - Body: `{reminder_date}`

### Savings
Base path: `/savings`

- `POST /rules` - Create savings rule
  - Body: `{type, amount, frequency, source_account_id, target_account_id}`
- `GET /rules` - List savings rules
- `PUT /rules/{rule_id}` - Update savings rule
- `DELETE /rules/{rule_id}` - Delete savings rule
- `POST /roundup` - Configure round-up savings
  - Body: `{enabled, multiplier}`

### Notifications
Base path: `/notifications`

- `GET /` - List user notifications
- `PUT /{notification_id}/read` - Mark notification as read
- `POST /settings` - Update notification preferences
  - Body: `{email_enabled, push_enabled, sms_enabled}`

## Response Format

All successful responses follow this format:
```json
{
  "data": {...},
  "status": "success"
}
```

Error responses:
```json
{
  "detail": "Error message",
  "status": "error"
}
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Mock Data

The API comes pre-populated with:
- 6 users (5 regular + 1 admin)
- Multiple accounts per user
- 90 days of transaction history
- 16 spending categories
- 21 common merchants
- Active budgets and goals
- Contact relationships
- Message conversations

