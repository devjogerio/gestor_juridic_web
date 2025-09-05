# -*- coding: utf-8 -*-
"""
Formulários para o módulo de Processos

Este módulo contém os formulários para gerenciamento de processos jurídicos.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Processo, Prazo, Andamento
from clientes.models import Cliente
import re


class ProcessoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de processos
    """
    
    class Meta:
        model = Processo
        fields = [
            'numero', 'cliente', 'status', 'tipo', 'parte_contraria',
            'vara', 'tribunal', 'juiz', 'advogado_responsavel', 'valor_causa', 
            'data_distribuicao', 'resumo', 'observacoes', 'ativo'
        ]
        
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0000000-00.0000.0.00.0000',
                'maxlength': 25
            }),
            'parte_contraria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da parte contrária',
                'maxlength': 200
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre o andamento'
            }),
            'tribunal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tribunal responsável',
                'maxlength': 200
            }),
            'juiz': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do juiz',
                'maxlength': 200
            }),
            'advogado_responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do advogado responsável',
                'maxlength': 200
            }),
            'vara': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vara responsável',
                'maxlength': 100
            }),
            'data_distribuicao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'valor_causa': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0,00',
                'step': '0.01',
                'min': '0'
            }),
            'resumo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Resumo do processo'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observações adicionais'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'numero': 'Número do Processo',
            'cliente': 'Cliente',
            'status': 'Status',
            'tipo': 'Tipo',
            'parte_contraria': 'Parte Contrária',
            'vara': 'Vara',
            'tribunal': 'Tribunal',
            'juiz': 'Juiz',
            'advogado_responsavel': 'Advogado Responsável',
            'valor_causa': 'Valor da Causa (R$)',
            'data_distribuicao': 'Data de Distribuição',
            'resumo': 'Resumo',
            'observacoes': 'Observações',
            'ativo': 'Processo Ativo'
        }
        
        help_texts = {
            'numero': 'Formato: 0000000-00.0000.0.00.0000',
            'valor_causa': 'Valor monetário da causa em reais',
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa o formulário"""
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['numero'].required = True
        self.fields['titulo'].required = True
        self.fields['cliente'].required = True
        self.fields['status'].required = True
        self.fields['tipo'].required = True
        
        # Filtrar apenas clientes ativos
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True).order_by('nome')
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['ativo'].initial = True
            self.fields['status'].initial = 'ativo'
            self.fields['prioridade'].initial = 'media'
    
    def clean_numero(self):
        """Valida o número do processo"""
        numero = self.cleaned_data.get('numero')
        if numero:
            numero = numero.strip()
            
            # Verifica se já existe outro processo com o mesmo número
            if self.instance.pk:
                existing = Processo.objects.filter(numero=numero).exclude(pk=self.instance.pk)
            else:
                existing = Processo.objects.filter(numero=numero)
            
            if existing.exists():
                raise ValidationError('Já existe um processo cadastrado com este número.')
        
        return numero
    
    def clean_parte_contraria(self):
        """Valida o nome da parte contrária"""
        parte_contraria = self.cleaned_data.get('parte_contraria')
        if parte_contraria:
            parte_contraria = parte_contraria.strip().title()
            if len(parte_contraria) < 3:
                raise ValidationError('Nome da parte contrária deve ter pelo menos 3 caracteres.')
        return parte_contraria
    
    def clean_valor_causa(self):
        """Valida o valor da causa"""
        valor_causa = self.cleaned_data.get('valor_causa')
        if valor_causa is not None and valor_causa < 0:
            raise ValidationError('Valor da causa não pode ser negativo.')
        return valor_causa


class PrazoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de prazos
    """
    
    class Meta:
        model = Prazo
        fields = [
            'processo', 'descricao', 'data_vencimento', 'data_cumprimento',
            'status', 'prioridade', 'responsavel', 'observacoes', 'notificado'
        ]
        
        widgets = {
            'processo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'prioridade': forms.Select(attrs={
                'class': 'form-control'
            }),
            'responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável',
                'maxlength': 200
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do prazo'
            }),
            'data_vencimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre o prazo'
            }),
            'notificado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'data_cumprimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        
        labels = {
            'processo': 'Processo',
            'descricao': 'Descrição',
            'data_vencimento': 'Data de Vencimento',
            'data_cumprimento': 'Data de Cumprimento',
            'status': 'Status',
            'prioridade': 'Prioridade',
            'responsavel': 'Responsável',
            'observacoes': 'Observações',
            'notificado': 'Notificado'
        }
        
        help_texts = {
            'data_cumprimento': 'Deixe em branco se ainda não foi cumprido',
            'notificado': 'Marque se já foi notificado sobre este prazo',
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa o formulário"""
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['processo'].required = True
        self.fields['titulo'].required = True
        self.fields['data_vencimento'].required = True
        
        # Filtrar apenas processos ativos
        self.fields['processo'].queryset = Processo.objects.filter(ativo=True).order_by('numero')
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['cumprido'].initial = False
            self.fields['dias_antecedencia'].initial = 3
    
    def clean_data_vencimento(self):
        """Valida a data de vencimento"""
        data_vencimento = self.cleaned_data.get('data_vencimento')
        if data_vencimento:
            hoje = timezone.now().date()
            if data_vencimento < hoje:
                raise ValidationError('Data de vencimento não pode ser no passado.')
        return data_vencimento
    
    def clean_data_cumprimento(self):
        """Valida a data de cumprimento"""
        data_cumprimento = self.cleaned_data.get('data_cumprimento')
        cumprido = self.cleaned_data.get('cumprido')
        
        if cumprido and not data_cumprimento:
            raise ValidationError('Data de cumprimento é obrigatória quando o prazo está marcado como cumprido.')
        
        if not cumprido and data_cumprimento:
            raise ValidationError('Não é possível informar data de cumprimento se o prazo não está marcado como cumprido.')
        
        if data_cumprimento:
            hoje = timezone.now().date()
            if data_cumprimento > hoje:
                raise ValidationError('Data de cumprimento não pode ser no futuro.')
        
        return data_cumprimento
    
    def clean_descricao(self):
        """Valida a descrição do prazo"""
        descricao = self.cleaned_data.get('descricao')
        if descricao and len(descricao.strip()) < 5:
            raise ValidationError('A descrição deve ter pelo menos 5 caracteres.')
        return descricao.strip() if descricao else descricao


class AndamentoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de andamentos
    """
    
    class Meta:
        model = Andamento
        fields = [
            'processo', 'data', 'descricao', 'tipo', 'responsavel', 'observacoes'
        ]
        
        widgets = {
            'processo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável',
                'maxlength': 200
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrição detalhada do andamento'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        
        labels = {
            'processo': 'Processo',
            'data': 'Data',
            'descricao': 'Descrição',
            'tipo': 'Tipo',
            'responsavel': 'Responsável',
            'observacoes': 'Observações'
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa o formulário"""
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['processo'].required = True
        self.fields['data'].required = True
        self.fields['titulo'].required = True
        self.fields['descricao'].required = True
        self.fields['tipo'].required = True
        
        # Filtrar apenas processos ativos
        self.fields['processo'].queryset = Processo.objects.filter(ativo=True).order_by('numero')
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['data'].initial = timezone.now().date()
            self.fields['tipo'].initial = 'andamento'
    
    def clean_data(self):
        """Valida a data do andamento"""
        data = self.cleaned_data.get('data')
        if data:
            hoje = timezone.now().date()
            if data > hoje:
                raise ValidationError('Data do andamento não pode ser no futuro.')
        return data
    



class ProcessoFiltroForm(forms.Form):
    """
    Formulário para filtros de busca de processos
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número, título, cliente, vara ou comarca...',
        }),
        label='Buscar'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Processo.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Status'
    )
    
    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Processo.TIPO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Tipo'
    )
    
    cliente = forms.ModelChoiceField(
        required=False,
        queryset=Cliente.objects.filter(ativo=True).order_by('nome'),
        empty_label='Todos os clientes',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Cliente'
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data Início'
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data Fim'
    )