# -*- coding: utf-8 -*-
"""
Modelos de dados para o módulo Core

Este módulo define os modelos centrais do sistema.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator


class Configuracao(models.Model):
    """Modelo para configurações do sistema"""
    
    TIPO_CHOICES = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('booleano', 'Booleano'),
        ('data', 'Data'),
        ('email', 'E-mail'),
        ('url', 'URL'),
        ('arquivo', 'Arquivo'),
    ]
    
    chave = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Chave'
    )
    valor = models.TextField(verbose_name='Valor')
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='texto',
        verbose_name='Tipo'
    )
    descricao = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name='Descrição'
    )
    categoria = models.CharField(
        max_length=50, 
        default='geral',
        verbose_name='Categoria'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    data_criacao = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Data de Criação'
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True, 
        verbose_name='Data de Atualização'
    )
    
    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'
        ordering = ['categoria', 'chave']
        indexes = [
            models.Index(fields=['chave']),
            models.Index(fields=['categoria']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.chave}: {self.valor[:50]}"
    
    @classmethod
    def get_valor(cls, chave, default=None):
        """Método para obter valor de configuração"""
        try:
            config = cls.objects.get(chave=chave, ativo=True)
            return config.valor
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_valor(cls, chave, valor, tipo='texto', descricao='', categoria='geral'):
        """Método para definir valor de configuração"""
        config, created = cls.objects.get_or_create(
            chave=chave,
            defaults={
                'valor': valor,
                'tipo': tipo,
                'descricao': descricao,
                'categoria': categoria
            }
        )
        if not created:
            config.valor = valor
            config.save()
        return config


class LogSistema(models.Model):
    """Modelo para logs do sistema"""
    
    NIVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    CATEGORIA_CHOICES = [
        ('sistema', 'Sistema'),
        ('usuario', 'Usuário'),
        ('processo', 'Processo'),
        ('cliente', 'Cliente'),
        ('documento', 'Documento'),
        ('agenda', 'Agenda'),
        ('financeiro', 'Financeiro'),
        ('seguranca', 'Segurança'),
        ('backup', 'Backup'),
        ('integracao', 'Integração'),
    ]
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Usuário'
    )
    nivel = models.CharField(
        max_length=20, 
        choices=NIVEL_CHOICES,
        verbose_name='Nível'
    )
    categoria = models.CharField(
        max_length=20, 
        choices=CATEGORIA_CHOICES,
        verbose_name='Categoria'
    )
    acao = models.CharField(max_length=100, verbose_name='Ação')
    descricao = models.TextField(verbose_name='Descrição')
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name='Endereço IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    dados_extras = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='Dados Extras'
    )
    data_criacao = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Data de Criação'
    )
    
    class Meta:
        verbose_name = 'Log do Sistema'
        verbose_name_plural = 'Logs do Sistema'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['nivel']),
            models.Index(fields=['categoria']),
            models.Index(fields=['data_criacao']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.nivel.upper()} - {self.acao} - {self.data_criacao}"
    
    @classmethod
    def log(cls, nivel, categoria, acao, descricao, usuario=None, ip_address=None, user_agent=None, **kwargs):
        """Método para criar log"""
        return cls.objects.create(
            nivel=nivel,
            categoria=categoria,
            acao=acao,
            descricao=descricao,
            usuario=usuario,
            ip_address=ip_address,
            user_agent=user_agent,
            dados_extras=kwargs
        )


class Backup(models.Model):
    """Modelo para controle de backups"""
    
    TIPO_CHOICES = [
        ('completo', 'Completo'),
        ('incremental', 'Incremental'),
        ('diferencial', 'Diferencial'),
    ]
    
    STATUS_CHOICES = [
        ('iniciado', 'Iniciado'),
        ('em_progresso', 'Em Progresso'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
        ('cancelado', 'Cancelado'),
    ]
    
    nome = models.CharField(max_length=200, verbose_name='Nome')
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='iniciado',
        verbose_name='Status'
    )
    
    # Informações do backup
    tamanho_bytes = models.BigIntegerField(
        null=True, 
        blank=True,
        verbose_name='Tamanho (bytes)'
    )
    arquivo_backup = models.FileField(
        upload_to='backups/',
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['zip', 'tar', 'gz'])],
        verbose_name='Arquivo de Backup'
    )
    
    # Datas
    data_inicio = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Data de Início'
    )
    data_fim = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Data de Fim'
    )
    
    # Informações adicionais
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    erro_detalhes = models.TextField(blank=True, verbose_name='Detalhes do Erro')
    
    # Configurações
    automatico = models.BooleanField(default=False, verbose_name='Automático')
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Usuário'
    )
    
    class Meta:
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'
        ordering = ['-data_inicio']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['tipo']),
            models.Index(fields=['data_inicio']),
            models.Index(fields=['automatico']),
        ]
    
    def __str__(self):
        return f"{self.nome} - {self.status} - {self.data_inicio}"
    
    @property
    def duracao(self):
        """Retorna a duração do backup"""
        if self.data_fim:
            return self.data_fim - self.data_inicio
        return None
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho formatado"""
        if not self.tamanho_bytes:
            return 'N/A'
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.tamanho_bytes < 1024.0:
                return f"{self.tamanho_bytes:.1f} {unit}"
            self.tamanho_bytes /= 1024.0
        return f"{self.tamanho_bytes:.1f} PB"


