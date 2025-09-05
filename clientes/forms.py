# -*- coding: utf-8 -*-
"""
Formulários para o módulo de Clientes

Este módulo contém os formulários para gerenciamento de clientes.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente
import re


class ClienteForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de clientes
    """
    
    class Meta:
        model = Cliente
        fields = [
            'nome', 'cpf_cnpj', 'tipo', 'email', 'telefone',
            'endereco', 'cidade', 'estado', 'cep',
            'observacoes', 'ativo'
        ]
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo ou razão social',
                'maxlength': 200
            }),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CPF ou CNPJ',
                'maxlength': 18
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999',
                'maxlength': 15
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Endereço completo',
                'rows': 2
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade',
                'maxlength': 100
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estado',
                'maxlength': 2
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00000-000',
                'maxlength': 9
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observações adicionais sobre o cliente'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'nome': 'Nome/Razão Social',
            'cpf_cnpj': 'CPF/CNPJ',
            'tipo': 'Tipo de Pessoa',
            'email': 'E-mail',
            'telefone': 'Telefone',
            'endereco': 'Endereço',
            'cidade': 'Cidade',
            'estado': 'Estado (UF)',
            'cep': 'CEP',
            'observacoes': 'Observações',
            'ativo': 'Cliente Ativo'
        }
        
        help_texts = {
            'cpf_cnpj': 'Informe apenas números para CPF ou CNPJ',
            'telefone': 'Formato: (11) 99999-9999',
            'cep': 'Formato: 00000-000',
            'estado': 'Sigla do estado (ex: SP, RJ, MG)',
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa o formulário"""
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['nome'].required = True
        self.fields['cpf_cnpj'].required = True
        self.fields['tipo'].required = True
        self.fields['email'].required = True
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['ativo'].initial = True
    
    def clean_nome(self):
        """Valida o campo nome"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip().title()
            if len(nome) < 2:
                raise ValidationError('Nome deve ter pelo menos 2 caracteres.')
        return nome
    
    def clean_cpf_cnpj(self):
        """Valida CPF ou CNPJ"""
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        if cpf_cnpj:
            # Remove caracteres não numéricos
            cpf_cnpj = re.sub(r'\D', '', cpf_cnpj)
            
            # Verifica se é CPF (11 dígitos) ou CNPJ (14 dígitos)
            if len(cpf_cnpj) == 11:
                if not self._validar_cpf(cpf_cnpj):
                    raise ValidationError('CPF inválido.')
            elif len(cpf_cnpj) == 14:
                if not self._validar_cnpj(cpf_cnpj):
                    raise ValidationError('CNPJ inválido.')
            else:
                raise ValidationError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.')
            
            # Verifica se já existe outro cliente com o mesmo CPF/CNPJ
            if self.instance.pk:
                existing = Cliente.objects.filter(cpf_cnpj=cpf_cnpj).exclude(pk=self.instance.pk)
            else:
                existing = Cliente.objects.filter(cpf_cnpj=cpf_cnpj)
            
            if existing.exists():
                raise ValidationError('Já existe um cliente cadastrado com este CPF/CNPJ.')
        
        return cpf_cnpj
    
    def clean_email(self):
        """Valida o campo email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            
            # Verifica se já existe outro cliente com o mesmo email
            if self.instance.pk:
                existing = Cliente.objects.filter(email=email).exclude(pk=self.instance.pk)
            else:
                existing = Cliente.objects.filter(email=email)
            
            if existing.exists():
                raise ValidationError('Já existe um cliente cadastrado com este e-mail.')
        
        return email
    
    def clean_telefone(self):
        """Valida o campo telefone"""
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remove caracteres não numéricos
            telefone_numerico = re.sub(r'\D', '', telefone)
            
            # Verifica se tem pelo menos 10 dígitos
            if len(telefone_numerico) < 10:
                raise ValidationError('Telefone deve ter pelo menos 10 dígitos.')
            
            # Formata o telefone
            if len(telefone_numerico) == 10:
                telefone = f"({telefone_numerico[:2]}) {telefone_numerico[2:6]}-{telefone_numerico[6:]}"
            elif len(telefone_numerico) == 11:
                telefone = f"({telefone_numerico[:2]}) {telefone_numerico[2:7]}-{telefone_numerico[7:]}"
            else:
                raise ValidationError('Telefone deve ter 10 ou 11 dígitos.')
        
        return telefone
    
    def clean_cep(self):
        """Valida o campo CEP"""
        cep = self.cleaned_data.get('cep')
        if cep:
            # Remove caracteres não numéricos
            cep_numerico = re.sub(r'\D', '', cep)
            
            if len(cep_numerico) != 8:
                raise ValidationError('CEP deve ter 8 dígitos.')
            
            # Formata o CEP
            cep = f"{cep_numerico[:5]}-{cep_numerico[5:]}"
        
        return cep
    
    def clean_estado(self):
        """Valida o campo estado"""
        estado = self.cleaned_data.get('estado')
        if estado:
            estado = estado.upper().strip()
            
            # Lista de estados válidos
            estados_validos = [
                'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
                'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
                'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
            ]
            
            if estado not in estados_validos:
                raise ValidationError('Informe uma sigla de estado válida.')
        
        return estado
    
    def _validar_cpf(self, cpf):
        """Valida CPF usando algoritmo oficial"""
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf[9]) != digito1:
            return False
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return int(cpf[10]) == digito2
    
    def _validar_cnpj(self, cnpj):
        """Valida CNPJ usando algoritmo oficial"""
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        # Calcula primeiro dígito verificador
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[12]) != digito1:
            return False
        
        # Calcula segundo dígito verificador
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return int(cnpj[13]) == digito2


class ClienteFiltroForm(forms.Form):
    """
    Formulário para filtros de busca de clientes
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nome, CPF/CNPJ, email ou telefone...',
        }),
        label='Buscar'
    )
    
    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Cliente.TIPO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Tipo'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('ativo', 'Ativos'),
            ('inativo', 'Inativos')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Status'
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