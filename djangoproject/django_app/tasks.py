from background_task import background
from .models import NodeGroup, Event
from .services import playback_manager, send_media_command, check_node_status
from .utils import get_priority, can_override
from django.utils import timezone
from django.conf import settings

def check_and_play_media():
    now = timezone.now()
    print(f"Checking for active media to play at {now}")
    node_groups = NodeGroup.objects.all()

    if not node_groups:
        print("No node groups found.")
        return

    for group in node_groups:
        print(f"Checking group {group.name}")
        active_type = group.active_schedule_type()
        if not active_type:
            print(f"No active schedule type for group {group.name} at {now}")
            continue

        active_events = [event for event in group.events.all() if event.schedule.type == active_type and event.start_time <= now <= event.end_time]
        if active_events:
            highest_priority_event = max(active_events, key=lambda event: get_priority(event.schedule.type))
            current_media_url = playback_manager.get_current_media_url()
            new_media_url = highest_priority_event.media.file.url  # Получение URL из FileField

            if current_media_url != new_media_url or playback_manager.is_media_ended():
                playback_manager.start_event(highest_priority_event.id, new_media_url)
                for node in group.nodes.all():
                    print(f"Attempting to send media to {node.ip_address} for event {highest_priority_event.id} with URL: {new_media_url}")
                    response = send_media_command(node.ip_address, new_media_url)
                    if response and response.status_code == 200:
                        print(f"Successfully sent media to {node.ip_address} for event {highest_priority_event.id}")
                    else:
                        print(f"Failed to send media to {node.ip_address} for event {highest_priority_event.id}")
        else:
            if playback_manager.current_event and playback_manager.is_media_ended():
                playback_manager.end_current_event()
                if playback_manager.get_current_media_url():
                    for node in group.nodes.all():
                        send_media_command(node.ip_address, playback_manager.get_current_media_url())
                        
                        
                        



 # Это фоновая задача для проверки и воспроизведения медиа
@background(schedule=60)  # Запускается каждую минуту
def scheduled_check_and_play_media():
    check_and_play_media()

 # Фоновая задача для проверки статуса узлов
@background(schedule=30)  # Запускается каждые 30 секунд
def scheduled_check_node_status():
    check_node_status()            
    
    
def start_scheduler():
    # Планирование фоновых задач
    scheduled_check_and_play_media(repeat=60)  # Повторять каждую минуту
    scheduled_check_node_status(repeat=30)    # Повторять каждые 30 секунд             
                        
                        
                        