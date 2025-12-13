#!/bin/bash

# Umoja Farmer Connect - Quick Run Script

echo "🌱 Starting Umoja Farmer Connect..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if ! python3 -c "import django" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install django pillow
fi

# Run migrations
echo "🗄️  Running database migrations..."
python3 manage.py migrate

# Start server
echo ""
echo "✅ Starting development server..."
echo "🌐 Open your browser at: http://127.0.0.1:8000/"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""
python3 manage.py runserver

