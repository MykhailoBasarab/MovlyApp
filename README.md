# Платформа вивчення іноземних мов з елементами ШІ

Дипломний проект - система для вивчення іноземних мов з інтеграцією штучного інтелекту на Django.

## Особливості

- 🎓 **Курси та уроки** - Структурована система навчання
- 📝 **IELTS-подібні тести** - Тести з секціями Listening, Reading, Writing, Speaking
- 🤖 **AI інтеграція** - Генерація вправ, перевірка відповідей, відгуки через OpenAI
- 🔊 **Аудіювання** - Генерація аудіо через AI Text-to-Speech
- 📊 **Аналітика** - Відстеження прогресу та статистики
- 🌍 **5 мов** - English, Deutsch, Français, Español, Italiano
- 💾 **Дві БД** - Основна база даних + окрема для аналітики
- 🎨 **Django Templates** - Frontend інтегровано в Django

## Структура проекту

```
.
├── backend/              # Django проект
│   ├── language_learning/   # Головний проект
│   ├── courses/             # Додаток курсів
│   ├── users/               # Додаток користувачів
│   ├── tests/               # Додаток тестів
│   ├── ai_services/         # AI сервіси
│   ├── templates/           # Django шаблони
│   ├── static/              # Статичні файли (CSS, JS)
│   ├── manage.py            # Django management
│   └── requirements.txt     # Python залежності
├── frontend/            # Опціональна папка для вихідних файлів
└── README.md            # Цей файл
```

## Швидкий старт

### Backend

1. Перейдіть в папку backend:
```bash
cd backend
```

2. Створіть віртуальне середовище:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# або
source venv/bin/activate  # Linux/Mac
```

3. Встановіть залежності:
```bash
pip install -r requirements.txt
```

4. Створіть файл `.env` (скопіюйте з `.env.example` якщо є):
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=language_learning
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
OPENAI_API_KEY=your-openai-api-key
```

5. Виконайте міграції:
```bash
python manage.py makemigrations
python manage.py migrate --database=default
python manage.py migrate --database=analytics
```

6. Створіть суперкористувача:
```bash
python manage.py createsuperuser
```

7. Запустіть сервер:
```bash
python manage.py runserver
```

8. Відкрийте браузер: `http://localhost:8000`

## Технології

### Backend
- Django 4.2
- Django REST Framework
- PostgreSQL (або SQLite для розробки)
- OpenAI API
- Celery + Redis (для асинхронних задач)

### Frontend
- Django Templates
- Vanilla JavaScript
- CSS3

## Документація

Детальна документація доступна в:
- `backend/README.md` - Документація backend
- `frontend/README.md` - Інформація про frontend структуру

## Ліцензія

Дипломний проект
