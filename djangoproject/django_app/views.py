from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, HttpRequest
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Node, Schedule, Event, Media, NodeGroup, NodeGroupEvent
from .forms import MediaForm, NodeGroupForm  # Предполагаем, что у нас есть форма для медиа
from django.contrib.auth.decorators import login_required
import os
import re
import requests
from django.conf import settings
from moviepy.editor import VideoFileClip, AudioFileClip
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from datetime import datetime, timedelta
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied
from .utils import get_priority, can_override, get_saved_presets
from django.core.files.base import ContentFile
from django.db.models import Q
from django.db import transaction
from .services import export_data_to_json, import_data_from_json
from datetime import timedelta
# Create your views here.
def hello_world(request):
    return HttpResponse("Hello, world!")

def update_nodegroup_members(nodegroup, selected_node_ids, selected_event_ids):
    """Обновляет состав нодов и событий в группе."""

    # Обновляем ноды в группе
    nodes = Node.objects.filter(id__in=selected_node_ids)
    nodegroup.nodes.set(nodes)

    # Обновляем события в группе
    events = Event.objects.filter(id__in=selected_event_ids)
    nodegroup.events.set(events)


@require_POST
@login_required
@csrf_exempt  # Отключаем CSRF для примера, в продакшене лучше использовать токены CSRF
def update_status(request):
    data = request.POST
    ip_address = data.get('ip_address')
    status = data.get('status')
    node = Node.objects.filter(ip_address=ip_address).first()

    if node:
        node.status = status
        node.save()
        return JsonResponse({'success': True, 'message': 'Status updated'})

    return JsonResponse({'success': False, 'message': 'Node not found'}, status=404)


@login_required
@require_http_methods(["GET"])
def get_nodes_status(request):
    nodes = Node.objects.all()  # Получаем все ноды из базы данных
    node_data = [{
        'ip_address': node.ip_address,
        'status': node.status,
        'group_name': node.group.name if node.group else 'No group',  # Указываем группу, если она есть
        'location': node.location
    } for node in nodes]
    return JsonResponse(node_data, safe=False)  # Возвращаем данные в формате JSON


@login_required
@require_http_methods(["GET"])
def node_statuses(request):
    # Получаем ноды, которые включены в группы
    nodes = Node.objects.exclude(group__isnull=True)
    statuses = [{
        'ip_address': node.ip_address,
        'status': node.status,
        'group': node.group.name if node.group else 'No group',
        'location': node.location  # Добавляем расположение ноды
    } for node in nodes]
    return JsonResponse(statuses, safe=False)  # Возвращаем данные в формате JSON


def my_view(request):
    # Добавление различных сообщений
    messages.success(request, 'Это успех!')
    messages.info(request, 'Это информация.')
    messages.warning(request, 'Это предупреждение!')
    messages.error(request, 'Это ошибка!')

    # Отрисовка страницы index.html с возможными сообщениями
    return render(request, 'index.html', {})




def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Вы успешно вошли в систему!')
            
            # Проверка роли пользователя и перенаправление на соответствующую страницу
            if user.role == 'master':
                return redirect(reverse('super_admin_page'))
            elif user.role == 'admin':
                return redirect(reverse('admin_page'))
            else:
                return redirect(reverse('index'))  # Или другая страница по умолчанию
        else:
            messages.error(request, 'Неправильное имя пользователя или пароль')
            return redirect(reverse('login'))
    
    return render(request, 'django_app/login.html')



def custom_permission_denied_view(request, exception):
    return render(request, 'django_app/unauthorized.html', status=403)

def logout_view(request):
    logout(request)
    messages.add_message(request, messages.SUCCESS, 'Вы успешно вышли из системы.')
    return redirect('hello_world')  # Перенаправление на главную страницу




