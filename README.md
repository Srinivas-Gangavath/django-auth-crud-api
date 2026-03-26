# Django Auth CRUD API

A Django project with authentication and API support.

## 🚀 Features
- User Authentication (Login, Signup)
- OTP Verification (2FA)
- Google OAuth
- CRUD Operations (Web + API)
- Token Authentication

## 🛠 Tech Stack
- Django
- Django REST Framework
- SQLite

## 📦 API Endpoints

- POST /api/login/
- GET /api/items/
- POST /api/items/
- GET /api/items/<id>/
- PUT/PATCH /api/items/<id>/
- DELETE /api/items/<id>/

## ▶️ Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver


🔐 Authentication
Authorization: Token <your_token>