# -*- coding: utf-8 -*-
"""
Formulários para o módulo Financeiro

Este módulo contém os formulários para gerenciamento financeiro.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Financeiro, ContaBancaria, CategoriaFinanceira, Orcamento, ItemOrcamento
from processos.models import Processo
from clientes.models import Cliente


class FinanceiroForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de movimentações financeiras
    """
    
    class Meta:
        model = Financeiro
        fields = [
            'tipo', 'descricao', 'valor', 'data_vencimento', 'data_pagamento',
            'status', 'categoria', 'processo', 'cliente', 'conta_bancaria',
            'forma_pagamento', 'numero_documento', 'observacoes'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição da movimentação'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00'
            }),
            'data_vencimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_pagamento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'processo': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'conta_bancaria': forms.Select(attrs={'class': 'form-control'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número do documento/comprovante'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
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
        
        self.fields['categoria'].queryset = CategoriaFinanceira.objects.filter(
            ativa=True
        ).order_by('nome')
        
        self.fields['conta_bancaria'].queryset = ContaBancaria.objects.filter(
            ativa=True
        ).order_by('nome')
        
        # Campos opcionais
        self.fields['processo'].required = False
        self.fields['cliente'].required = False
        self.fields['data_pagamento'].required = False
        self.fields['forma_pagamento'].required = False
        self.fields['numero_documento'].required = False
        self.fields['observacoes'].required = False
    
    def clean_descricao(self):
        """Validação da descrição"""
        descricao = self.cleaned_data.get('descricao')
        if descricao:
            descricao = descricao.strip()
            if len(descricao) < 3:
                raise ValidationError('A descrição deve ter pelo menos 3 caracteres.')
            if len(descricao) > 200:
                raise ValidationError('A descrição não pode ter mais de 200 caracteres.')
        return descricao
    
    def clean_valor(self):
        """Validação do valor"""
        valor = self.cleaned_data.get('valor')
        if valor is not None:
            if valor <= 0:
                raise ValidationError('O valor deve ser maior que zero.')
            if valor > Decimal('999999999.99'):
                raise ValidationError('O valor é muito alto.')
        return valor
    
    def clean_data_vencimento(self):
        """Validação da data de vencimento"""
        data_vencimento = self.cleaned_data.get('data_vencimento')
        if data_vencimento:
            # Verificar se não é muito no passado (mais de 5 anos)
            limite_passado = timezone.now().date() - timedelta(days=1825)
            if data_vencimento < limite_passado:
                raise ValidationError('A data de vencimento não pode ser mais de 5 anos no passado.')
            
            # Verificar se não é muito no futuro (mais de 10 anos)
            limite_futuro = timezone.now().date() + timedelta(days=3650)
            if data_vencimento > limite_futuro:
                raise ValidationError('A data de vencimento não pode ser mais de 10 anos no futuro.')
        
        return data_vencimento
    
    def clean_data_pagamento(self):
        """Validação da data de pagamento"""
        data_pagamento = self.cleaned_data.get('data_pagamento')
        if data_pagamento:
            # Verificar se não é no futuro
            if data_pagamento > timezone.now().date():
                raise ValidationError('A data de pagamento não pode ser no futuro.')
            
            # Verificar se não é muito no passado
            limite_passado = timezone.now().date() - timedelta(days=1825)
            if data_pagamento < limite_passado:
                raise ValidationError('A data de pagamento não pode ser mais de 5 anos no passado.')
        
        return data_pagamento
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        data_pagamento = cleaned_data.get('data_pagamento')
        processo = cleaned_data.get('processo')
        cliente = cleaned_data.get('cliente')
        
        # Se status é 'pago', data de pagamento é obrigatória
        if status == 'pago' and not data_pagamento:
            raise ValidationError('Data de pagamento é obrigatória quando o status é "Pago".')
        
        # Se data de pagamento informada, status deve ser 'pago'
        if data_pagamento and status != 'pago':
            raise ValidationError('Status deve ser "Pago" quando a data de pagamento é informada.')
        
        # Pelo menos um deve ser informado (processo ou cliente)
        if not processo and not cliente:
            raise ValidationError(
                'É necessário informar pelo menos um processo ou cliente para a movimentação.'
            )
        
        # Se processo informado, verificar se cliente é compatível
        if processo and cliente:
            if processo.cliente != cliente:
                raise ValidationError(
                    'O cliente selecionado não corresponde ao cliente do processo.'
                )
        
        return cleaned_data


class ContaBancariaForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de contas bancárias
    """
    
    class Meta:
        model = ContaBancaria
        fields = ['nome', 'banco', 'agencia', 'conta', 'tipo_conta', 'saldo_inicial', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da conta'
            }),
            'banco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do banco'
            }),
            'agencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número da agência'
            }),
            'conta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número da conta'
            }),
            'tipo_conta': forms.Select(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0,00'
            }),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_nome(self):
        """Validação do nome"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            if len(nome) < 2:
                raise ValidationError('O nome deve ter pelo menos 2 caracteres.')
            
            # Verificar duplicidade
            qs = ContaBancaria.objects.filter(nome__iexact=nome)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Já existe uma conta bancária com este nome.')
        
        return nome
    
    def clean_saldo_inicial(self):
        """Validação do saldo inicial"""
        saldo = self.cleaned_data.get('saldo_inicial')
        if saldo is not None:
            if saldo < Decimal('-999999999.99') or saldo > Decimal('999999999.99'):
                raise ValidationError('Saldo inicial fora dos limites permitidos.')
        return saldo


class CategoriaFinanceiraForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de categorias financeiras
    """
    
    class Meta:
        model = CategoriaFinanceira
        fields = ['nome', 'descricao', 'tipo', 'cor', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição da categoria'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_nome(self):
        """Validação do nome"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            if len(nome) < 2:
                raise ValidationError('O nome deve ter pelo menos 2 caracteres.')
            
            # Verificar duplicidade
            qs = CategoriaFinanceira.objects.filter(nome__iexact=nome)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Já existe uma categoria financeira com este nome.')
        
        return nome


class OrcamentoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de orçamentos
    """
    
    class Meta:
        model = Orcamento
        fields = ['nome', 'descricao', 'processo', 'cliente', 'valor_total', 'data_validade', 'status']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do orçamento'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do orçamento'
            }),
            'processo': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'valor_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00'
            }),
            'data_validade': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'})
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
        
        # Campos opcionais
        self.fields['processo'].required = False
        self.fields['descricao'].required = False
    
    def clean_nome(self):
        """Validação do nome"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            if len(nome) < 3:
                raise ValidationError('O nome deve ter pelo menos 3 caracteres.')
        return nome
    
    def clean_valor_total(self):
        """Validação do valor total"""
        valor = self.cleaned_data.get('valor_total')
        if valor is not None:
            if valor <= 0:
                raise ValidationError('O valor total deve ser maior que zero.')
            if valor > Decimal('999999999.99'):
                raise ValidationError('O valor total é muito alto.')
        return valor
    
    def clean_data_validade(self):
        """Validação da data de validade"""
        data_validade = self.cleaned_data.get('data_validade')
        if data_validade:
            if data_validade <= timezone.now().date():
                raise ValidationError('A data de validade deve ser no futuro.')
        return data_validade


class FinanceiroFiltroForm(forms.Form):
    """
    Formulário para filtros de busca de movimentações financeiras
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por descrição, observações...'
        })
    )
    
    tipo = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + Financeiro.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + Financeiro.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    categoria = forms.ModelChoiceField(
        queryset=CategoriaFinanceira.objects.filter(ativa=True),
        required=False,
        empty_label='Todas as categorias',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    conta_bancaria = forms.ModelChoiceField(
        queryset=ContaBancaria.objects.filter(ativa=True),
        required=False,
        empty_label='Todas as contas',
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
    
    valor_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Valor mínimo'
        })
    )
    
    valor_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Valor máximo'
        })
    )
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        valor_min = cleaned_data.get('valor_min')
        valor_max = cleaned_data.get('valor_max')
        
        if data_inicio and data_fim:
            if data_inicio > data_fim:
                raise ValidationError('A data de início não pode ser posterior à data de fim.')
        
        if valor_min and valor_max:
            if valor_min > valor_max:
                raise ValidationError('O valor mínimo não pode ser maior que o valor máximo.')
        
        return cleaned_data