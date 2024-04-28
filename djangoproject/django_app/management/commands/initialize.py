from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

class Command(BaseCommand):
    help = 'Initializes the database and starts the server.'

    def handle(self, *args, **options):
        self.stdout.write("Подключаемся к базе данных...")
        call_command('migrate')  # Выполнение миграций

        self.stdout.write("Добавляем начальные данные в базу...")
        call_command('create_users')
        call_command('update_media', settings.MEDIA_ROOT)

        self.stdout.write("Успешное подключение к базе данных и создание таблиц!")
