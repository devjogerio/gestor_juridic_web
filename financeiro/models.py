# -*- coding: utf-8 -*-
"""
Modelos de dados para o módulo Financeiro

Este módulo define os modelos relacionados ao controle financeiro.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from processos.models import Processo
from clientes.models import Cliente


class Financeiro(models.Model):
    """Modelo para representar movimentações financeiras"""
    
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]
    
    CATEGORIA_RECEITA_CHOICES = [
        ('honorarios', 'Honorários'),
        ('consulta', 'Consulta'),
        ('sucumbencia', 'Sucumbência'),
        ('outros', 'Outros'),
    ]
    
    CATEGORIA_DESPESA_CHOICES = [
        ('custas', 'Custas Processuais'),
        ('pericia', 'Perícia'),
        ('diligencia', 'Diligência'),
        ('cartorio', 'Cartório'),
        ('correios', 'Correios'),
        ('transporte', 'Transporte'),
        ('material', 'Material de Escritório'),
        ('outros', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('recebido', 'Recebido'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('transferencia', 'Transferência'),
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('cheque', 'Cheque'),
    ]
    
    # Campos básicos
    descricao = models.CharField(max_length=200, verbose_name='Descrição')
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    categoria = models.CharField(max_length=50, verbose_name='Categoria')
    
    # Valores
    valor = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor'
    )
    valor_pago = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        verbose_name='Valor Pago'
    )
    
    # Relacionamentos
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='financeiro',
        blank=True, 
        null=True,
        verbose_name='Processo'
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='financeiro',
        verbose_name='Cliente'
    )
    
    # Datas
    data_vencimento = models.DateField(verbose_name='Data de Vencimento')
    data_pagamento = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='Data de Pagamento'
    )
    data_criacao = models.DateTimeField(default=timezone.now, verbose_name='Data de Criação')
    
    # Status e forma de pagamento
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name='Status'
    )
    forma_pagamento = models.CharField(
        max_length=20, 
        choices=FORMA_PAGAMENTO_CHOICES,
        blank=True,
        verbose_name='Forma de Pagamento'
    )
    
    # Informações adicionais
    numero_documento = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Número do Documento'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    # Controle
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Parcelamento
    parcelado = models.BooleanField(default=False, verbose_name='Parcelado')
    numero_parcelas = models.PositiveIntegerField(
        default=1, 
        verbose_name='Número de Parcelas'
    )
    parcela_atual = models.PositiveIntegerField(
        default=1, 
        verbose_name='Parcela Atual'
    )
    financeiro_pai = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='parcelas',
        verbose_name='Financeiro Principal'
    )
    
    class Meta:
        verbose_name = 'Movimentação Financeira'
        verbose_name_plural = 'Movimentações Financeiras'
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['processo']),
            models.Index(fields=['cliente']),
            models.Index(fields=['tipo']),
            models.Index(fields=['status']),
            models.Index(fields=['data_vencimento']),
            models.Index(fields=['data_pagamento']),
            models.Index(fields=['categoria']),
        ]
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor} - {self.cliente.nome}"
    
    def save(self, *args, **kwargs):
        """Sobrescreve o método save para definir categoria baseada no tipo"""
        if not self.categoria:
            if self.tipo == 'receita':
                self.categoria = 'honorarios'
            else:
                self.categoria = 'outros'
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('financeiro:detail', kwargs={'pk': self.pk})
    
    @property
    def valor_pendente(self):
        """Retorna o valor ainda pendente de pagamento"""
        return self.valor - self.valor_pago
    
    @property
    def percentual_pago(self):
        """Retorna o percentual pago"""
        if self.valor == 0:
            return 0
        return (self.valor_pago / self.valor) * 100
    
    @property
    def is_vencido(self):
        """Verifica se está vencido"""
        if self.status in ['pago', 'recebido', 'cancelado']:
            return False
        from datetime import date
        return self.data_vencimento < date.today()
    
    @property
    def dias_vencimento(self):
        """Retorna os dias para vencimento (negativo se vencido)"""
        from datetime import date
        delta = self.data_vencimento - date.today()
        return delta.days
    
    @property
    def is_parcial(self):
        """Verifica se foi pago parcialmente"""
        return self.valor_pago > 0 and self.valor_pago < self.valor
    
    def clean(self):
        """Validação customizada"""
        from django.core.exceptions import ValidationError
        
        if self.valor_pago > self.valor:
            raise ValidationError('O valor pago não pode ser maior que o valor total.')
        
        if self.parcelado and self.numero_parcelas < 2:
            raise ValidationError('Para parcelamento, o número de parcelas deve ser maior que 1.')
        
        if self.parcela_atual > self.numero_parcelas:
            raise ValidationError('A parcela atual não pode ser maior que o número total de parcelas.')


class ContaBancaria(models.Model):
    """Modelo para contas bancárias"""
    
    TIPO_CHOICES = [
        ('corrente', 'Conta Corrente'),
        ('poupanca', 'Conta Poupança'),
        ('investimento', 'Conta Investimento'),
    ]
    
    nome = models.CharField(max_length=100, verbose_name='Nome da Conta')
    banco = models.CharField(max_length=100, verbose_name='Banco')
    agencia = models.CharField(max_length=20, verbose_name='Agência')
    conta = models.CharField(max_length=20, verbose_name='Conta')
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    saldo_inicial = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        verbose_name='Saldo Inicial'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    class Meta:
        verbose_name = 'Conta Bancária'
        verbose_name_plural = 'Contas Bancárias'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.banco}"
    
    @property
    def saldo_atual(self):
        """Calcula o saldo atual baseado nas movimentações"""
        from django.db.models import Sum, Q
        
        receitas = Financeiro.objects.filter(
            conta_bancaria=self,
            tipo='receita',
            status='recebido'
        ).aggregate(total=Sum('valor_pago'))['total'] or 0
        
        despesas = Financeiro.objects.filter(
            conta_bancaria=self,
            tipo='despesa',
            status='pago'
        ).aggregate(total=Sum('valor_pago'))['total'] or 0
        
        return self.saldo_inicial + receitas - despesas


class CategoriaFinanceira(models.Model):
    """Modelo para categorias financeiras personalizadas"""
    
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
        ('ambos', 'Ambos'),
    ]
    
    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    cor = models.CharField(
        max_length=7, 
        default='#007bff',
        verbose_name='Cor (Hex)'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Categoria Financeira'
        verbose_name_plural = 'Categorias Financeiras'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Orcamento(models.Model):
    """Modelo para controle de orçamentos"""
    
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviado', 'Enviado'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('expirado', 'Expirado'),
    ]
    
    numero = models.CharField(max_length=50, unique=True, verbose_name='Número')
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='orcamentos',
        verbose_name='Cliente'
    )
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='orcamentos',
        blank=True, 
        null=True,
        verbose_name='Processo'
    )
    
    descricao = models.TextField(verbose_name='Descrição dos Serviços')
    valor_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name='Valor Total'
    )
    
    data_criacao = models.DateTimeField(default=timezone.now, verbose_name='Data de Criação')
    data_validade = models.DateField(verbose_name='Data de Validade')
    data_aprovacao = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='Data de Aprovação'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='rascunho',
        verbose_name='Status'
    )
    
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['cliente']),
            models.Index(fields=['processo']),
            models.Index(fields=['status']),
            models.Index(fields=['data_validade']),
        ]
    
    def __str__(self):
        return f"Orçamento {self.numero} - {self.cliente.nome}"
    
    @property
    def is_expirado(self):
        """Verifica se o orçamento está expirado"""
        from datetime import date
        return self.data_validade < date.today() and self.status not in ['aprovado', 'rejeitado']
    
    @property
    def dias_validade(self):
        """Retorna os dias restantes de validade"""
        from datetime import date
        delta = self.data_validade - date.today()
        return delta.days


class ItemOrcamento(models.Model):
    """Modelo para itens de orçamento"""
    
    orcamento = models.ForeignKey(
        Orcamento, 
        on_delete=models.CASCADE, 
        related_name='itens',
        verbose_name='Orçamento'
    )
    descricao = models.CharField(max_length=200, verbose_name='Descrição')
    quantidade = models.PositiveIntegerField(default=1, verbose_name='Quantidade')
    valor_unitario = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name='Valor Unitário'
    )
    valor_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name='Valor Total'
    )
    
    class Meta:
        verbose_name = 'Item de Orçamento'
        verbose_name_plural = 'Itens de Orçamento'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.descricao} - {self.orcamento.numero}"
    
    def save(self, *args, **kwargs):
        """Calcula o valor total automaticamente"""
        self.valor_total = self.quantidade * self.valor_unitario
        super().save(*args, **kwargs)
