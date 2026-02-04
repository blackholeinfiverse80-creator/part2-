# Creator Core Deployment Guide

## Step-by-Step Render Deployment

### 1. Go to Render Dashboard
- Visit: https://render.com
- Sign in with GitHub

### 2. Create New Web Service
- Click "New +" → "Web Service"
- Connect GitHub repository: `blackholeinfiverse80-creator/part2-`

### 3. Configure Service Settings
```
Name: creator-core
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: python app.py
```

### 4. Environment Variables
```
FLASK_ENV=production
SQLALCHEMY_DATABASE_URI=sqlite:///instance/context_intelligence.db
```

### 5. Advanced Settings
```
Health Check Path: /history
Auto-Deploy: Yes
```

## API Endpoints

### Generate Content
```
POST /generate
{
  "prompt": "Write a story about AI"
}
```

### Submit Feedback
```
POST /feedback
{
  "generation_id": 1,
  "command": "+2"
}
```

### Get History
```
GET /history
```

## Expected URL
Your Creator Core will be available at:
`https://creator-core.onrender.com`