@login_required
def super_admin_page(request):
    if request.user.role != 'master':  # Проверяем роль пользователя
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Перенаправляем на главную страницу или страницу входа

    # Получаем данные из базы данных
    schedules = Schedule.objects.all()
    events = Event.objects.all()
    media_files = Media.objects.all()

    # Передаем данные в шаблон
    return render(request, 'super_admin.html', {
        'schedules': schedules,
        'events': events,
        'media_files': media_files
    })



@login_required
def new_schedule(request):
    if request.user.role != 'master':  # предполагается, что у модели пользователя есть поле role
        messages.error(request, "Доступ запрещен")
        return redirect('index')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        schedule_type = request.POST.get('type')
        datetime_str = request.POST.get('datetime') if schedule_type == 'специальная дата' else None
        
        existing_schedule = Schedule.objects.filter(name=name).first()
        if existing_schedule:
            messages.error(request, 'Расписание с таким названием уже существует.')
            return render(request, 'edit_schedule.html', {'schedule': None})

        new_schedule = Schedule(name=name, description=description, type=schedule_type)

        if schedule_type == 'специальная дата' and datetime_str:
            try:
                new_schedule.datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                messages.error(request, 'Неверный формат даты и времени. Используйте формат ГГГГ-ММ-ДД ЧЧ:ММ.')
                return render(request, 'edit_schedule.html', {'schedule': None})

        new_schedule.save()
        messages.success(request, 'Новое расписание создано.')
        return redirect('super_admin_page')

    return render(request, 'edit_schedule.html', {'schedule': None})



@login_required
def edit_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')
    
   

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        schedule_type = request.POST.get('type')
        datetime_str = request.POST.get('datetime') if schedule_type == 'специальная дата' else None

        existing_schedule = Schedule.objects.exclude(id=schedule_id).filter(name=name).first()
        if existing_schedule:
            messages.error(request, 'Расписание с таким названием уже существует.')
            return render(request, 'edit_schedule.html', {'schedule': schedule})
        
        schedule.name = name
        schedule.description = description
        schedule.type = schedule_type

        if schedule_type == 'специальная дата' and datetime_str:
            try:
                schedule.datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                messages.error(request, 'Неверный формат даты и времени.')
                return render(request, 'edit_schedule.html', {'schedule': schedule})

        schedule.save()
        messages.success(request, 'Расписание успешно обновлено.')
        return redirect('super_admin_page')

    return render(request, 'edit_schedule.html', {'schedule': schedule})


@login_required
@require_POST  # Обрабатываем только POST-запросы
def delete_schedule(request, schedule_id):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Перенаправляем на страницу ошибки или главную

    schedule = get_object_or_404(Schedule, pk=schedule_id)
    if schedule.events.all():  # Проверяем, связано ли расписание с какими-либо событиями
        messages.error(request, 'Расписание используется в одном или нескольких событиях и не может быть удалено. Пожалуйста, удалите связанные события перед удалением расписания.')
        return redirect('super_admin_page')

    schedule.delete()  # Удаляем расписание
    messages.success(request, 'Расписание успешно удалено.')
    return redirect('super_admin_page')



