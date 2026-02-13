import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'language_learning.settings')
django.setup()

from users.models import CustomUser

print("\n--- Список користувачів у БД ---")
users = CustomUser.objects.all()
if not users:
    print("Користувачів поки немає.")
else:
    for user in users:
        print(f"ID: {user.id} | Логін: {user.username} | Email: {user.email} | Дата: {user.date_joined.strftime('%Y-%m-%d %H:%M')}")
print("-------------------------------\n")
