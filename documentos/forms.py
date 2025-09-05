# -*- coding: utf-8 -*-
"""
Formulários para o módulo de Documentos

Este módulo contém os formulários para gerenciamento de documentos jurídicos.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Documento, CategoriaDocumento, TagDocumento
from processos.models import Processo
from clientes.models import Cliente
import os


class DocumentoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de documentos
    """
    
    tags = forms.ModelMultipleChoiceField(
        queryset=TagDocumento.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Tags'
    )
    
    class Meta:
        model = Documento
        fields = [
            'nome', 'descricao', 'arquivo', 'tipo', 'status',
            'processo', 'cliente', 'data_vencimento', 'confidencial', 'tags'
        ]
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do documento',
                'maxlength': 255
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrição do documento'
            }),
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),

            'processo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data_vencimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'confidencial': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'nome': 'Nome do Documento',
            'descricao': 'Descrição',
            'arquivo': 'Arquivo',
            'tipo': 'Tipo',
            'status': 'Status',

            'processo': 'Processo',
            'cliente': 'Cliente',
            'data_vencimento': 'Data de Vencimento',
            'confidencial': 'Documento Confidencial',
            'tags': 'Tags'
        }
        
        help_texts = {
            'arquivo': 'Formatos aceitos: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG (máx. 10MB)',
            'data_vencimento': 'Deixe em branco se não há data de vencimento',
            'confidencial': 'Marque se o documento contém informações confidenciais',
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa o formulário"""
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['nome'].required = True
        self.fields['arquivo'].required = True
        self.fields['tipo'].required = True
        self.fields['status'].required = True
        
        # Filtrar apenas processos e clientes ativos
        self.fields['processo'].queryset = Processo.objects.filter(ativo=True).order_by('numero')
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True).order_by('nome')
        
        # Adicionar opção vazia
        self.fields['processo'].empty_label = 'Selecione um processo (opcional)'
        self.fields['cliente'].empty_label = 'Selecione um cliente (opcional)'
        self.fields['categoria'].empty_label = 'Selecione uma categoria (opcional)'
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['status'].initial = 'ativo'
            self.fields['confidencial'].initial = False
    
    def clean_nome(self):
        """Valida o nome do documento"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            if len(nome) < 3:
                raise ValidationError('Nome deve ter pelo menos 3 caracteres.')
        return nome
    
    def clean_arquivo(self):
        """Valida o arquivo enviado"""
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo:
            # Verificar tamanho (máx. 10MB)
            if arquivo.size > 10 * 1024 * 1024:
                raise ValidationError('Arquivo muito grande. Tamanho máximo: 10MB.')
            
            # Verificar extensão
            extensoes_permitidas = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png']
            nome_arquivo = arquivo.name.lower()
            extensao = os.path.splitext(nome_arquivo)[1]
            
            if extensao not in extensoes_permitidas:
                raise ValidationError(
                    f'Extensão não permitida. Extensões aceitas: {", ".join(extensoes_permitidas)}'
                )
        
        return arquivo
    
    def clean_data_vencimento(self):
        """Valida a data de vencimento"""
        data_vencimento = self.cleaned_data.get('data_vencimento')
        if data_vencimento:
            hoje = timezone.now().date()
            if data_vencimento <= hoje:
                raise ValidationError('Data de vencimento deve ser no futuro.')
        return data_vencimento
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        processo = cleaned_data.get('processo')
        cliente = cleaned_data.get('cliente')
        
        # Pelo menos um deve ser informado (processo ou cliente)
        if not processo and not cliente:
            raise ValidationError(
                'É necessário informar pelo menos um processo ou cliente para o documento.'
            )
        
        # Se processo informado, verificar se cliente é compatível
        if processo and cliente:
            if processo.cliente != cliente:
                raise ValidationError(
                    'O cliente selecionado não corresponde ao cliente do processo.'
                )
        
        return cleaned_data


class CategoriaDocumentoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de categorias de documentos
    """
    
    class Meta:
        model = CategoriaDocumento
        fields = ['nome', 'descricao', 'cor', 'ativo']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria',
                'maxlength': 100
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição da categoria'
            }),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição',
            'cor': 'Cor',
            'ativo': 'Categoria Ativa'
        }
        
        help_texts = {
            'cor': 'Cor para identificação visual da categoria',
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa o formulário"""
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['nome'].required = True
        
        # Valores padrão
        if not self.instance.pk:
            self.fields['ativa'].initial = True
    
    def clean_nome(self):
        """Valida o nome da categoria"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip().title()
            
            # Verificar se já existe categoria com o mesmo nome
            if self.instance.pk:
                existing = CategoriaDocumento.objects.filter(nome=nome).exclude(pk=self.instance.pk)
            else:
                existing = CategoriaDocumento.objects.filter(nome=nome)
            
            if existing.exists():
                raise ValidationError('Já existe uma categoria com este nome.')
            
            if len(nome) < 2:
                raise ValidationError('Nome deve ter pelo menos 2 caracteres.')
        
        return nome


class TagDocumentoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de tags de documentos
    """
    
    class Meta:
        model = TagDocumento
        fields = ['nome', 'cor']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da tag',
                'maxlength': 50
            }),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#28a745'
            })
        }
        
        labels = {
            'nome': 'Nome',
            'cor': 'Cor'
        }
        
        help_texts = {
            'cor': 'Cor para identificação visual da tag',
        }
    
    def clean_nome(self):
        """Valida o nome da tag"""
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip().lower()
            
            # Verificar se já existe tag com o mesmo nome
            if self.instance.pk:
                existing = TagDocumento.objects.filter(nome=nome).exclude(pk=self.instance.pk)
            else:
                existing = TagDocumento.objects.filter(nome=nome)
            
            if existing.exists():
                raise ValidationError('Já existe uma tag com este nome.')
            
            if len(nome) < 2:
                raise ValidationError('Nome deve ter pelo menos 2 caracteres.')
        
        return nome


