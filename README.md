# Smart Expense Splitter (Django + SQLite)

## Quick start (on Replit)

1. Install dependencies (Replit will usually run `pip install -r requirements.txt` automatically).
2. Run migrations:

```bash
python manage.py migrate
```

3. (Optional) Create a superuser:

```bash
python manage.py createsuperuser
```

4. Run the development server:

```bash
python manage.py runserver 0.0.0.0:5000
```

## Endpoints (basic)

- `POST /api/groups/` - create group (body: `{ "name": "Goa Trip", "created_by": <user_id> }`)
- `POST /api/groups/<group_id>/members/` - add member (body: `{ "user_id": <user_id> }`)
- `POST /api/groups/<group_id>/expenses/` - add expense (body: `{ "payer": <user_id>, "amount": "900.00", "description": "hotel" }`)
- `GET /api/groups/<group_id>/report/` - get balances + settlement mapping

This starter implements the core split + settlement algorithm (equal split) and returns JSON mapping using a greedy algorithm.
