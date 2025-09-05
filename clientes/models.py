# -*- coding: utf-8 -*-
"""
Modelos de dados para o módulo de Clientes

Este módulo define os modelos relacionados aos clientes do escritório jurídico.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Cliente(models.Model):
    """Modelo para representar um cliente do escritório jurídico"""
    
    TIPO_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    # Campos básicos
    nome = models.CharField(max_length=200, verbose_name='Nome')
    cpf_cnpj = models.CharField(
        max_length=18, 
        unique=True, 
        verbose_name='CPF/CNPJ',
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
                message='CPF deve estar no formato XXX.XXX.XXX-XX ou CNPJ no formato XX.XXX.XXX/XXXX-XX'
            )
        ]
    )
    tipo = models.CharField(
        max_length=2, 
        choices=TIPO_CHOICES, 
        default='PF',
        verbose_name='Tipo'
    )
    
    # Contato
    email = models.EmailField(blank=True, verbose_name='E-mail')
    telefone = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='Telefone',
        validators=[
            RegexValidator(
                regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
                message='Telefone deve estar no formato (XX) XXXXX-XXXX'
            )
        ]
    )
    
    # Endereço
    endereco = models.TextField(blank=True, verbose_name='Endereço')
    cidade = models.CharField(max_length=100, blank=True, verbose_name='Cidade')
    estado = models.CharField(max_length=2, blank=True, verbose_name='Estado')
    cep = models.CharField(
        max_length=10, 
        blank=True,
        verbose_name='CEP',
        validators=[
            RegexValidator(
                regex=r'^\d{5}-\d{3}$',
                message='CEP deve estar no formato XXXXX-XXX'
            )
        ]
    )
    
    # Campos adicionais
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name='Data de Cadastro')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['cpf_cnpj']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('clientes:detail', kwargs={'pk': self.pk})
    
    @property
    def processos_ativos(self):
        """Retorna o número de processos ativos do cliente"""
        return self.processos.filter(ativo=True).count()
    
    def clean(self):
        """Validação customizada do modelo"""
        from django.core.exceptions import ValidationError
        
        # Validação específica para CPF/CNPJ baseada no tipo
        if self.tipo == 'PF' and len(self.cpf_cnpj.replace('.', '').replace('-', '')) != 11:
            raise ValidationError({'cpf_cnpj': 'CPF deve ter 11 dígitos'})
        elif self.tipo == 'PJ' and len(self.cpf_cnpj.replace('.', '').replace('/', '').replace('-', '')) != 14:
            raise ValidationError({'cpf_cnpj': 'CNPJ deve ter 14 dígitos'})