class DocumentoFiltroForm(forms.Form):
    """
    Formulário para filtros de busca de documentos
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nome, descrição, processo ou cliente...',
        }),
        label='Buscar'
    )
    
    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Documento.TIPO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Tipo'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Documento.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Status'
    )
    
    categoria = forms.ModelChoiceField(
        required=False,
        queryset=CategoriaDocumento.objects.filter(ativo=True).order_by('nome'),
        empty_label='Todas as categorias',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Categoria'
    )
    
    processo = forms.ModelChoiceField(
        required=False,
        queryset=Processo.objects.filter(ativo=True).order_by('numero'),
        empty_label='Todos os processos',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Processo'
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
    
    confidencial = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('true', 'Apenas confidenciais'),
            ('false', 'Apenas não confidenciais')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Confidencial'
    )


class DocumentoUploadForm(forms.Form):
    """
    Formulário simplificado para upload rápido de documentos
    """
    
    arquivo = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'
        }),
        label='Arquivo',
        help_text='Selecione um arquivo para upload'
    )
    
    processo = forms.ModelChoiceField(
        required=False,
        queryset=Processo.objects.filter(ativo=True).order_by('numero'),
        empty_label='Selecione um processo (opcional)',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Processo'
    )
    
    cliente = forms.ModelChoiceField(
        required=False,
        queryset=Cliente.objects.filter(ativo=True).order_by('nome'),
        empty_label='Selecione um cliente (opcional)',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Cliente'
    )
    
    categoria = forms.ModelChoiceField(
        required=False,
        queryset=CategoriaDocumento.objects.filter(ativo=True).order_by('nome'),
        empty_label='Selecione uma categoria (opcional)',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Categoria'
    )
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        processo = cleaned_data.get('processo')
        cliente = cleaned_data.get('cliente')
        
        # Pelo menos um deve ser informado (processo ou cliente)
        if not processo and not cliente:
            raise ValidationError(
                'É necessário informar pelo menos um processo ou cliente para os documentos.'
            )
        
        return cleaned_data