@login_required
@require_http_methods(["GET", "POST"])
def new_event(request):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Или другую страницу ошибки

    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        media_id = request.POST.get('media_id')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        start_datetime = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        end_datetime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')

        schedule = get_object_or_404(Schedule, pk=schedule_id)

        current_type = schedule.type
        current_priority = get_priority(current_type)

        # Проверка на перекрытие времени с другими событиями
        overlapping_events = Event.objects.filter(end_time__gt=start_datetime, start_time__lt=end_datetime)

        for event in overlapping_events:
            # Проверяем, может ли текущее событие перекрыть существующее
            if get_priority(event.schedule.type) >= current_priority and not can_override(current_type, event.schedule.type):
                messages.error(request, f'Выбранное время перекрывается с событием ID {event.id}, которое не может быть перекрыто.')
                return redirect('new_event')  # URL-имя для создания нового события

        # Если нет перекрытия, создаем новое событие
        new_event = Event(schedule_id=schedule_id, media_id=media_id, start_time=start_datetime, end_time=end_datetime)
        new_event.save()
        messages.success(request, 'Новое событие успешно создано.')
        return redirect('super_admin_page')  # URL-имя для административной страницы

    else:
        schedules = Schedule.objects.all()
        media_files = Media.objects.all()
        return render(request, 'edit_event.html', {'event': None, 'schedules': schedules, 'media_files': media_files})
    
    
    

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    schedules = Schedule.objects.all()
    media_files = Media.objects.all()

    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Имя маршрута к странице администратора

    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        media_id = request.POST.get('media_id')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        start_datetime = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        end_datetime = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
        schedule = Schedule.objects.get(pk=schedule_id)

        # Проверка на перекрытие времени с другими событиями
        overlapping_events = Event.objects.exclude(id=event_id).filter(
            schedule_id=schedule_id,
            start_time__lt=end_datetime,
            end_time__gt=start_datetime
        )

        for ev in overlapping_events:
            if get_priority(ev.schedule.type) >= get_priority(schedule.type) and not can_override(schedule.type, ev.schedule.type):
                messages.error(request, f'Выбранное время перекрывается с событием ID {ev.id}, которое не может быть перекрыто.')
                return redirect('edit_event', event_id=event_id)  # Указываем имя маршрута и параметры

        # Обновление данных события
        event.schedule_id = schedule_id
        event.media_id = media_id
        event.start_time = start_datetime
        event.end_time = end_datetime
        event.save()

        messages.success(request, 'Событие успешно обновлено.')
        return redirect('super_admin_page')

    return render(request, 'edit_event.html', {
        'event': event,
        'schedules': schedules,
        'media_files': media_files
    })    



@login_required
@require_POST  # Обеспечиваем обработку только POST-запросов
def delete_event(request, event_id):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Используйте имя URL для перенаправления

    event = get_object_or_404(Event, pk=event_id)

    # Проверяем, связано ли событие с какими-либо группами нодов
    if event.node_groups.exists():  # Проверяем, есть ли связанные группы
        messages.error(request, 'Событие не может быть удалено, так как оно является частью одной или нескольких групп нодов.')
        return redirect('super_admin_page')  # Имя маршрута на страницу администратора

    event.delete()
    messages.success(request, 'Событие успешно удалено.')
    return redirect('super_admin_page')  # Имя маршрута на страницу администратора


@login_required
def media_player(request):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('some_other_view_name')  # Перенаправляем на другую страницу, возможно на главную или страницу ошибки

    media_files = Media.objects.all()  # Получаем список всех медиафайлов из базы данных
    return render(request, 'media_player.html', {'media_files': media_files})





def new_media(request):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')

    if request.method == 'POST':
        form = MediaForm(request.POST, request.FILES)

        if form.is_valid():
            tags = form.cleaned_data['tags']
            file = form.cleaned_data.get('file')

            if file is None:
                messages.error(request, 'Файл не был предоставлен.')
                return render(request, 'edit_media.html', {'form': form})

            filename = file.name

            if filename.endswith(('.mp4', '.avi', '.mp3')):
                filepath = os.path.join(settings.MEDIA_ROOT, filename)
                file_path_for_save = default_storage.save(filepath, ContentFile(file.read()))
                full_file_path = os.path.join(settings.MEDIA_ROOT, file_path_for_save)

                try:
                    if filename.endswith(('.mp4', '.avi')):
                        clip = VideoFileClip(full_file_path)
                    else:
                        clip = AudioFileClip(full_file_path)
                    duration = str(timedelta(seconds=int(clip.duration)))
                except Exception as e:
                    messages.error(request, f'Ошибка при определении длительности файла: {e}')
                    return render(request, 'edit_media.html', {'form': form})

                new_media = Media(title=filename, file_path=full_file_path, duration=duration, tags=tags, status='Активен')
                new_media.save()

                messages.success(request, f'Файл успешно загружен: {filename}')
                return redirect('media_list')
            else:
                messages.error(request, 'Неподдерживаемый формат файла.')
        else:
            messages.error(request, 'Проверьте правильность заполнения формы.')
            return render(request, 'edit_media.html', {'form': form})

    form = MediaForm()
    return render(request, 'edit_media.html', {'form': form})







