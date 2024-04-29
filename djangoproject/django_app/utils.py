
import os


def get_priority(schedule_type):
    priorities = {
        'исключение': 3,
        'специальная дата': 2,
        'повседневное': 1
    }
    return priorities.get(schedule_type, 0)  # Возвращаем 0 для неизвестных типов

def can_override(event_type, other_event_type):
    overriding_rules = {
        'исключение': ['повседневное', 'специальная дата', 'исключение'],
        'специальная дата': ['повседневное'],
        'повседневное': []
    }
    return other_event_type in overriding_rules[event_type]

def get_saved_presets():
    """Получает список сохраненных пресетов из папки сохранений."""
    # Получаем базовую директорию проекта
    from django.conf import settings

    save_json_dir = os.path.join(settings.BASE_DIR, 'django_app', 'static', 'SaveJson')
    
    # Проверяем, существует ли директория
    if not os.path.exists(save_json_dir):
        return []

    # Возвращаем список всех JSON файлов в директории
    saved_presets = [f for f in os.listdir(save_json_dir) if f.endswith('.json')]
    return saved_presets



