# -*- coding: utf-8 -*-
"""
Views para o módulo de Processos

Este módulo contém as views para gerenciamento de processos jurídicos.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Processo, Prazo, Andamento
from .forms import ProcessoForm, PrazoForm, AndamentoForm
from clientes.models import Cliente


class ProcessoListView(LoginRequiredMixin, ListView):
    """View para listagem de processos"""
    model = Processo
    template_name = 'processos/lista.html'
    context_object_name = 'processos'
    paginate_by = 20
    ordering = ['-data_cadastro']
    
    def get_queryset(self):
        """Filtra processos baseado na busca"""
        queryset = Processo.objects.filter(ativo=True).select_related('cliente')
        
        # Busca por termo
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search) |
                Q(titulo__icontains=search) |
                Q(cliente__nome__icontains=search) |
                Q(vara__icontains=search) |
                Q(comarca__icontains=search)
            )
        
        # Filtro por status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtro por tipo
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Filtro por prioridade
        prioridade = self.request.GET.get('prioridade')
        if prioridade:
            queryset = queryset.filter(prioridade=prioridade)
        
        # Filtro por cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        return queryset.annotate(
            documentos_count=Count('documentos'),
            prazos_count=Count('prazos')
        )
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        context['prioridade_filter'] = self.request.GET.get('prioridade', '')
        context['cliente_filter'] = self.request.GET.get('cliente', '')
        context['total_processos'] = Processo.objects.filter(ativo=True).count()
        context['clientes'] = Cliente.objects.filter(ativo=True).order_by('nome')
        return context


class ProcessoDetailView(LoginRequiredMixin, DetailView):
    """View para detalhes do processo"""
    model = Processo
    template_name = 'processos/detalhe.html'
    context_object_name = 'processo'
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        processo = self.get_object()
        
        # Prazos do processo
        context['prazos'] = processo.prazos.all().order_by('data_vencimento')[:10]
        context['prazos_pendentes'] = processo.prazos.filter(cumprido=False).count()
        
        # Andamentos do processo
        context['andamentos'] = processo.andamentos.all().order_by('-data')[:10]
        context['total_andamentos'] = processo.andamentos.count()
        
        # Documentos do processo
        context['documentos'] = processo.documentos.all()[:10]
        context['total_documentos'] = processo.documentos.count()
        
        # Movimentações financeiras
        context['financeiro'] = processo.financeiro.all()[:10]
        context['total_financeiro'] = processo.financeiro.count()
        
        return context


class ProcessoCreateView(LoginRequiredMixin, CreateView):
    """View para criação de processo"""
    model = Processo
    form_class = ProcessoForm
    template_name = 'processos/form.html'
    success_url = reverse_lazy('processos:lista')
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Processo cadastrado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Processa formulário inválido"""
        messages.error(self.request, 'Erro ao cadastrar processo. Verifique os dados informados.')
        return super().form_invalid(form)


