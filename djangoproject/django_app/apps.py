from django.apps import AppConfig


class DjangoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_app'

    def ready(self):
        # Импортируем функцию запуска планировщика задач
        from .tasks import start_scheduler
        # Вызываем функцию для запуска планировщика
        start_scheduler()