@login_required
def edit_media(request, media_id):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Перенаправляем на страницу ошибки или главную

    media = get_object_or_404(Media, pk=media_id)
    if request.method == 'POST':
        media.tags = request.POST.get('tags')
        media.save()
        messages.success(request, 'Информация о медиафайле обновлена.')
        return redirect('media_player')
    else:
        return render(request, 'edit_media.html', {'media': media})


@login_required
def delete_media(request, media_id):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Перенаправляем на страницу ошибки или главную

    media = get_object_or_404(Media, pk=media_id)
    if media.events.exists():
        messages.error(request, 'Этот медиафайл используется в одном или нескольких событиях и не может быть удалён.')
        return redirect('media_player')
    else:
        file_path = os.path.join(settings.MEDIA_ROOT, media.file.name)
        try:
            os.remove(file_path)
            media.delete()
            messages.success(request, 'Медиафайл успешно удалён.')
        except OSError as e:
            messages.error(request, f'Ошибка при удалении файла: {e}')
        
        return redirect('media_player')

@login_required
def node_interface(request):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Перенаправляем на начальную страницу или страницу ошибки

    # Заменяем запросы SQLAlchemy запросами Django ORM
    nodes = Node.objects.all()  # Получаем список всех нодов из базы данных
    node_groups = NodeGroup.objects.all()  # Получаем список всех групп нодов
    events = Event.objects.all()  # Получаем список всех событий
    saved_presets = get_saved_presets()  # Функция get_saved_presets() должна быть определена в вашем Django приложении

    # Отображаем шаблон с данными
    return render(request, 'node_interface.html', {
        'nodes': nodes,
        'node_groups': node_groups,
        'events': events,
        'saved_presets': saved_presets
    })
    
    
    
def new_node(request):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('index')  # Перенаправляем на главную или другую страницу

    # Получение всех существующих узлов для отображения на странице
    existing_nodes = Node.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        ip_address = request.POST.get('ip_address')
        location = request.POST.get('location')

        # Проверка уникальности имени и IP-адреса узла
        if Node.objects.filter(name=name).exists():
            messages.error(request, 'Узел с таким именем уже существует.')
            return render(request, 'edit_node.html', {'node': None, 'existing_nodes': existing_nodes})

        if Node.objects.filter(ip_address=ip_address).exists():
            messages.error(request, 'Узел с таким IP-адресом уже существует.')
            return render(request, 'edit_node.html', {'node': None, 'existing_nodes': existing_nodes})

        # Проверка корректности IP-адреса
        if not re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip_address):
            messages.error(request, 'Некорректный формат IP-адреса.')
            return render(request, 'edit_node.html', {'node': None, 'existing_nodes': existing_nodes})

        # Создание и сохранение нового узла
        new_node = Node(name=name, ip_address=ip_address, location=location, status=True)  # По умолчанию статус 'включен'
        new_node.save()

        messages.success(request, 'Новый узел успешно создан.')
        return redirect('node_interface')

    return render(request, 'edit_node.html', {'node': None, 'existing_nodes': existing_nodes})    


