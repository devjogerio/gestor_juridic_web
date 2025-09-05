# -*- coding: utf-8 -*-
"""
Modelos de dados para o módulo de Agenda

Este módulo define os modelos relacionados à agenda e compromissos.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import datetime, timedelta
from processos.models import Processo
from clientes.models import Cliente


class Agenda(models.Model):
    """Modelo para representar compromissos na agenda"""
    
    TIPO_CHOICES = [
        ('audiencia', 'Audiência'),
        ('reuniao', 'Reunião'),
        ('prazo', 'Prazo'),
        ('consulta', 'Consulta'),
        ('diligencia', 'Diligência'),
        ('protocolo', 'Protocolo'),
        ('outros', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('confirmado', 'Confirmado'),
        ('realizado', 'Realizado'),
        ('cancelado', 'Cancelado'),
        ('reagendado', 'Reagendado'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    # Campos básicos
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    
    # Data e hora
    data_inicio = models.DateTimeField(verbose_name='Data e Hora de Início')
    data_fim = models.DateTimeField(verbose_name='Data e Hora de Fim')
    
    # Status e prioridade
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='agendado',
        verbose_name='Status'
    )
    prioridade = models.CharField(
        max_length=20, 
        choices=PRIORIDADE_CHOICES, 
        default='normal',
        verbose_name='Prioridade'
    )
    
    # Relacionamentos
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='agenda',
        blank=True, 
        null=True,
        verbose_name='Processo'
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='agenda',
        verbose_name='Cliente'
    )
    
    # Local
    local = models.CharField(max_length=300, blank=True, verbose_name='Local')
    endereco = models.TextField(blank=True, verbose_name='Endereço')
    
    # Responsável
    responsavel = models.CharField(max_length=200, verbose_name='Responsável')
    
    # Notificações
    notificar_email = models.BooleanField(default=True, verbose_name='Notificar por E-mail')
    notificar_sms = models.BooleanField(default=False, verbose_name='Notificar por SMS')
    tempo_notificacao = models.PositiveIntegerField(
        default=60, 
        verbose_name='Tempo de Notificação (minutos)',
        help_text='Quantos minutos antes do compromisso enviar a notificação'
    )
    
    # Controle
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    data_criacao = models.DateTimeField(default=timezone.now, verbose_name='Data de Criação')
    
    # Recorrência
    recorrente = models.BooleanField(default=False, verbose_name='Recorrente')
    frequencia_recorrencia = models.CharField(
        max_length=20,
        choices=[
            ('diaria', 'Diária'),
            ('semanal', 'Semanal'),
            ('mensal', 'Mensal'),
            ('anual', 'Anual'),
        ],
        blank=True,
        verbose_name='Frequência de Recorrência'
    )
    data_fim_recorrencia = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='Data Fim da Recorrência'
    )
    
    class Meta:
        verbose_name = 'Compromisso'
        verbose_name_plural = 'Compromissos'
        ordering = ['data_inicio']
        indexes = [
            models.Index(fields=['data_inicio']),
            models.Index(fields=['data_fim']),
            models.Index(fields=['processo']),
            models.Index(fields=['cliente']),
            models.Index(fields=['status']),
            models.Index(fields=['tipo']),
            models.Index(fields=['responsavel']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.data_inicio.strftime('%d/%m/%Y %H:%M')}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('agenda:detail', kwargs={'pk': self.pk})
    
    @property
    def duracao(self):
        """Retorna a duração do compromisso em minutos"""
        delta = self.data_fim - self.data_inicio
        return int(delta.total_seconds() / 60)
    
    @property
    def duracao_formatada(self):
        """Retorna a duração formatada"""
        minutos = self.duracao
        if minutos < 60:
            return f"{minutos} min"
        horas = minutos // 60
        minutos_restantes = minutos % 60
        if minutos_restantes == 0:
            return f"{horas}h"
        return f"{horas}h {minutos_restantes}min"
    
    @property
    def is_hoje(self):
        """Verifica se o compromisso é hoje"""
        return self.data_inicio.date() == timezone.now().date()
    
    @property
    def is_passado(self):
        """Verifica se o compromisso já passou"""
        return self.data_fim < timezone.now()
    
    @property
    def tempo_restante(self):
        """Retorna o tempo restante para o compromisso"""
        if self.is_passado:
            return None
        delta = self.data_inicio - timezone.now()
        return delta
    
    def clean(self):
        """Validação customizada"""
        from django.core.exceptions import ValidationError
        
        if self.data_fim <= self.data_inicio:
            raise ValidationError('A data de fim deve ser posterior à data de início.')
        
        if self.recorrente and not self.frequencia_recorrencia:
            raise ValidationError('Para compromissos recorrentes, a frequência deve ser informada.')


class TipoCompromisso(models.Model):
    """Modelo para tipos personalizados de compromissos"""
    
    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    cor = models.CharField(
        max_length=7, 
        default='#007bff',
        verbose_name='Cor (Hex)',
        help_text='Cor em formato hexadecimal (#RRGGBB)'
    )
    icone = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Ícone',
        help_text='Nome do ícone (ex: calendar, clock, etc.)'
    )
    duracao_padrao = models.PositiveIntegerField(
        default=60, 
        verbose_name='Duração Padrão (minutos)'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Tipo de Compromisso'
        verbose_name_plural = 'Tipos de Compromissos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Participante(models.Model):
    """Modelo para participantes de compromissos"""
    
    TIPO_CHOICES = [
        ('organizador', 'Organizador'),
        ('participante', 'Participante'),
        ('opcional', 'Opcional'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('recusado', 'Recusado'),
    ]
    
    agenda = models.ForeignKey(
        Agenda, 
        on_delete=models.CASCADE, 
        related_name='participantes',
        verbose_name='Compromisso'
    )
    nome = models.CharField(max_length=200, verbose_name='Nome')
    email = models.EmailField(blank=True, verbose_name='E-mail')
    telefone = models.CharField(
        max_length=20, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\(?\d{2}\)?[\s-]?\d{4,5}[\s-]?\d{4}$',
                message='Telefone deve estar no formato (XX) XXXXX-XXXX'
            )
        ],
        verbose_name='Telefone'
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='participante',
        verbose_name='Tipo'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name='Status'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    class Meta:
        verbose_name = 'Participante'
        verbose_name_plural = 'Participantes'
        unique_together = ['agenda', 'email']
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.agenda.titulo}"


class Notificacao(models.Model):
    """Modelo para controle de notificações enviadas"""
    
    TIPO_CHOICES = [
        ('email', 'E-mail'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('enviada', 'Enviada'),
        ('erro', 'Erro'),
    ]
    
    agenda = models.ForeignKey(
        Agenda, 
        on_delete=models.CASCADE, 
        related_name='notificacoes',
        verbose_name='Compromisso'
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    destinatario = models.CharField(max_length=200, verbose_name='Destinatário')
    assunto = models.CharField(max_length=200, verbose_name='Assunto')
    mensagem = models.TextField(verbose_name='Mensagem')
    
    data_agendamento = models.DateTimeField(verbose_name='Data de Agendamento')
    data_envio = models.DateTimeField(blank=True, null=True, verbose_name='Data de Envio')
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name='Status'
    )
    erro_detalhes = models.TextField(blank=True, verbose_name='Detalhes do Erro')
    tentativas = models.PositiveIntegerField(default=0, verbose_name='Tentativas')
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_agendamento']
        indexes = [
            models.Index(fields=['agenda']),
            models.Index(fields=['data_agendamento']),
            models.Index(fields=['status']),
            models.Index(fields=['tipo']),
        ]
    
    def __str__(self):
        return f"{self.assunto} - {self.destinatario}"
