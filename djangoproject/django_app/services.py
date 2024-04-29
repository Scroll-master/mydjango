import requests
from django.db import transaction
from django.conf import settings
from .models import Node, NodeGroup, Event, NodeGroupEvent
import os
import json
from datetime import datetime

class PlaybackManager:
    def __init__(self):
        self.current_event = None
        self.event_stack = []

    def start_event(self, event_id, media_url):
        if self.current_event:
            self.event_stack.append(self.current_event)
        self.current_event = {'event_id': event_id, 'media_url': media_url}

    def end_current_event(self):
        if self.event_stack:
            self.current_event = self.event_stack.pop()
        else:
            self.current_event = None

    def get_current_media_url(self):
        if self.current_event:
            return self.current_event['media_url']
        return None

    def is_media_ended(self):
        if self.current_event and 'process' in self.current_event:
            ended = self.current_event['process'].poll() is not None
            print(f"Media process ended: {ended}")
            return ended
        print("No media process found")
        return True  # Если процесса нет, считаем медиа завершенным

# Глобальная переменная для управления воспроизведением
playback_manager = PlaybackManager()



def send_media_command(ip_address, media_url):
    try:
        api_endpoint = f"http://{ip_address}:5000/api/play"
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_endpoint, json={"media_url": media_url}, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Successfully sent media command to {ip_address}")
        return response
    except requests.RequestException as e:
        print(f"Failed to send command to {ip_address}: {e}")
        return None
    
    
    

def check_node_status():
    # Получаем только те узлы, которые принадлежат группе
    nodes = Node.objects.exclude(group=None)
    for node in nodes:
        try:
            print(f"Checking status for {node.ip_address}")
            response = requests.get(f'http://{node.ip_address}:5000/api/status', timeout=3)
            print(f"Status for {node.ip_address}: {response.status_code}")
            node.status = response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Failed to check status for {node.ip_address}: {e}")
            node.status = False
        
        # Сохраняем изменения статуса в базу данных
        node.save()

    # Используйте transaction.atomic для обеспечения атомарности операции обновления
    with transaction.atomic():
        for node in nodes:
            node.save()    
            
            
def export_data_to_json(preset_name):
    data = {'node_groups': []}

    # Получаем все группы нодов
    node_groups = NodeGroup.objects.all()

    # Обходим каждую группу нодов
    for group in node_groups:
        group_data = {
            'name': group.name,
            'nodes': [],
            'events': []
        }

        # Добавляем данные о нодах в группе
        for node in group.nodes.all():
            node_data = {
                'id': node.id,
                'name': node.name,
                'ip_address': node.ip_address,
                'location': node.location,
                'status': node.status
            }
            group_data['nodes'].append(node_data)

        # Добавляем данные о событиях, связанных с группой
        for event in group.events.all():
            event_data = {
                'id': event.id,
                'schedule_id': event.schedule_id,
                'media_id': event.media_id,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat()
                # Добавьте любые другие детали о событии, которые вы хотите экспортировать
            }
            group_data['events'].append(event_data)

        data['node_groups'].append(group_data)

    # Путь к файлу JSON
    save_json_dir = os.path.join(settings.BASE_DIR, 'django_app', 'static', 'SaveJson')
    os.makedirs(save_json_dir, exist_ok=True)
    json_file_path = os.path.join(save_json_dir, f'{preset_name}.json')

    # Сохраняем данные в JSON-файл
    with open(json_file_path, 'w') as f:
        json.dump(data, f, indent=4)

    return 'Data exported successfully.'     



def import_data_from_json(json_file_path):
    try:
        # Удаляем существующие группы
        delete_existing_groups()

        with open(json_file_path, 'r') as file:
            data = json.load(file)

        with transaction.atomic():
            for group_data in data['node_groups']:
                group, created = NodeGroup.objects.get_or_create(name=group_data['name'])

                # Обновляем ноды
                nodes = []
                for node_data in group_data['nodes']:
                    node, created_node = Node.objects.get_or_create(
                        name=node_data['name'],
                        defaults={
                            'ip_address': node_data['ip_address'],
                            'location': node_data['location'],
                            'status': node_data.get('status', True)
                        }
                    )

                    if not created_node:
                        # Обновляем существующий нод, если IP адрес изменился
                        node.ip_address = node_data['ip_address']
                        node.location = node_data['location']
                        node.status = node_data.get('status', True)
                        node.save()

                    nodes.append(node)

                group.nodes.set(nodes)

                # Обновляем события
                events = []
                for event_data in group_data['events']:
                    event, created_event = Event.objects.get_or_create(
                        schedule_id=event_data['schedule_id'],
                        media_id=event_data['media_id'],
                        start_time=datetime.strptime(event_data['start_time'], '%Y-%m-%dT%H:%M:%S'),
                        end_time=datetime.strptime(event_data['end_time'], '%Y-%m-%dT%H:%M:%S')
                    )
                    events.append(event)

                group.events.set(events)

                group.save()

    except Exception as e:
        print(f"Ошибка при импорте данных: {e}")     
          
        
def delete_existing_groups():
    """Удаляет все группы нодов и связанные данные."""
    with transaction.atomic():
        # Обнуляем group_id у всех нод, которые принадлежат какой-либо группе
        Node.objects.update(group=None)

        # Удаляем все связи из промежуточной таблицы NodeGroupEvent
        NodeGroupEvent.objects.all().delete()

        # Удаляем все группы нодов
        NodeGroup.objects.all().delete()
        