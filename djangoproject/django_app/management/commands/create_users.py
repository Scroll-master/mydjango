from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import datetime
from django.utils import timezone


class Command(BaseCommand):
    help = 'Creates initial user records'
    
    def handle(self, *args, **options):
        User = get_user_model()
        # Создание суперпользователя, если он не существует
        if not User.objects.filter(username='Super_Admin').exists():
            super_admin = User(
                username='Super_Admin',
                is_superuser=True,  # В Django есть флаг для суперпользователя
                is_staff=True,     # и флаг для персонала (доступ в админку)
                date_joined=timezone.now(),
                role='master'      # Предполагаем, что у вас есть поле 'role'
            )
            super_admin.set_password('08140215SuPA')
            super_admin.save()

        # Создание администратора, если он не существует
        if not User.objects.filter(username='Admin').exists():
            admin = User(
                username='Admin',
                is_staff=True,     # Админ имеет доступ в админку
                date_joined=timezone.now(),
                role='admin'       # Предполагаем, что у вас есть поле 'role'
            )
            admin.set_password('08152114MiNA')
            admin.save()

        self.stdout.write(self.style.SUCCESS('Successfully created users'))