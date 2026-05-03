from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('partners/', views.matchmaking_view, name='partners'),
    path('inbox/', views.thread_list_view, name='inbox'),
    path('thread/<int:pk>/', views.chat_detail_view, name='chat-detail'),
    path('send/<int:pk>/', views.send_message_ajax, name='send-message'),
    path('get-new/<int:pk>/', views.get_messages_ajax, name='get-messages'),
    path('delete/<int:pk>/', views.delete_message_ajax, name='delete-message'),
    path('edit/<int:pk>/', views.edit_message_ajax, name='edit-message'),
]