@login_required
def edit_node(request, node_id):
    if request.user.role != 'master':
        messages.error(request, "Access denied.")
        return redirect('index')

    node = get_object_or_404(Node, id=node_id)

    existing_nodes = Node.objects.exclude(id=node_id)  # Получаем все узлы, кроме редактируемого

    if request.method == 'POST':
        name = request.POST.get('name')
        ip_address = request.POST.get('ip_address')

        # Проверка на уникальность имени и IP-адреса
        existing_node = existing_nodes.filter(name=name) | existing_nodes.filter(ip_address=ip_address)

        if existing_node.exists():
            messages.error(request, "Another node with the same name or IP address already exists.")
            return render(request, 'edit_node.html', {'node': node, 'existing_nodes': existing_nodes})

        # Проверка корректности IP-адреса
        if not re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip_address):
            messages.error(request, "Invalid IP address format.")
            return render(request, 'edit_node.html', {'node': node, 'existing_nodes': existing_nodes})

        # Обновляем узел
        node.name = name
        node.ip_address = ip_address
        node.location = request.POST.get('location')

        node.save()
        messages.success(request, "Node successfully updated.")
        return redirect('node_interface')

    return render(request, 'edit_node.html', {'node': node, 'existing_nodes': existing_nodes})



@login_required
def delete_node(request, node_id):
    if request.user.role != 'master':
        messages.error(request, "Access denied.")
        return redirect('index')

    node = get_object_or_404(Node, id=node_id)

    if node.group:  # Проверяем, связан ли узел с какой-либо группой
        messages.error(request, "Node is part of a group and cannot be deleted. Remove it from the group first.")
        return redirect('node_interface')

    node.delete()
    messages.success(request, "Node successfully deleted.")
    return redirect('node_interface')


@login_required
def new_nodegroup(request):
    if request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('node_interface')  # Перенаправляем на главную или страницу с интерфейсом

    if request.method == 'POST':
        form = NodeGroupForm(request.POST)
        if form.is_valid():
            nodegroup = form.save(commit=False)
            nodegroup.save()

            # Устанавливаем связанные узлы и события
            nodegroup.nodes.set(form.cleaned_data['node_ids'])
            nodegroup.events.set(form.cleaned_data['event_ids'])

            messages.success(request, 'Группа нодов успешно создана.')
            return redirect('node_interface')

        messages.error(request, 'Не удалось создать группу нодов.')
        return render(request, 'edit_nodegroup.html', {'form': form, 'nodes': Node.objects.all(), 'events': Event.objects.all()})

    # Передаем форму и необходимые данные для создания
    form = NodeGroupForm()
    return render(request, 'edit_nodegroup.html', {'form': form, 'nodes': Node.objects.all(), 'events': Event.objects.all()})



def edit_nodegroup(request: HttpRequest, nodegroup_id: int):
    if not request.user.is_authenticated or request.user.role != 'master':
        messages.error(request, "Доступ запрещен")
        return redirect('node_interface')

    nodegroup = get_object_or_404(NodeGroup, pk=nodegroup_id)

    if request.method == 'POST':
        name = request.POST.get('name').strip()
        selected_node_ids = request.POST.getlist('node_ids')
        selected_event_ids = request.POST.getlist('event_ids')

        if not name:
            messages.error(request, "Название группы не может быть пустым.")
            return redirect('edit_nodegroup', nodegroup_id=nodegroup_id)

        existing_group = NodeGroup.objects.filter(Q(id__ne=nodegroup_id) & Q(name=name)).first()
        if existing_group:
            messages.error(request, 'Группа нодов с таким именем уже существует.')
            return redirect('edit_nodegroup', nodegroup_id=nodegroup_id)

        nodegroup.name = name

        update_nodegroup_members(nodegroup, selected_node_ids, selected_event_ids)

        nodegroup.save()
        messages.success(request, 'Группа нодов успешно обновлена.')
        return redirect('node_interface')

    else:
        available_nodes = Node.objects.filter(Q(group=None) | Q(group=nodegroup))
        all_events = Event.objects.all()

        # Pre-format event dates
        formatted_events = [
            {
                'id': event.id,
                'schedule': event.schedule.name,
                'start_time': event.start_time.strftime('%Y-%m-%d %H:%M'),
                'end_time': event.end_time.strftime('%Y-%m-%d %H:%M')
            }
            for event in all_events
        ]

        return render(
            request,
            'edit_nodegroup.html',
            {
                'nodegroup': nodegroup,
                'nodes': available_nodes,
                'events': formatted_events
            }
        )

    
    
