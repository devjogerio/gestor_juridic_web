from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta

# Importar modelos dos outros apps
from clientes.models import Cliente
from processos.models import Processo, Andamento, Prazo
from documentos.models import Documento
from agenda.models import Agenda
from financeiro.models import Financeiro


class DashboardView(TemplateView):
    """
    View principal do dashboard com estatísticas gerais do sistema
    """
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Data atual para filtros
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Estatísticas de processos
        context['total_processos'] = Processo.objects.count()
        context['processos_ativos'] = Processo.objects.filter(
            status__in=['em_andamento', 'aguardando']
        ).count()
        context['processos_mes'] = Processo.objects.filter(
            data_cadastro__range=[inicio_mes, fim_mes]
        ).count()
        
        # Estatísticas de clientes
        context['total_clientes'] = Cliente.objects.count()
        context['clientes_ativos'] = Cliente.objects.filter(
            ativo=True
        ).count()
        context['clientes_mes'] = Cliente.objects.filter(
            data_cadastro__range=[inicio_mes, fim_mes]
        ).count()
        
        # Prazos próximos (próximos 7 dias)
        proximos_7_dias = hoje + timedelta(days=7)
        context['prazos_proximos'] = Prazo.objects.filter(
            data_vencimento__range=[hoje, proximos_7_dias],
            status='pendente'
        ).count()
        
        # Compromissos de hoje
        try:
            context['compromissos_hoje'] = Agenda.objects.filter(
                data_inicio__date=hoje,
                status__in=['agendado', 'confirmado']
            ).count()
        except:
            context['compromissos_hoje'] = 0
        
        # Documentos recentes (últimos 30 dias)
        ultimos_30_dias = hoje - timedelta(days=30)
        context['documentos_recentes'] = Documento.objects.filter(
            data_upload__gte=ultimos_30_dias
        ).count()
        
        # Estatísticas financeiras
        try:
            context['receitas_mes'] = Financeiro.objects.filter(
                data_vencimento__range=[inicio_mes, fim_mes],
                tipo='receita',
                status__in=['pago', 'recebido']
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            context['despesas_mes'] = Financeiro.objects.filter(
                data_vencimento__range=[inicio_mes, fim_mes],
                tipo='despesa',
                status='pago'
            ).aggregate(total=Sum('valor'))['total'] or 0
        except:
            context['receitas_mes'] = 0
            context['despesas_mes'] = 0
        
        # Atividades recentes
        context['andamentos_recentes'] = Andamento.objects.select_related(
            'processo'
        ).order_by('-data')[:5]
        
        context['prazos_vencendo'] = Prazo.objects.select_related(
            'processo'
        ).filter(
            data_vencimento__range=[hoje, proximos_7_dias],
            status='pendente'
        ).order_by('data_vencimento')[:5]
        
        try:
            context['compromissos_proximos'] = Agenda.objects.filter(
                data_inicio__gte=timezone.now(),
                status__in=['agendado', 'confirmado']
            ).order_by('data_inicio')[:5]
        except:
            context['compromissos_proximos'] = []
        
        return context


class ConfiguracoesView(TemplateView):
    """
    View para configurações do sistema
    """
    template_name = 'core/configuracoes.html'


class PerfilView(TemplateView):
    """
    View para perfil do usuário
    """
    template_name = 'core/perfil.html'


class BuscaGlobalView(TemplateView):
    """
    View para busca global no sistema
    """
    template_name = 'core/busca_global.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        
        if query:
            # Buscar em processos
            context['processos'] = Processo.objects.filter(
                Q(numero__icontains=query) |
                Q(assunto__icontains=query) |
                Q(observacoes__icontains=query)
            )[:10]
            
            # Buscar em clientes
            context['clientes'] = Cliente.objects.filter(
                Q(nome__icontains=query) |
                Q(email__icontains=query) |
                Q(telefone__icontains=query)
            )[:10]
            
            # Buscar em documentos
            context['documentos'] = Documento.objects.filter(
                Q(nome__icontains=query) |
                Q(descricao__icontains=query)
            )[:10]
            
        context['query'] = query
        return context
