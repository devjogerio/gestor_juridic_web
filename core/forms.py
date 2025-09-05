# -*- coding: utf-8 -*-
"""
Formulários para o módulo Core

Este módulo contém os formulários para funcionalidades centrais do sistema.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Configuracao, LogSistema, Backup, Notificacao, PerfilUsuario


class ConfiguracaoForm(forms.ModelForm):
    """
    Formulário para configurações do sistema
    """
    
    class Meta:
        model = Configuracao
        fields = [
            'nome_empresa', 'cnpj', 'endereco', 'telefone', 'email',
            'logo', 'tema', 'idioma', 'fuso_horario', 'moeda',
            'backup_automatico', 'intervalo_backup', 'notificacoes_email',
            'notificacoes_sistema', 'manutencao'
        ]
        widgets = {
            'nome_empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da empresa/escritório'
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00.000.000/0000-00'
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Endereço completo'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 0000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@empresa.com'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'tema': forms.Select(attrs={'class': 'form-control'}),
            'idioma': forms.Select(attrs={'class': 'form-control'}),
            'fuso_horario': forms.Select(attrs={'class': 'form-control'}),
            'moeda': forms.Select(attrs={'class': 'form-control'}),
            'backup_automatico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'intervalo_backup': forms.Select(attrs={'class': 'form-control'}),
            'notificacoes_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificacoes_sistema': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'manutencao': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_cnpj(self):
        """Validação do CNPJ"""
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            # Remover caracteres especiais
            cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
            
            # Verificar se tem 14 dígitos
            if len(cnpj_limpo) != 14:
                raise ValidationError('CNPJ deve ter 14 dígitos.')
            
            # Verificar se não são todos iguais
            if len(set(cnpj_limpo)) == 1:
                raise ValidationError('CNPJ inválido.')
            
            # Formatação padrão
            cnpj_formatado = f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"
            return cnpj_formatado
        
        return cnpj
    
    def clean_telefone(self):
        """Validação do telefone"""
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remover caracteres especiais
            telefone_limpo = ''.join(filter(str.isdigit, telefone))
            
            # Verificar se tem pelo menos 10 dígitos
            if len(telefone_limpo) < 10:
                raise ValidationError('Telefone deve ter pelo menos 10 dígitos.')
            
            # Formatação padrão
            if len(telefone_limpo) == 10:
                telefone_formatado = f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"
            elif len(telefone_limpo) == 11:
                telefone_formatado = f"({telefone_limpo[:2]}) {telefone_limpo[2:7]}-{telefone_limpo[7:]}"
            else:
                telefone_formatado = telefone
            
            return telefone_formatado
        
        return telefone
    
    def clean_logo(self):
        """Validação do arquivo de logo"""
        logo = self.cleaned_data.get('logo')
        if logo:
            # Verificar tamanho do arquivo (máximo 5MB)
            if logo.size > 5 * 1024 * 1024:
                raise ValidationError('O arquivo de logo não pode ser maior que 5MB.')
            
            # Verificar tipo do arquivo
            tipos_permitidos = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if logo.content_type not in tipos_permitidos:
                raise ValidationError('Formato de imagem não suportado. Use JPEG, PNG, GIF ou WebP.')
        
        return logo


class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulário para perfil do usuário
    """
    
    class Meta:
        model = PerfilUsuario
        fields = [
            'telefone', 'endereco', 'data_nascimento', 'cargo',
            'departamento', 'avatar', 'bio', 'tema_preferido',
            'notificacoes_email', 'notificacoes_push'
        ]
        widgets = {
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Endereço completo'
            }),
            'data_nascimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo/Função'
            }),
            'departamento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Departamento/Setor'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Biografia/Descrição'
            }),
            'tema_preferido': forms.Select(attrs={'class': 'form-control'}),
            'notificacoes_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificacoes_push': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_telefone(self):
        """Validação do telefone"""
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remover caracteres especiais
            telefone_limpo = ''.join(filter(str.isdigit, telefone))
            
            # Verificar se tem pelo menos 10 dígitos
            if len(telefone_limpo) < 10:
                raise ValidationError('Telefone deve ter pelo menos 10 dígitos.')
            
            # Formatação padrão
            if len(telefone_limpo) == 10:
                telefone_formatado = f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"
            elif len(telefone_limpo) == 11:
                telefone_formatado = f"({telefone_limpo[:2]}) {telefone_limpo[2:7]}-{telefone_limpo[7:]}"
            else:
                telefone_formatado = telefone
            
            return telefone_formatado
        
        return telefone
    
    def clean_data_nascimento(self):
        """Validação da data de nascimento"""
        data_nascimento = self.cleaned_data.get('data_nascimento')
        if data_nascimento:
            # Verificar se não é no futuro
            if data_nascimento > timezone.now().date():
                raise ValidationError('A data de nascimento não pode ser no futuro.')
            
            # Verificar idade mínima (16 anos)
            idade_minima = timezone.now().date() - timedelta(days=16*365)
            if data_nascimento > idade_minima:
                raise ValidationError('Idade mínima é 16 anos.')
            
            # Verificar idade máxima (120 anos)
            idade_maxima = timezone.now().date() - timedelta(days=120*365)
            if data_nascimento < idade_maxima:
                raise ValidationError('Data de nascimento inválida.')
        
        return data_nascimento
    
    def clean_avatar(self):
        """Validação do avatar"""
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Verificar tamanho do arquivo (máximo 2MB)
            if avatar.size > 2 * 1024 * 1024:
                raise ValidationError('O arquivo de avatar não pode ser maior que 2MB.')
            
            # Verificar tipo do arquivo
            tipos_permitidos = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if avatar.content_type not in tipos_permitidos:
                raise ValidationError('Formato de imagem não suportado. Use JPEG, PNG, GIF ou WebP.')
        
        return avatar


