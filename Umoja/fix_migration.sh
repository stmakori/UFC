#!/bin/bash

# Fix migration issues by resetting database (DEVELOPMENT ONLY!)

echo "⚠️  WARNING: This will DELETE all data in the database!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo "🗑️  Removing old database..."
rm -f db.sqlite3

echo "🗑️  Removing migration files..."
rm -f umoja/migrations/0003_refactor_to_bid_system.py

echo "📦 Creating fresh migrations..."
python3 manage.py makemigrations

echo "🗄️  Running migrations..."
python3 manage.py migrate

echo "✅ Done! Database reset and migrations applied."
echo "💡 You may want to create a superuser: python3 manage.py createsuperuser"

