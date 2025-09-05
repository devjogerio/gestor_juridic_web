# -*- coding: utf-8 -*-
"""
Formulários para o módulo de Agenda

Este módulo contém os formulários para gerenciamento de compromissos e agenda.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Agenda, TipoCompromisso, Participante
from processos.models import Processo
from clientes.models import Cliente


class AgendaForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de compromissos
    """
    
    class Meta:
        model = Agenda
        fields = [
            'titulo', 'descricao', 'data_hora', 'duracao', 'local',
            'tipo_compromisso', 'processo', 'cliente', 'prioridade',
            'status', 'notificar_antecedencia', 'observacoes'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o título do compromisso'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição detalhada do compromisso'
            }),
            'data_hora': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duracao': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duração em minutos',
                'min': '1'
            }),
            'local': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Local do compromisso'
            }),
            'tipo_compromisso': forms.Select(attrs={
                'class': 'form-control'
            }),
            'processo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'prioridade': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notificar_antecedencia': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minutos antes do compromisso',
                'min': '0'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observações adicionais'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa o formulário com configurações específicas"""
        super().__init__(*args, **kwargs)
        
        # Configurar querysets
        self.fields['processo'].queryset = Processo.objects.filter(
            status__in=['ativo', 'em_andamento']
        ).order_by('numero')
        
        self.fields['cliente'].queryset = Cliente.objects.filter(
            ativo=True
        ).order_by('nome')
        
        self.fields['tipo_compromisso'].queryset = TipoCompromisso.objects.filter(
            ativo=True
        ).order_by('nome')
        
        # Campos opcionais
        self.fields['processo'].required = False
        self.fields['cliente'].required = False
        self.fields['duracao'].required = False
        self.fields['local'].required = False
        self.fields['observacoes'].required = False
        self.fields['notificar_antecedencia'].required = False
    
    def clean_titulo(self):
        """Validação do título"""
        titulo = self.cleaned_data.get('titulo')
        if titulo:
            titulo = titulo.strip()
            if len(titulo) < 3:
                raise ValidationError('O título deve ter pelo menos 3 caracteres.')
            if len(titulo) > 200:
                raise ValidationError('O título não pode ter mais de 200 caracteres.')
        return titulo
    
    def clean_data_hora(self):
        """Validação da data e hora"""
        data_hora = self.cleaned_data.get('data_hora')
        if data_hora:
            # Verificar se a data não é no passado (exceto para edição)
            if not self.instance.pk and data_hora < timezone.now():
                raise ValidationError('A data e hora não podem ser no passado.')
            
            # Verificar se não é muito no futuro (mais de 2 anos)
            limite_futuro = timezone.now() + timedelta(days=730)
            if data_hora > limite_futuro:
                raise ValidationError('A data não pode ser mais de 2 anos no futuro.')
        
        return data_hora
    
    def clean_duracao(self):
        """Validação da duração"""
        duracao = self.cleaned_data.get('duracao')
        if duracao is not None:
            if duracao < 1:
                raise ValidationError('A duração deve ser de pelo menos 1 minuto.')
            if duracao > 1440:  # 24 horas
                raise ValidationError('A duração não pode ser maior que 24 horas (1440 minutos).')
        return duracao
    
    def clean_notificar_antecedencia(self):
        """Validação da antecedência de notificação"""
        antecedencia = self.cleaned_data.get('notificar_antecedencia')
        if antecedencia is not None:
            if antecedencia < 0:
                raise ValidationError('A antecedência não pode ser negativa.')
            if antecedencia > 10080:  # 1 semana em minutos
                raise ValidationError('A antecedência não pode ser maior que 1 semana.')
        return antecedencia
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        processo = cleaned_data.get('processo')
        cliente = cleaned_data.get('cliente')
        
        # Pelo menos um deve ser informado (processo ou cliente)
        if not processo and not cliente:
            raise ValidationError(
                'É necessário informar pelo menos um processo ou cliente para o compromisso.'
            )
        
        # Se processo informado, verificar se cliente é compatível
        if processo and cliente:
            if processo.cliente != cliente:
                raise ValidationError(
                    'O cliente selecionado não corresponde ao cliente do processo.'
                )
        
        return cleaned_data


class TipoCompromissoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de tipos de compromisso
    """
    
    class Meta:
        model = TipoCompromisso
        fields = ['nome', 'descricao', 'cor', 'duracao_padrao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do tipo de compromisso'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do tipo de compromisso'
            }),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'duracao_padrao': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duração padrão em minutos',
                'min': '1'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_nome(self):
        """Validação do nome"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            if len(nome) < 2:
                raise ValidationError('O nome deve ter pelo menos 2 caracteres.')
            
            # Verificar duplicidade
            qs = TipoCompromisso.objects.filter(nome__iexact=nome)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Já existe um tipo de compromisso com este nome.')
        
        return nome
    
    def clean_duracao_padrao(self):
        """Validação da duração padrão"""
        duracao = self.cleaned_data.get('duracao_padrao')
        if duracao is not None:
            if duracao < 1:
                raise ValidationError('A duração padrão deve ser de pelo menos 1 minuto.')
            if duracao > 1440:
                raise ValidationError('A duração padrão não pode ser maior que 24 horas.')
        return duracao


class AgendaFiltroForm(forms.Form):
    """
    Formulário para filtros de busca de compromissos
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título, descrição, local...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + Agenda.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    prioridade = forms.ChoiceField(
        choices=[('', 'Todas as prioridades')] + Agenda.PRIORIDADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tipo_compromisso = forms.ModelChoiceField(
        queryset=TipoCompromisso.objects.filter(ativo=True),
        required=False,
        empty_label='Todos os tipos',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    processo = forms.ModelChoiceField(
        queryset=Processo.objects.filter(status__in=['ativo', 'em_andamento']),
        required=False,
        empty_label='Todos os processos',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(ativo=True),
        required=False,
        empty_label='Todos os clientes',
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


class ParticipanteForm(forms.ModelForm):
    """
    Formulário para adicionar participantes a compromissos
    """
    
    class Meta:
        model = Participante
        fields = ['usuario', 'tipo_participacao', 'confirmado']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'tipo_participacao': forms.Select(attrs={'class': 'form-control'}),
            'confirmado': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }