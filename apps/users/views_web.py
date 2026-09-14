"""Registro web por sesión. Login/logout usa django.contrib.auth (JWT sigue para API)."""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
    def clean(self):
        d = super().clean()
        if d.get('password') != d.get('password_confirm'):
            raise forms.ValidationError('Passwords no coinciden.')
        return d


def register_view(request):
    if request.user.is_authenticated: return redirect('/')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            u = User.objects.create_user(email=form.cleaned_data['email'], password=form.cleaned_data['password'],
                                         first_name=form.cleaned_data.get('first_name', ''), last_name=form.cleaned_data.get('last_name', ''))
            login(request, u)
            return redirect('/')
    else: form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})
