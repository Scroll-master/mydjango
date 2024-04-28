from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from .utils import get_priority, can_override
# Create your models here.

class User(AbstractUser):
    role = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_groups",  # Уникальное имя для обратной связи
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_permissions",  # Уникальное имя для обратной связи
        related_query_name="user",
    )

    def set_password(self, password):
        super().set_password(password)

    def check_password(self, password):
        return super().check_password(password)
    
    
    
class Media(models.Model):
    title = models.CharField(max_length=255, null=False)
    file = models.FileField(upload_to='videos/', null=True, blank=True)  # Указывает на подпапку в MEDIA_ROOT
    created_at = models.DateTimeField(default=timezone.now)
    duration = models.CharField(max_length=8, blank=True, null=True)  # Длительность файла, если применимо
    tags = models.CharField(max_length=255, blank=True, null=True)  # Теги для поиска и категоризации
    status = models.CharField(max_length=50, default='Активен')  # Статус файла, например 'Активен', 'Архивирован'

    def __str__(self):
        return self.title
    
    
class Schedule(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    type = models.CharField(max_length=50)  # Например, 'периодическое', 'исключение', 'специальная дата'
    datetime = models.DateTimeField(null=True)  # Обновлено для хранения даты и времени специального расписания

    def __str__(self):
        return self.name    
    
    
class Event(models.Model):
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE)
    media = models.ForeignKey('Media', on_delete=models.CASCADE, related_name='events')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"Event from {self.start_time} to {self.end_time} related to {self.media.title}"    
    
    
class Node(models.Model):
    name = models.CharField(max_length=128, null=False)
    ip_address = models.CharField(max_length=15, null=False)
    location = models.CharField(max_length=128, blank=True)  # `blank=True` позволяет полю быть пустым в формах
    status = models.BooleanField(default=True)
    group = models.ForeignKey('NodeGroup', on_delete=models.SET_NULL, null=True, related_name='nodes')

    def __str__(self):
        return f"{self.name} ({self.ip_address})"    
    

class NodeGroup(models.Model):
    name = models.CharField(max_length=128, null=False)
    events = models.ManyToManyField('Event', through='NodeGroupEvent', related_name='node_groups')
    # Предполагается, что связи с events и nodes уже определены в соответствующих моделях

    def __str__(self):
        return self.name

    @property
    def active_schedule_type(self):
        now = timezone.now()
        print(f"Checking active schedule type for NodeGroup {self.name} at {now}")

        # Собираем все активные события в текущий момент времени
        active_events = [event for event in self.events.all() if event.start_time <= now <= event.end_time]

        if not active_events:
            print("No active events found for this NodeGroup at the current time.")
            return None
        
        if len(active_events) == 1:
            only_event = active_events[0]
            print(f"Active event found: Event ID {only_event.id} with schedule type {only_event.schedule.type}")
            return only_event.schedule.type
        
        highest_priority_event = max(active_events, key=lambda event: get_priority(event.schedule.type))

        for event in active_events:
            if event.id != highest_priority_event.id and can_override(highest_priority_event.schedule.type, event.schedule.type):
                print(f"Active event found: Event ID {highest_priority_event.id} with schedule type {highest_priority_event.schedule.type}")
                return highest_priority_event.schedule.type

        print(f"Event with ID {highest_priority_event.id} does not have a higher priority to override other active events.")
        return None    
    
    
class NodeGroupEvent(models.Model):
    node_group = models.ForeignKey(NodeGroup, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        db_table = 'nodegroup_event'  # Это указывает Django использовать конкретное имя таблицы

    def __str__(self):
        return f"{self.node_group.name} - {self.event.title}"
    