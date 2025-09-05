# -*- coding: utf-8 -*-
"""
Views para o módulo de Clientes

Este módulo contém as views para gerenciamento de clientes.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Cliente
from .forms import ClienteForm


class ClienteListView(LoginRequiredMixin, ListView):
    """View para listagem de clientes"""
    model = Cliente
    template_name = 'clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 20
    ordering = ['-data_cadastro']
    
    def get_queryset(self):
        """Filtra clientes baseado na busca"""
        queryset = Cliente.objects.filter(ativo=True)
        
        # Busca por termo
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) |
                Q(cpf_cnpj__icontains=search) |
                Q(email__icontains=search) |
                Q(telefone__icontains=search)
            )
        
        # Filtro por tipo
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Filtro por status
        status = self.request.GET.get('status')
        if status == 'ativo':
            queryset = queryset.filter(ativo=True)
        elif status == 'inativo':
            queryset = queryset.filter(ativo=False)
        
        return queryset.annotate(
            processos_count=Count('processos', filter=Q(processos__ativo=True))
        )
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['total_clientes'] = Cliente.objects.filter(ativo=True).count()
        return context


class ClienteDetailView(LoginRequiredMixin, DetailView):
    """View para detalhes do cliente"""
    model = Cliente
    template_name = 'clientes/detalhe.html'
    context_object_name = 'cliente'
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        cliente = self.get_object()
        
        # Processos do cliente
        context['processos'] = cliente.processos.filter(ativo=True)[:10]
        context['total_processos'] = cliente.processos.filter(ativo=True).count()
        
        # Documentos do cliente
        context['documentos'] = cliente.documentos.all()[:10]
        context['total_documentos'] = cliente.documentos.count()
        
        # Movimentações financeiras
        context['financeiro'] = cliente.financeiro.all()[:10]
        context['total_financeiro'] = cliente.financeiro.count()
        
        return context


class ClienteCreateView(LoginRequiredMixin, CreateView):
    """View para criação de cliente"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes:lista')
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Cliente cadastrado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Processa formulário inválido"""
        messages.error(self.request, 'Erro ao cadastrar cliente. Verifique os dados informados.')
        return super().form_invalid(form)


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    """View para edição de cliente"""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'
    
    def get_success_url(self):
        """Retorna URL de sucesso"""
        return reverse_lazy('clientes:detalhe', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Cliente atualizado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Processa formulário inválido"""
        messages.error(self.request, 'Erro ao atualizar cliente. Verifique os dados informados.')
        return super().form_invalid(form)


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    """View para exclusão de cliente"""
    model = Cliente
    template_name = 'clientes/confirmar_exclusao.html'
    success_url = reverse_lazy('clientes:lista')
    
    def delete(self, request, *args, **kwargs):
        """Desativa cliente ao invés de excluir"""
        self.object = self.get_object()
        self.object.ativo = False
        self.object.save()
        messages.success(request, 'Cliente desativado com sucesso!')
        return redirect(self.success_url)


# Views baseadas em função

@login_required
def cliente_dashboard(request):
    """Dashboard de clientes"""
    context = {
        'total_clientes': Cliente.objects.filter(ativo=True).count(),
        'clientes_pf': Cliente.objects.filter(ativo=True, tipo='pf').count(),
        'clientes_pj': Cliente.objects.filter(ativo=True, tipo='pj').count(),
        'clientes_recentes': Cliente.objects.filter(ativo=True).order_by('-data_cadastro')[:5],
        'clientes_com_processos': Cliente.objects.filter(
            ativo=True, 
            processos__ativo=True
        ).distinct().count(),
    }
    return render(request, 'clientes/dashboard.html', context)


@login_required
@require_http_methods(["GET"])
def cliente_busca_ajax(request):
    """Busca de clientes via AJAX"""
    term = request.GET.get('term', '')
    
    if len(term) < 2:
        return JsonResponse({'results': []})
    
    clientes = Cliente.objects.filter(
        Q(nome__icontains=term) |
        Q(cpf_cnpj__icontains=term) |
        Q(email__icontains=term),
        ativo=True
    )[:10]
    
    results = []
    for cliente in clientes:
        results.append({
            'id': cliente.id,
            'text': f"{cliente.nome} - {cliente.cpf_cnpj}",
            'nome': cliente.nome,
            'cpf_cnpj': cliente.cpf_cnpj,
            'email': cliente.email,
            'telefone': cliente.telefone,
            'tipo': cliente.get_tipo_display()
        })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["POST"])
def cliente_toggle_status(request, pk):
    """Alterna status ativo/inativo do cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    cliente.ativo = not cliente.ativo
    cliente.save()
    
    status_text = 'ativado' if cliente.ativo else 'desativado'
    messages.success(request, f'Cliente {status_text} com sucesso!')
    
    return JsonResponse({
        'success': True,
        'ativo': cliente.ativo,
        'message': f'Cliente {status_text} com sucesso!'
    })


@login_required
def cliente_relatorio(request):
    """Relatório de clientes"""
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo')
    
    queryset = Cliente.objects.filter(ativo=True)
    
    # Aplicar filtros
    if data_inicio:
        queryset = queryset.filter(data_cadastro__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data_cadastro__lte=data_fim)
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    
    # Estatísticas
    stats = {
        'total': queryset.count(),
        'pessoa_fisica': queryset.filter(tipo='pf').count(),
        'pessoa_juridica': queryset.filter(tipo='pj').count(),
        'com_processos': queryset.filter(processos__ativo=True).distinct().count(),
        'sem_processos': queryset.exclude(processos__ativo=True).count(),
    }
    
    context = {
        'clientes': queryset.order_by('-data_cadastro'),
        'stats': stats,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'tipo': tipo,
        }
    }
    
    return render(request, 'clientes/relatorio.html', context)


@login_required
def cliente_exportar(request):
    """Exporta lista de clientes para CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clientes.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Nome', 'CPF/CNPJ', 'Tipo', 'Email', 'Telefone', 
        'Cidade', 'Estado', 'Data Cadastro', 'Status'
    ])
    
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    
    for cliente in clientes:
        writer.writerow([
            cliente.nome,
            cliente.cpf_cnpj,
            cliente.get_tipo_display(),
            cliente.email,
            cliente.telefone,
            cliente.cidade,
            cliente.estado,
            cliente.data_cadastro.strftime('%d/%m/%Y'),
            'Ativo' if cliente.ativo else 'Inativo'
        ])
    
    return response
