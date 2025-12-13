# Migration Fix Guide

## Problem
Django is asking how to handle the change from `booking` to `bid` field in Payment model because existing records might have null values.

## Solution Options

### Option 1: Reset Database (Recommended for Development)
If you don't have important data, reset everything:

```bash
# Delete database and migration
rm db.sqlite3
rm umoja/migrations/0003_refactor_to_bid_system.py

# Create fresh migrations
python3 manage.py makemigrations
python3 manage.py migrate

# Create superuser (optional)
python3 manage.py createsuperuser
```

Or use the automated script:
```bash
./fix_migration.sh
```

### Option 2: Answer the Prompt
When Django asks what to do, select:
- **Option 2**: "Ignore for now" - This will create the migration with nullable fields, then you can clean up later

Then run:
```bash
python3 manage.py migrate
```

### Option 3: Manual Fix
If you want to keep existing data:

1. Select **Option 2** (Ignore for now) when prompted
2. The migration will create `bid` as nullable
3. After migration, manually delete old Payment/Review records:
   ```python
   # In Django shell: python3 manage.py shell
   from umoja.models import Payment, Review
   Payment.objects.filter(bid__isnull=True).delete()
   Review.objects.filter(bid__isnull=True).delete()
   ```
4. Then create a new migration to make `bid` non-nullable:
   ```bash
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```

## Recommended Approach
Since this is a complete refactoring from Booking to Bid system, **Option 1 (reset database)** is the cleanest approach. The migration file I created already handles deleting old records, but if you're getting prompts, it's easier to start fresh.