class UsuarioForm(UserChangeForm):
    """
    Formulário para edição de usuário
    """
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active', 'is_staff']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sobrenome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_email(self):
        """Validação do email"""
        email = self.cleaned_data.get('email')
        if email:
            # Verificar duplicidade
            qs = User.objects.filter(email__iexact=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Já existe um usuário com este email.')
        
        return email


class UsuarioCriacaoForm(UserCreationForm):
    """
    Formulário para criação de usuário
    """
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome de usuário'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sobrenome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        """Validação do email"""
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError('Já existe um usuário com este email.')
        return email
    
    def save(self, commit=True):
        """Salvar usuário com email"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class NotificacaoForm(forms.ModelForm):
    """
    Formulário para criação de notificações
    """
    
    class Meta:
        model = Notificacao
        fields = ['titulo', 'mensagem', 'tipo', 'usuario']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da notificação'
            }),
            'mensagem': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mensagem da notificação'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'usuario': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usuario'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['usuario'].required = False
    
    def clean_titulo(self):
        """Validação do título"""
        titulo = self.cleaned_data.get('titulo')
        if titulo:
            titulo = titulo.strip()
            if len(titulo) < 3:
                raise ValidationError('O título deve ter pelo menos 3 caracteres.')
        return titulo
    
    def clean_mensagem(self):
        """Validação da mensagem"""
        mensagem = self.cleaned_data.get('mensagem')
        if mensagem:
            mensagem = mensagem.strip()
            if len(mensagem) < 10:
                raise ValidationError('A mensagem deve ter pelo menos 10 caracteres.')
        return mensagem


class BackupForm(forms.ModelForm):
    """
    Formulário para configuração de backup
    """
    
    class Meta:
        model = Backup
        fields = ['nome', 'descricao', 'tipo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do backup'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do backup'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'})
        }
    
    def clean_nome(self):
        """Validação do nome"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            if len(nome) < 3:
                raise ValidationError('O nome deve ter pelo menos 3 caracteres.')
        return nome


class LogSistemaFiltroForm(forms.Form):
    """
    Formulário para filtros de logs do sistema
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por ação, detalhes...'
        })
    )
    
    nivel = forms.ChoiceField(
        choices=[('', 'Todos os níveis')] + LogSistema.NIVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    usuario = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label='Todos os usuários',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim:
            if data_inicio > data_fim:
                raise ValidationError('A data de início não pode ser posterior à data de fim.')
        
        return cleaned_data