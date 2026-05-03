from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from users.models import CustomUser, Notification
from .models import Thread, Message
from django.utils import timezone

@login_required
def matchmaking_view(request):
    """Знайти користувачів або виконати пошук"""
    user = request.user
    query = request.GET.get('q', '')
    
    if query:
        partners = CustomUser.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query)
        ).exclude(id=user.id)[:20]
    else:
        p_query = Q(native_language=user.learning_language, learning_language=user.native_language)
        p_query |= Q(native_language=user.learning_language)
        partners = CustomUser.objects.filter(p_query).exclude(id=user.id).distinct()
        
        if partners.count() < 3:
            recent_ids = CustomUser.objects.exclude(id=user.id).order_by('-date_joined').values_list('id', flat=True)[:10]
            partners = CustomUser.objects.filter(Q(id__in=list(recent_ids)) | p_query).exclude(id=user.id).distinct()

    return render(request, 'chat/matchmaking.html', {'partners': partners, 'query': query})

@login_required
def thread_list_view(request):
    """Список активних чатів"""
    threads = Thread.objects.filter(
        Q(first_user=request.user) | Q(second_user=request.user)
    ).order_by('-updated_at')
    
    for thread in threads:
        thread.last_message = thread.messages.last()
        thread.unread_count = thread.messages.filter(is_read=False).exclude(sender=request.user).count()
        thread.other_user = thread.second_user if thread.first_user == request.user else thread.first_user

    return render(request, 'chat/inbox.html', {'threads': threads})

@login_required
def chat_detail_view(request, pk):
    """Вікно чату"""
    other_user = get_object_or_404(CustomUser, pk=pk)
    thread = Thread.objects.filter(
        (Q(first_user=request.user) & Q(second_user=other_user)) |
        (Q(first_user=other_user) & Q(second_user=request.user))
    ).first()
    
    if not thread:
        users = sorted([request.user.id, other_user.id])
        thread = Thread.objects.create(
            first_user=CustomUser.objects.get(id=users[0]), 
            second_user=CustomUser.objects.get(id=users[1])
        )

    messages = thread.messages.all()
    messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    return render(request, 'chat/detail.html', {
        'thread': thread,
        'other_user': other_user,
        'chat_messages': messages
    })

@login_required
def send_message_ajax(request, pk):
    """Відправка повідомлення (текст, фото або голос)"""
    if request.method == 'POST':
        thread = get_object_or_404(Thread, pk=pk)
        text = request.POST.get('text', '').strip()
        image = request.FILES.get('image')
        audio = request.FILES.get('audio')
        
        if text or image or audio:
            msg = Message.objects.create(
                thread=thread, 
                sender=request.user, 
                text=text,
                image=image,
                audio=audio
            )
            thread.save() # Оновлюємо updated_at у thread
            
            return JsonResponse({
                'status': 'success', 
                'id': msg.id,
                'sender_id': msg.sender.id,
                'text': msg.text,
                'image_url': msg.image.url if msg.image else None,
                'audio_url': msg.audio.url if msg.audio else None,
                'created_at': msg.created_at.strftime('%H:%M')
            })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_messages_ajax(request, pk):
    """Отримати нові повідомлення"""
    thread = get_object_or_404(Thread, pk=pk)
    last_id = request.GET.get('last_id')
    
    messages = thread.messages.all()
    if last_id:
        messages = messages.filter(id__gt=last_id)
    
    # Позначаємо як прочитані
    messages.exclude(sender=request.user).update(is_read=True)
    
    data = []
    for m in messages:
        data.append({
            'id': m.id,
            'text': m.text,
            'image_url': m.image.url if m.image else None,
            'audio_url': m.audio.url if m.audio else None,
            'sender_id': m.sender.id,
            'sender_name': m.sender.username,
            'is_own': m.sender == request.user,
            'created_at': m.created_at.strftime('%H:%M')
        })
    return JsonResponse({'messages': data})

@login_required
def delete_message_ajax(request, pk):
    msg = get_object_or_404(Message, pk=pk, sender=request.user)
    msg.delete()
    return JsonResponse({'status': 'success'})

@login_required
def edit_message_ajax(request, pk):
    if request.method == 'POST':
        msg = get_object_or_404(Message, pk=pk, sender=request.user)
        text = request.POST.get('text', '').strip()
        if text:
            msg.text = text
            msg.save()
            return JsonResponse({'status': 'success', 'text': msg.text})
    return JsonResponse({'status': 'error'}, status=400)
