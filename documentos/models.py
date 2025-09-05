# -*- coding: utf-8 -*-
"""
Modelos de dados para o módulo de Documentos

Este módulo define os modelos relacionados aos documentos jurídicos.
"""

import os
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from processos.models import Processo
from clientes.models import Cliente


def documento_upload_path(instance, filename):
    """Define o caminho de upload dos documentos"""
    # Organiza por ano/mês/cliente/processo
    year = timezone.now().year
    month = timezone.now().month
    cliente_id = instance.processo.cliente.id if instance.processo else instance.cliente.id
    processo_id = instance.processo.id if instance.processo else 'sem_processo'
    
    return f'documentos/{year}/{month:02d}/cliente_{cliente_id}/processo_{processo_id}/{filename}'


class Documento(models.Model):
    """Modelo para representar documentos jurídicos"""
    
    TIPO_CHOICES = [
        ('peticao', 'Petição'),
        ('contrato', 'Contrato'),
        ('procuracao', 'Procuração'),
        ('certidao', 'Certidão'),
        ('comprovante', 'Comprovante'),
        ('rg', 'RG'),
        ('cpf', 'CPF'),
        ('cnpj', 'CNPJ'),
        ('comprovante_residencia', 'Comprovante de Residência'),
        ('comprovante_renda', 'Comprovante de Renda'),
        ('laudo', 'Laudo'),
        ('parecer', 'Parecer'),
        ('sentenca', 'Sentença'),
        ('acordao', 'Acórdão'),
        ('outros', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('arquivado', 'Arquivado'),
        ('vencido', 'Vencido'),
    ]
    
    # Campos básicos
    nome = models.CharField(max_length=200, verbose_name='Nome do Documento')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    tipo = models.CharField(
        max_length=30, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    
    # Relacionamentos
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='documentos',
        blank=True, 
        null=True,
        verbose_name='Processo'
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='documentos',
        verbose_name='Cliente'
    )
    
    # Arquivo
    arquivo = models.FileField(
        upload_to=documento_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt']
            )
        ],
        verbose_name='Arquivo'
    )
    
    # Metadados
    tamanho_arquivo = models.PositiveIntegerField(
        blank=True, 
        null=True,
        verbose_name='Tamanho do Arquivo (bytes)'
    )
    
    # Datas
    data_upload = models.DateTimeField(default=timezone.now, verbose_name='Data de Upload')
    data_vencimento = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='Data de Vencimento'
    )
    
    # Status e controle
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ativo',
        verbose_name='Status'
    )
    confidencial = models.BooleanField(default=False, verbose_name='Confidencial')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Controle de versão
    versao = models.PositiveIntegerField(default=1, verbose_name='Versão')
    documento_pai = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='versoes',
        verbose_name='Documento Original'
    )
    
    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-data_upload']
        indexes = [
            models.Index(fields=['processo']),
            models.Index(fields=['cliente']),
            models.Index(fields=['tipo']),
            models.Index(fields=['status']),
            models.Index(fields=['data_upload']),
            models.Index(fields=['data_vencimento']),
        ]
    
    def __str__(self):
        return f"{self.nome} - {self.cliente.nome}"
    
    def save(self, *args, **kwargs):
        """Sobrescreve o método save para calcular o tamanho do arquivo"""
        if self.arquivo:
            self.tamanho_arquivo = self.arquivo.size
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('documentos:detail', kwargs={'pk': self.pk})
    
    @property
    def extensao_arquivo(self):
        """Retorna a extensão do arquivo"""
        if self.arquivo:
            return os.path.splitext(self.arquivo.name)[1].lower()
        return ''
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado"""
        if not self.tamanho_arquivo:
            return '0 bytes'
        
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if self.tamanho_arquivo < 1024.0:
                return f"{self.tamanho_arquivo:.1f} {unit}"
            self.tamanho_arquivo /= 1024.0
        return f"{self.tamanho_arquivo:.1f} TB"
    
    @property
    def is_vencido(self):
        """Verifica se o documento está vencido"""
        if not self.data_vencimento:
            return False
        from datetime import date
        return self.data_vencimento < date.today()
    
    @property
    def dias_para_vencimento(self):
        """Retorna o número de dias para o vencimento"""
        if not self.data_vencimento:
            return None
        from datetime import date
        delta = self.data_vencimento - date.today()
        return delta.days


class CategoriaDocumento(models.Model):
    """Modelo para categorizar documentos"""
    
    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    cor = models.CharField(
        max_length=7, 
        default='#007bff',
        verbose_name='Cor (Hex)',
        help_text='Cor em formato hexadecimal (#RRGGBB)'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Categoria de Documento'
        verbose_name_plural = 'Categorias de Documentos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class TagDocumento(models.Model):
    """Modelo para tags de documentos"""
    
    nome = models.CharField(max_length=50, unique=True, verbose_name='Nome')
    cor = models.CharField(
        max_length=7, 
        default='#6c757d',
        verbose_name='Cor (Hex)'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Relacionamento many-to-many com documentos
    documentos = models.ManyToManyField(
        Documento, 
        blank=True, 
        related_name='tags',
        verbose_name='Documentos'
    )
    
    class Meta:
        verbose_name = 'Tag de Documento'
        verbose_name_plural = 'Tags de Documentos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class HistoricoDocumento(models.Model):
    """Modelo para histórico de alterações em documentos"""
    
    ACAO_CHOICES = [
        ('criacao', 'Criação'),
        ('edicao', 'Edição'),
        ('download', 'Download'),
        ('exclusao', 'Exclusão'),
        ('restauracao', 'Restauração'),
    ]
    
    documento = models.ForeignKey(
        Documento, 
        on_delete=models.CASCADE, 
        related_name='historico',
        verbose_name='Documento'
    )
    acao = models.CharField(
        max_length=20, 
        choices=ACAO_CHOICES,
        verbose_name='Ação'
    )
    usuario = models.CharField(max_length=200, verbose_name='Usuário')
    data_acao = models.DateTimeField(default=timezone.now, verbose_name='Data da Ação')
    detalhes = models.TextField(blank=True, verbose_name='Detalhes')
    ip_address = models.GenericIPAddressField(
        blank=True, 
        null=True, 
        verbose_name='Endereço IP'
    )
    
    class Meta:
        verbose_name = 'Histórico de Documento'
        verbose_name_plural = 'Históricos de Documentos'
        ordering = ['-data_acao']
        indexes = [
            models.Index(fields=['documento']),
            models.Index(fields=['data_acao']),
            models.Index(fields=['acao']),
        ]
    
    def __str__(self):
        return f"{self.documento.nome} - {self.acao} - {self.data_acao}"
