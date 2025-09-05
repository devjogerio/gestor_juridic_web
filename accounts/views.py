from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from .forms import CustomUserCreationForm, CustomAuthenticationForm


@csrf_protect
def login_view(request):
    """
    View para login de usuários
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                return redirect('core:dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    View para realizar logout do usuário
    """
    logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('accounts:login')


@csrf_protect
def register_view(request):
    """
    View para registro de novos usuários
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada para {username}! Você já pode fazer login.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Erro ao criar conta. Verifique os dados informados.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    """
    View para exibir perfil do usuário
    """
    return render(request, 'accounts/profile.html', {'user': request.user})