class Notificacao(models.Model):
    """Modelo para notificações do sistema"""
    
    TIPO_CHOICES = [
        ('info', 'Informação'),
        ('sucesso', 'Sucesso'),
        ('aviso', 'Aviso'),
        ('erro', 'Erro'),
        ('lembrete', 'Lembrete'),
    ]
    
    CATEGORIA_CHOICES = [
        ('sistema', 'Sistema'),
        ('processo', 'Processo'),
        ('prazo', 'Prazo'),
        ('agenda', 'Agenda'),
        ('financeiro', 'Financeiro'),
        ('documento', 'Documento'),
        ('cliente', 'Cliente'),
    ]
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Usuário'
    )
    titulo = models.CharField(max_length=200, verbose_name='Título')
    mensagem = models.TextField(verbose_name='Mensagem')
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='info',
        verbose_name='Tipo'
    )
    categoria = models.CharField(
        max_length=20, 
        choices=CATEGORIA_CHOICES, 
        default='sistema',
        verbose_name='Categoria'
    )
    
    # Status
    lida = models.BooleanField(default=False, verbose_name='Lida')
    importante = models.BooleanField(default=False, verbose_name='Importante')
    
    # Datas
    data_criacao = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Data de Criação'
    )
    data_leitura = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Data de Leitura'
    )
    data_expiracao = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Data de Expiração'
    )
    
    # Dados extras
    url_acao = models.URLField(
        blank=True,
        verbose_name='URL de Ação'
    )
    dados_extras = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='Dados Extras'
    )
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['lida']),
            models.Index(fields=['tipo']),
            models.Index(fields=['categoria']),
            models.Index(fields=['data_criacao']),
            models.Index(fields=['importante']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
    
    def marcar_como_lida(self):
        """Marca a notificação como lida"""
        if not self.lida:
            self.lida = True
            self.data_leitura = timezone.now()
            self.save()
    
    @property
    def is_expirada(self):
        """Verifica se a notificação está expirada"""
        if self.data_expiracao:
            return timezone.now() > self.data_expiracao
        return False
    
    @classmethod
    def criar_notificacao(cls, usuario, titulo, mensagem, tipo='info', categoria='sistema', **kwargs):
        """Método para criar notificação"""
        return cls.objects.create(
            usuario=usuario,
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            categoria=categoria,
            **kwargs
        )


class PerfilUsuario(models.Model):
    """Modelo para perfil estendido do usuário"""
    
    TEMA_CHOICES = [
        ('claro', 'Claro'),
        ('escuro', 'Escuro'),
        ('auto', 'Automático'),
    ]
    
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Usuário'
    )
    
    # Informações pessoais
    telefone = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='Telefone'
    )
    celular = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='Celular'
    )
    foto = models.ImageField(
        upload_to='perfis/',
        blank=True, 
        null=True,
        verbose_name='Foto'
    )
    
    # Configurações de interface
    tema = models.CharField(
        max_length=20, 
        choices=TEMA_CHOICES, 
        default='claro',
        verbose_name='Tema'
    )
    idioma = models.CharField(
        max_length=10, 
        default='pt-br',
        verbose_name='Idioma'
    )
    
    # Configurações de notificação
    notificacoes_email = models.BooleanField(
        default=True, 
        verbose_name='Notificações por E-mail'
    )
    notificacoes_sistema = models.BooleanField(
        default=True, 
        verbose_name='Notificações do Sistema'
    )
    notificacoes_prazos = models.BooleanField(
        default=True, 
        verbose_name='Notificações de Prazos'
    )
    
    # Informações profissionais
    oab_numero = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='Número da OAB'
    )
    oab_uf = models.CharField(
        max_length=2, 
        blank=True,
        verbose_name='UF da OAB'
    )
    especialidades = models.TextField(
        blank=True,
        verbose_name='Especialidades'
    )
    
    # Controle
    data_criacao = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Data de Criação'
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True, 
        verbose_name='Data de Atualização'
    )
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuário'
        ordering = ['usuario__username']
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"
    
    @property
    def nome_completo(self):
        """Retorna o nome completo do usuário"""
        return f"{self.usuario.first_name} {self.usuario.last_name}".strip() or self.usuario.username
    
    @property
    def oab_completa(self):
        """Retorna a OAB completa"""
        if self.oab_numero and self.oab_uf:
            return f"{self.oab_numero}/{self.oab_uf}"
        return self.oab_numero or ''