@login_required
@require_POST
def delete_nodegroup(request, nodegroup_id):
    nodegroup = get_object_or_404(NodeGroup, pk=nodegroup_id)

    # Если удаление инициировано процессом импорта
    referer = request.META.get('HTTP_REFERER', '')
    if 'import_preset' in referer:
        # Обнуляем group_id у всех нодов, которые принадлежали группе
        nodegroup.nodes.update(group=None)

        # Удаляем связи из промежуточной таблицы NodeGroupEvent
        NodeGroupEvent.objects.filter(node_group_id=nodegroup_id).delete()

        # Удаляем саму группу
        with transaction.atomic():
            nodegroup.delete()

        messages.success(request, 'Группа нодов успешно удалена через импорт.')
    else:
        # Проверяем, не связаны ли с группой ноды или события
        if nodegroup.events.exists() or nodegroup.nodes.exists():
            event_ids = ", ".join(str(event.id) for event in nodegroup.events.all())
            node_ids = ", ".join(str(node.id) for node in nodegroup.nodes.all())
            messages.error(request, f'Группа {nodegroup.name} связана с событиями: {event_ids} и нодами: {node_ids}.')
        else:
            # Удаляем связи и саму группу
            NodeGroupEvent.objects.filter(node_group_id=nodegroup_id).delete()
            with transaction.atomic():
                nodegroup.delete()

            messages.success(request, 'Группа нодов успешно удалена.')

    return redirect('node_interface')    



@login_required
def export_preset_route(request):
    if not request.user.is_authenticated or request.user.role != 'master':
        return HttpResponseForbidden("Доступ запрещен")

    if request.method == 'POST':
        preset_name = request.POST.get('preset_name')

        # Если пользователь не ввел название пресета, вернем ошибку
        if not preset_name:
            messages.error(request, 'Пожалуйста, введите название пресета.')
            return redirect('export_preset_route')

        # Проверяем, существует ли файл с таким же названием
        json_file_path = os.path.join(settings.BASE_DIR, 'django_app', 'static', 'SaveJson', f'{preset_name}.json')
        if os.path.exists(json_file_path):
            messages.error(request, f'Файл с названием "{preset_name}" уже существует.')
            return redirect('export_preset_route')

        # Вызываем функцию экспорта данных
        export_data_to_json(preset_name)

        messages.success(request, f'Пресет "{preset_name}" успешно создан.')
        return redirect('node_interface')

    # Возвращаем страницу для GET-запроса
    return render(request, 'create_export_preset.html')



def import_preset_route(request):
    if not request.user.has_perm('auth.master'):
        raise PermissionDenied("Доступ запрещен")

    if request.method == 'POST':
        preset_name = request.POST.get('preset_name')
        if preset_name.endswith('.json'):
            preset_name = preset_name[:-5]

        json_file_path = os.path.join(settings.BASE_DIR, 'static', 'SaveJson', f'{preset_name}.json')

        import_data_from_json(json_file_path)

        if NodeGroup.objects.count() > 0:
            messages.success(request, 'Data imported successfully.')
        else:
            messages.error(request, 'Failed to import data.')
        
        return redirect('node_interface')

    return render(request, 'create_export_preset.html')  # Отображение формы для импорта пресета


def delete_preset_route(request):
    if not request.user.has_perm('auth.master'):
        messages.error(request, "Доступ запрещен")
        return redirect('node_interface')

    preset_name = request.POST.get('preset_name')
    file_path = os.path.join(settings.BASE_DIR, 'static', 'SaveJson', preset_name)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            messages.success(request, 'Файл успешно удален.')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении файла: {str(e)}')
    else:
        messages.error(request, 'Файл не найден.')

    return redirect('node_interface')