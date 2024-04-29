"""
URL configuration for djangoproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler403
from django.contrib import admin
from django.urls import path, include
from django_app.views import hello_world  # Импортируйте ваше представление
from django_app.views import update_status, get_nodes_status, node_statuses, login_view, custom_permission_denied_view, logout_view, super_admin_page, new_schedule, edit_schedule, delete_schedule, new_event, edit_event, delete_event, media_player, new_media, edit_media, delete_media, node_interface, new_node, edit_node, delete_node, new_nodegroup, edit_nodegroup, delete_nodegroup, import_preset_route, delete_preset_route, export_preset_route

urlpatterns = [
    path('admin/', admin.site.urls),
    path('update_status/', update_status, name='update_status'),
    path('api/nodes', get_nodes_status, name='get_nodes_status'),
    path('node_statuses', node_statuses, name='node_statuses'),
    path('schedule/new/', new_schedule, name='new_schedule'),
    path('schedule/edit/<int:schedule_id>/', edit_schedule, name='edit_schedule'),
    path('schedule/delete/<int:schedule_id>/', delete_schedule, name='delete_schedule'),
    path('event/new/', new_event, name='new_event'),
    path('event/edit/<int:event_id>/', edit_event, name='edit_event'),
    path('event/delete/<int:event_id>/', delete_event, name='delete_event'),
    path('media_player/', media_player, name='media_player'),
    path('node_interface/', node_interface, name='node_interface'),  # Маршрут для интерфейса узлов
    path('node/new/', new_node, name='new_node'),  # Маршрут для создания нового узла
    path('node/edit/<int:node_id>/', edit_node, name='edit_node'),  # Маршрут для редактирования узла
    path('node/delete/<int:node_id>/', delete_node, name='delete_node'),  # Новый маршрут для удаления узла
    path('nodegroup/new/', new_nodegroup, name='new_nodegroup'),
    path('nodegroup/edit/<int:nodegroup_id>/', edit_nodegroup, name='edit_nodegroup'),
    path('nodegroup/delete/<int:nodegroup_id>/', delete_nodegroup, name='delete_nodegroup'),
    path('export_preset', export_preset_route, name='export_preset_route'),
    path('import_preset/', import_preset_route, name='import_preset_route'),
    path('delete_preset/', delete_preset_route, name='delete_preset_route'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('media/new/', new_media, name='new_media'),
    path('media/edit/<int:media_id>/', edit_media, name='edit_media'),
    path('media/delete/<int:media_id>/', delete_media, name='delete_media'),
    path('superadmin/', super_admin_page, name='super_admin_page'),
    path('hello/', hello_world, name='hello_world'),  # Добавьте маршрут к вашему представлению
]

handler403 = custom_permission_denied_view

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)