# Smart Expense Splitter - Django Application

## Overview
A Django REST API web application for splitting expenses among friends. Built with Django 5.2.8 and Django REST Framework, using SQLite for data persistence.

## Project Architecture
- **Backend Framework**: Django 5.2.8 with Django REST Framework
- **Database**: SQLite (db.sqlite3)
- **Port**: 5000 (configured for Replit webview)

## Key Features
- Create and manage expense groups
- Add members to groups
- Track expenses with automatic equal-split calculation
- View balance reports (who owes whom)
- Settlement mapping using greedy algorithm to minimize transactions
- Django admin panel for data management

## Project Structure
```
project/
├── project/           # Django project settings
│   ├── settings.py   # Configuration
│   ├── urls.py       # Main URL routing
│   └── wsgi.py       # WSGI configuration
├── splitter/         # Main application
│   ├── models.py     # Database models (Group, GroupMember, Expense)
│   ├── views.py      # API views and business logic
│   ├── serializers.py # REST Framework serializers
│   ├── urls.py       # App URL routing
│   └── admin.py      # Admin panel configuration
├── manage.py         # Django management script
└── requirements.txt  # Python dependencies
```

## API Endpoints
- `POST /api/groups/` - Create a new expense group
- `POST /api/groups/<group_id>/members/` - Add a member to a group
- `POST /api/groups/<group_id>/expenses/` - Add an expense to a group
- `GET /api/groups/<group_id>/report/` - Get balance report and settlement mapping

## Recent Changes
- **2025-11-13**: Complete application with web UI
  - Created Django project structure
  - Implemented models: Group, GroupMember, Expense
  - Built REST API endpoints with Django REST Framework
  - Implemented equal-split expense calculation
  - Added greedy settlement algorithm for optimal debt resolution
  - Built beautiful, responsive web UI with gradient design
  - Added dynamic user creation and member management
  - Configured CSRF exemptions for seamless API integration
  - Configured for Replit deployment on port 5000

## Database Models
1. **Group**: Expense groups with name and creator
2. **GroupMember**: Many-to-many relationship between groups and users
3. **Expense**: Individual expenses with payer, amount, and description

## Settlement Algorithm
The application uses a greedy algorithm to minimize the number of transactions needed to settle all debts:
1. Calculate net balance for each member (amount paid - fair share)
2. Identify creditors (positive balance) and debtors (negative balance)
3. Match largest creditor with largest debtor iteratively
4. Continue until all debts are settled

## Dependencies
- Django >= 4.2
- djangorestframework

## Development Notes
- Django development server runs on 0.0.0.0:5000
- ALLOWED_HOSTS configured for all hosts (development mode)
- SQLite database for easy setup and portability
- No authentication required for MVP (can be added later)
