

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