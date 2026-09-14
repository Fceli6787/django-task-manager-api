"""Vistas HTML fullstack (Opción A). Reusan ORM + get_visible_tasks del API. JWT intacto."""
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from .models import Task, Category, Tag, Comment, TaskAttachment, TaskHistory
from apps.tasks.views import get_visible_tasks


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'due_date', 'start_date',
                  'category', 'tags', 'assigned_to', 'parent', 'estimated_hours',
                  'is_recurring', 'recurrence_pattern', 'recurrence_end_date']
        widgets = {'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                   'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                   'recurrence_end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['category'].queryset = Category.objects.filter(owner=user)
            self.fields['tags'].queryset = Tag.objects.filter(owner=user)
            self.fields['parent'].queryset = Task.objects.filter(owner=user)
            self.fields['category'].required = False


@login_required
def task_list(request):
    qs = get_visible_tasks(request.user).order_by('-created_at')
    f = request.GET.get('filter', '')
    search, fs, fp = request.GET.get('search', ''), request.GET.get('status', ''), request.GET.get('priority', '')
    if f == 'trash':
        from django.db.models import Q as _Q
        base = Task.all_objects.filter(is_deleted=True)
        if request.user.role == 'admin': qs = base.order_by('-deleted_at')
        elif request.user.role == 'manager':
            team = request.user.team_members.values_list('id', flat=True)
            qs = base.filter(_Q(owner=request.user) | _Q(owner__in=team)).order_by('-deleted_at')
        else: qs = base.filter(owner=request.user).order_by('-deleted_at')
    else:
        if search: qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if fs: qs = qs.filter(status=fs)
        if fp: qs = qs.filter(priority=fp)
    pag = Paginator(qs, 20)
    page = pag.get_page(request.GET.get('page'))
    return render(request, 'web/task_list.html', {
        'tasks': page, 'page_obj': page, 'is_paginated': pag.num_pages > 1,
        'search': search, 'f_status': fs, 'f_priority': fp,
        'status_choices': Task.STATUS_CHOICES, 'priority_choices': Task.PRIORITY_CHOICES,
    })


@login_required
def task_detail(request, pk):
    task = get_object_or_404(get_visible_tasks(request.user), pk=pk)
    return render(request, 'web/task_detail.html', {
        'task': task,
        'comments': task.comments.select_related('author').order_by('created_at')[:100],
        'attachments': task.attachments.all()[:50],
        'history': task.history.select_related('user').order_by('-created_at')[:50],
    })


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            t = form.save(commit=False); t.owner = request.user; t.save()
            form.save_m2m()
            TaskHistory.objects.create(task=t, user=request.user, field_name='task', action='created', new_value=t.title)
            messages.success(request, 'Tarea creada (soft-delete activo).')
            return redirect('web-task-detail', pk=t.id)
    else: form = TaskForm(user=request.user)
    return render(request, 'web/task_form.html', {'form': form, 'mode': 'Nueva'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(get_visible_tasks(request.user), pk=pk)
    if task.owner != request.user and request.user.role not in ('admin', 'manager'):
        messages.error(request, 'Asignados solo lectura (usa Completar).'); return redirect('web-task-detail', pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            old = Task.objects.get(pk=pk).status
            form.save()
            if old != task.status:
                TaskHistory.objects.create(task=task, user=request.user, field_name='status', old_value=old, new_value=task.status, action='updated')
            return redirect('web-task-detail', pk=pk)
    else: form = TaskForm(instance=task, user=request.user)
    return render(request, 'web/task_form.html', {'form': form, 'mode': 'Editar'})


@login_required
def task_delete(request, pk):
    if request.method != 'POST': return redirect('web-task-list')
    task = get_object_or_404(get_visible_tasks(request.user), pk=pk)
    task.delete()
    TaskHistory.objects.create(task=task, user=request.user, field_name='task', action='deleted')
    messages.success(request, 'Borrada (papelera).'); return redirect('web-task-list')


@login_required
def task_complete(request, pk):
    if request.method != 'POST': return redirect('web-task-detail', pk=pk)
    task = get_object_or_404(get_visible_tasks(request.user), pk=pk)
    old = task.status; task.complete()
    TaskHistory.objects.create(task=task, user=request.user, field_name='status', old_value=old, new_value='completed', action='updated')
    return redirect('web-task-detail', pk=pk)


@login_required
def task_comment(request, pk):
    if request.method != 'POST': return redirect('web-task-detail', pk=pk)
    task = get_object_or_404(get_visible_tasks(request.user), pk=pk)
    content = request.POST.get('content', '').strip()
    if content:
        Comment.objects.create(task=task, author=request.user, content=content)
    return redirect('web-task-detail', pk=pk)


@login_required
def task_attach(request, pk):
    if request.method != 'POST': return redirect('web-task-detail', pk=pk)
    task = get_object_or_404(get_visible_tasks(request.user), pk=pk)
    f = request.FILES.get('file')
    if f:
        if f.size > 5 * 1024 * 1024: messages.error(request, 'Máx 5MB.')
        else:
            TaskAttachment.objects.create(task=task, file=f, filename=f.name, file_size=f.size, mime_type=getattr(f, 'content_type', ''), uploaded_by=request.user)
            from django.db.models import F as _F
            Task.objects.filter(pk=task.pk).update(attachments_count=_F('attachments_count') + 1)
    return redirect('web-task-detail', pk=pk)


@login_required
def categories_view(request):
    cats = Category.objects.filter(owner=request.user).order_by('name')
    tags = Tag.objects.filter(owner=request.user).order_by('name')
    for c in cats: c.tasks_count = c.tasks.filter(is_deleted=False).count()
    return render(request, 'web/categories.html', {'categories': cats, 'tags': tags})


@login_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#3498db')
        if name:
            Category.objects.get_or_create(name=name, owner=request.user, defaults={'color': color})
    return redirect('web-categories')


@login_required
def category_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(Category, pk=pk, owner=request.user).delete()
    return redirect('web-categories')


@login_required
def tag_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Tag.objects.get_or_create(name=name, owner=request.user)
    return redirect('web-categories')


@login_required
def tag_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(Tag, pk=pk, owner=request.user).delete()
    return redirect('web-categories')
