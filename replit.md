# Smart Expense Splitter - Django Application

## Overview
A Django REST API web application for splitting expenses among friends. Built with Django 5.2.8 and Django REST Framework, using SQLite for data persistence.

## Project Architecture
- **Backend Framework**: Django 5.2.8 with Django REST Framework
- **Database**: SQLite (db.sqlite3)
- **Port**: 5000 (configured for Replit webview)

## Key Features
- **User Authentication**: Email/password login and registration system
- Create and manage expense groups
- Add members to groups
- Track expenses with automatic equal-split calculation
- View balance reports (who owes whom)
- Settlement mapping using greedy algorithm to minimize transactions
- Protected views requiring login for sensitive operations
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
### Authentication
- `GET/POST /api/login/` - User login with email and password
- `GET/POST /api/register/` - User registration
- `GET /api/logout/` - User logout

### Expense Management
- `POST /api/groups/` - Create a new expense group
- `POST /api/groups/<group_id>/members/` - Add a member to a group
- `POST /api/groups/<group_id>/expenses/` - Add an expense to a group
- `GET /api/groups/<group_id>/report/` - Get balance report and settlement mapping

## Recent Changes
- **2025-11-13**: Added email/password authentication system
  - Implemented secure user registration with email and password
  - Created login system with email-based authentication
  - Added protected views requiring login (Add Member, Add Expense, Report)
  - Implemented proper redirect flow preserving destination after login
  - Added security measures: password hashing, CSRF protection, open redirect prevention
  - Updated navigation to show Login/Register for guests, Logout for authenticated users
  - Configured LOGIN_URL and redirect settings

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
- Authentication required for protected views (Add Member, Add Expense, Report)
- Login uses email address instead of username for better UX
- Passwords are hashed using Django's built-in authentication system
- Open redirect protection implemented for secure login redirects