class ProcessoUpdateView(LoginRequiredMixin, UpdateView):
    """View para edição de processo"""
    model = Processo
    form_class = ProcessoForm
    template_name = 'processos/form.html'
    
    def get_success_url(self):
        """Retorna URL de sucesso"""
        return reverse_lazy('processos:detalhe', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Processo atualizado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Processa formulário inválido"""
        messages.error(self.request, 'Erro ao atualizar processo. Verifique os dados informados.')
        return super().form_invalid(form)


class ProcessoDeleteView(LoginRequiredMixin, DeleteView):
    """View para exclusão de processo"""
    model = Processo
    template_name = 'processos/confirmar_exclusao.html'
    success_url = reverse_lazy('processos:lista')
    
    def delete(self, request, *args, **kwargs):
        """Desativa processo ao invés de excluir"""
        self.object = self.get_object()
        self.object.ativo = False
        self.object.save()
        messages.success(request, 'Processo desativado com sucesso!')
        return redirect(self.success_url)


# Views para Prazos

class PrazoCreateView(LoginRequiredMixin, CreateView):
    """View para criação de prazo"""
    model = Prazo
    form_class = PrazoForm
    template_name = 'processos/prazo_form.html'
    
    def get_initial(self):
        """Define valores iniciais"""
        initial = super().get_initial()
        processo_id = self.kwargs.get('processo_id')
        if processo_id:
            initial['processo'] = processo_id
        return initial
    
    def get_success_url(self):
        """Retorna URL de sucesso"""
        return reverse_lazy('processos:detalhe', kwargs={'pk': self.object.processo.pk})
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Prazo cadastrado com sucesso!')
        return super().form_valid(form)


class PrazoUpdateView(LoginRequiredMixin, UpdateView):
    """View para edição de prazo"""
    model = Prazo
    form_class = PrazoForm
    template_name = 'processos/prazo_form.html'
    
    def get_success_url(self):
        """Retorna URL de sucesso"""
        return reverse_lazy('processos:detalhe', kwargs={'pk': self.object.processo.pk})
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Prazo atualizado com sucesso!')
        return super().form_valid(form)


# Views para Andamentos

class AndamentoCreateView(LoginRequiredMixin, CreateView):
    """View para criação de andamento"""
    model = Andamento
    form_class = AndamentoForm
    template_name = 'processos/andamento_form.html'
    
    def get_initial(self):
        """Define valores iniciais"""
        initial = super().get_initial()
        processo_id = self.kwargs.get('processo_id')
        if processo_id:
            initial['processo'] = processo_id
        return initial
    
    def get_success_url(self):
        """Retorna URL de sucesso"""
        return reverse_lazy('processos:detalhe', kwargs={'pk': self.object.processo.pk})
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Andamento cadastrado com sucesso!')
        return super().form_valid(form)


class AndamentoUpdateView(LoginRequiredMixin, UpdateView):
    """View para edição de andamento"""
    model = Andamento
    form_class = AndamentoForm
    template_name = 'processos/andamento_form.html'
    
    def get_success_url(self):
        """Retorna URL de sucesso"""
        return reverse_lazy('processos:detalhe', kwargs={'pk': self.object.processo.pk})
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Andamento atualizado com sucesso!')
        return super().form_valid(form)


# Views baseadas em função

@login_required
def processo_dashboard(request):
    """Dashboard de processos"""
    hoje = timezone.now().date()
    
    context = {
        'total_processos': Processo.objects.filter(ativo=True).count(),
        'processos_ativos': Processo.objects.filter(ativo=True, status='ativo').count(),
        'processos_suspensos': Processo.objects.filter(ativo=True, status='suspenso').count(),
        'processos_arquivados': Processo.objects.filter(ativo=True, status='arquivado').count(),
        'prazos_vencendo': Prazo.objects.filter(
            processo__ativo=True,
            cumprido=False,
            data_vencimento__lte=hoje + timedelta(days=7)
        ).count(),
        'prazos_vencidos': Prazo.objects.filter(
            processo__ativo=True,
            cumprido=False,
            data_vencimento__lt=hoje
        ).count(),
        'processos_recentes': Processo.objects.filter(ativo=True).order_by('-data_cadastro')[:5],
        'prazos_urgentes': Prazo.objects.filter(
            processo__ativo=True,
            cumprido=False,
            data_vencimento__lte=hoje + timedelta(days=3)
        ).order_by('data_vencimento')[:5],
    }
    return render(request, 'processos/dashboard.html', context)


@login_required
@require_http_methods(["GET"])
def processo_busca_ajax(request):
    """Busca de processos via AJAX"""
    term = request.GET.get('term', '')
    
    if len(term) < 2:
        return JsonResponse({'results': []})
    
    processos = Processo.objects.filter(
        Q(numero__icontains=term) |
        Q(titulo__icontains=term) |
        Q(cliente__nome__icontains=term),
        ativo=True
    ).select_related('cliente')[:10]
    
    results = []
    for processo in processos:
        results.append({
            'id': processo.id,
            'text': f"{processo.numero} - {processo.titulo}",
            'numero': processo.numero,
            'titulo': processo.titulo,
            'cliente': processo.cliente.nome,
            'status': processo.get_status_display(),
            'tipo': processo.get_tipo_display()
        })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["POST"])
def prazo_marcar_cumprido(request, pk):
    """Marca prazo como cumprido"""
    prazo = get_object_or_404(Prazo, pk=pk)
    
    prazo.cumprido = True
    prazo.data_cumprimento = timezone.now().date()
    prazo.save()
    
    messages.success(request, 'Prazo marcado como cumprido!')
    
    return JsonResponse({
        'success': True,
        'cumprido': prazo.cumprido,
        'message': 'Prazo marcado como cumprido!'
    })


@login_required
def processo_relatorio(request):
    """Relatório de processos"""
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status = request.GET.get('status')
    tipo = request.GET.get('tipo')
    cliente_id = request.GET.get('cliente')
    
    queryset = Processo.objects.filter(ativo=True)
    
    # Aplicar filtros
    if data_inicio:
        queryset = queryset.filter(data_cadastro__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data_cadastro__lte=data_fim)
    if status:
        queryset = queryset.filter(status=status)
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if cliente_id:
        queryset = queryset.filter(cliente_id=cliente_id)
    
    # Estatísticas
    stats = {
        'total': queryset.count(),
        'ativos': queryset.filter(status='ativo').count(),
        'suspensos': queryset.filter(status='suspenso').count(),
        'arquivados': queryset.filter(status='arquivado').count(),
        'finalizados': queryset.filter(status='finalizado').count(),
        'por_tipo': {},
        'por_prioridade': {},
    }
    
    # Estatísticas por tipo
    for tipo_key, tipo_label in Processo.TIPO_CHOICES:
        stats['por_tipo'][tipo_label] = queryset.filter(tipo=tipo_key).count()
    
    # Estatísticas por prioridade
    for prioridade_key, prioridade_label in Processo.PRIORIDADE_CHOICES:
        stats['por_prioridade'][prioridade_label] = queryset.filter(prioridade=prioridade_key).count()
    
    context = {
        'processos': queryset.select_related('cliente').order_by('-data_cadastro'),
        'stats': stats,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'status': status,
            'tipo': tipo,
            'cliente': cliente_id,
        },
        'clientes': Cliente.objects.filter(ativo=True).order_by('nome')
    }
    
    return render(request, 'processos/relatorio.html', context)


@login_required
def prazos_vencendo(request):
    """Lista prazos que estão vencendo"""
    hoje = timezone.now().date()
    dias = int(request.GET.get('dias', 7))
    
    prazos = Prazo.objects.filter(
        processo__ativo=True,
        cumprido=False,
        data_vencimento__lte=hoje + timedelta(days=dias)
    ).select_related('processo', 'processo__cliente').order_by('data_vencimento')
    
    context = {
        'prazos': prazos,
        'dias': dias,
        'hoje': hoje,
    }
    
    return render(request, 'processos/prazos_vencendo.html', context)


@login_required
def processo_exportar(request):
    """Exporta lista de processos para CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="processos.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Número', 'Título', 'Cliente', 'Status', 'Tipo', 'Prioridade',
        'Vara', 'Comarca', 'Data Cadastro', 'Valor Causa'
    ])
    
    processos = Processo.objects.filter(ativo=True).select_related('cliente').order_by('numero')
    
    for processo in processos:
        writer.writerow([
            processo.numero,
            processo.titulo,
            processo.cliente.nome,
            processo.get_status_display(),
            processo.get_tipo_display(),
            processo.get_prioridade_display(),
            processo.vara,
            processo.comarca,
            processo.data_cadastro.strftime('%d/%m/%Y'),
            processo.valor_causa or ''
        ])
    
    return response
