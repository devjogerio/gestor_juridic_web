# -*- coding: utf-8 -*-
"""
Modelos de dados para o módulo de Processos

Este módulo define os modelos relacionados aos processos jurídicos.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from clientes.models import Cliente


class Processo(models.Model):
    """Modelo para representar um processo jurídico"""
    
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('arquivado', 'Arquivado'),
        ('suspenso', 'Suspenso'),
        ('finalizado', 'Finalizado'),
    ]
    
    TIPO_CHOICES = [
        ('civel', 'Cível'),
        ('criminal', 'Criminal'),
        ('trabalhista', 'Trabalhista'),
        ('tributario', 'Tributário'),
        ('administrativo', 'Administrativo'),
        ('familia', 'Família'),
        ('previdenciario', 'Previdenciário'),
        ('consumidor', 'Consumidor'),
        ('outros', 'Outros'),
    ]
    
    # Campos básicos
    numero = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name='Número do Processo',
        validators=[
            RegexValidator(
                regex=r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$',
                message='Número deve estar no formato NNNNNNN-DD.AAAA.J.TR.OOOO'
            )
        ]
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ativo',
        verbose_name='Status'
    )
    
    # Relacionamentos
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name='processos',
        verbose_name='Cliente'
    )
    
    # Partes do processo
    parte_contraria = models.CharField(max_length=200, blank=True, verbose_name='Parte Contrária')
    
    # Informações do tribunal
    tribunal = models.CharField(max_length=200, blank=True, verbose_name='Tribunal')
    vara = models.CharField(max_length=100, blank=True, verbose_name='Vara')
    juiz = models.CharField(max_length=200, blank=True, verbose_name='Juiz')
    
    # Responsável
    advogado_responsavel = models.CharField(max_length=200, verbose_name='Advogado Responsável')
    
    # Valores
    valor_causa = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        verbose_name='Valor da Causa'
    )
    
    # Datas
    data_distribuicao = models.DateField(blank=True, null=True, verbose_name='Data de Distribuição')
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name='Data de Cadastro')
    
    # Descrições
    resumo = models.TextField(blank=True, verbose_name='Resumo')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    # Controle
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Processo'
        verbose_name_plural = 'Processos'
        ordering = ['-data_cadastro']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['cliente']),
            models.Index(fields=['status']),
            models.Index(fields=['tipo']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.cliente.nome}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('processos:detail', kwargs={'pk': self.pk})
    
    @property
    def documentos_count(self):
        """Retorna o número de documentos do processo"""
        return self.documentos.filter(ativo=True).count()
    
    @property
    def prazos_pendentes(self):
        """Retorna o número de prazos pendentes"""
        return self.prazos.filter(status='pendente', ativo=True).count()
    
    @property
    def ultimo_andamento(self):
        """Retorna o último andamento do processo"""
        return self.andamentos.filter(ativo=True).order_by('-data').first()


class Prazo(models.Model):
    """Modelo para representar prazos de um processo"""
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('cumprido', 'Cumprido'),
        ('vencido', 'Vencido'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    # Relacionamentos
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='prazos',
        verbose_name='Processo'
    )
    
    # Campos básicos
    descricao = models.CharField(max_length=200, verbose_name='Descrição')
    data_vencimento = models.DateField(verbose_name='Data de Vencimento')
    data_cumprimento = models.DateField(blank=True, null=True, verbose_name='Data de Cumprimento')
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name='Status'
    )
    prioridade = models.CharField(
        max_length=20, 
        choices=PRIORIDADE_CHOICES, 
        default='normal',
        verbose_name='Prioridade'
    )
    
    responsavel = models.CharField(max_length=200, blank=True, verbose_name='Responsável')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    notificado = models.BooleanField(default=False, verbose_name='Notificado')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Prazo'
        verbose_name_plural = 'Prazos'
        ordering = ['data_vencimento']
        indexes = [
            models.Index(fields=['processo']),
            models.Index(fields=['data_vencimento']),
            models.Index(fields=['status']),
            models.Index(fields=['prioridade']),
        ]
    
    def __str__(self):
        return f"{self.descricao} - {self.data_vencimento}"
    
    @property
    def dias_restantes(self):
        """Retorna o número de dias restantes para o vencimento"""
        from datetime import date
        if self.status == 'cumprido':
            return 0
        delta = self.data_vencimento - date.today()
        return delta.days
    
    @property
    def is_vencido(self):
        """Verifica se o prazo está vencido"""
        from datetime import date
        return self.data_vencimento < date.today() and self.status == 'pendente'


class Andamento(models.Model):
    """Modelo para representar andamentos de um processo"""
    
    TIPO_CHOICES = [
        ('despacho', 'Despacho'),
        ('sentenca', 'Sentença'),
        ('audiencia', 'Audiência'),
        ('peticao', 'Petição'),
        ('recurso', 'Recurso'),
        ('decisao', 'Decisão'),
        ('outros', 'Outros'),
    ]
    
    # Relacionamentos
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='andamentos',
        verbose_name='Processo'
    )
    
    # Campos básicos
    data = models.DateField(default=timezone.now, verbose_name='Data')
    descricao = models.TextField(verbose_name='Descrição')
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    responsavel = models.CharField(max_length=200, blank=True, verbose_name='Responsável')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Andamento'
        verbose_name_plural = 'Andamentos'
        ordering = ['-data']
        indexes = [
            models.Index(fields=['processo']),
            models.Index(fields=['data']),
            models.Index(fields=['tipo']),
        ]
    
    def __str__(self):
        return f"{self.data} - {self.descricao[:50]}..."
