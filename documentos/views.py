# -*- coding: utf-8 -*-
"""
Views para o módulo de Documentos

Este módulo contém as views para gerenciamento de documentos jurídicos.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import os
import csv
from datetime import datetime, timedelta

from .models import Documento, CategoriaDocumento, TagDocumento, HistoricoDocumento
from .forms import DocumentoForm, CategoriaDocumentoForm, DocumentoFiltroForm
from processos.models import Processo
from clientes.models import Cliente


class DocumentoListView(LoginRequiredMixin, ListView):
    """
    View para listagem de documentos
    """
    model = Documento
    template_name = 'documentos/documento_list.html'
    context_object_name = 'documentos'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtra documentos baseado nos parâmetros de busca"""
        queryset = Documento.objects.select_related(
            'processo', 'cliente', 'categoria'
        ).prefetch_related('tags').order_by('-data_upload')
        
        # Aplicar filtros do formulário
        form = DocumentoFiltroForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(nome__icontains=search) |
                    Q(descricao__icontains=search) |
                    Q(processo__numero__icontains=search) |
                    Q(cliente__nome__icontains=search)
                )
            
            tipo = form.cleaned_data.get('tipo')
            if tipo:
                queryset = queryset.filter(tipo=tipo)
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            categoria = form.cleaned_data.get('categoria')
            if categoria:
                queryset = queryset.filter(categoria=categoria)
            
            processo = form.cleaned_data.get('processo')
            if processo:
                queryset = queryset.filter(processo=processo)
            
            cliente = form.cleaned_data.get('cliente')
            if cliente:
                queryset = queryset.filter(cliente=cliente)
            
            data_inicio = form.cleaned_data.get('data_inicio')
            if data_inicio:
                queryset = queryset.filter(data_upload__gte=data_inicio)
            
            data_fim = form.cleaned_data.get('data_fim')
            if data_fim:
                queryset = queryset.filter(data_upload__lte=data_fim)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        context['form'] = DocumentoFiltroForm(self.request.GET)
        context['total_documentos'] = self.get_queryset().count()
        return context


class DocumentoDetailView(LoginRequiredMixin, DetailView):
    """
    View para detalhes do documento
    """
    model = Documento
    template_name = 'documentos/documento_detail.html'
    context_object_name = 'documento'
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        documento = self.get_object()
        
        # Histórico do documento
        context['historico'] = HistoricoDocumento.objects.filter(
            documento=documento
        ).order_by('-data_acao')
        
        # Documentos relacionados (mesmo processo)
        if documento.processo:
            context['documentos_relacionados'] = Documento.objects.filter(
                processo=documento.processo
            ).exclude(pk=documento.pk)[:5]
        
        return context


class DocumentoCreateView(LoginRequiredMixin, CreateView):
    """
    View para criação de documento
    """
    model = Documento
    form_class = DocumentoForm
    template_name = 'documentos/documento_form.html'
    
    def form_valid(self, form):
        """Processa formulário válido"""
        documento = form.save(commit=False)
        documento.usuario_upload = self.request.user
        documento.save()
        form.save_m2m()  # Salva tags many-to-many
        
        # Criar registro no histórico
        HistoricoDocumento.objects.create(
            documento=documento,
            usuario=self.request.user,
            acao='upload',
            descricao=f'Documento {documento.nome} foi enviado'
        )
        
        messages.success(self.request, 'Documento cadastrado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """URL de redirecionamento após sucesso"""
        return reverse('documentos:documento_detail', kwargs={'pk': self.object.pk})


class DocumentoUpdateView(LoginRequiredMixin, UpdateView):
    """
    View para edição de documento
    """
    model = Documento
    form_class = DocumentoForm
    template_name = 'documentos/documento_form.html'
    
    def form_valid(self, form):
        """Processa formulário válido"""
        # Criar registro no histórico
        HistoricoDocumento.objects.create(
            documento=self.object,
            usuario=self.request.user,
            acao='edicao',
            descricao=f'Documento {self.object.nome} foi editado'
        )
        
        messages.success(self.request, 'Documento atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """URL de redirecionamento após sucesso"""
        return reverse('documentos:documento_detail', kwargs={'pk': self.object.pk})


class DocumentoDeleteView(LoginRequiredMixin, DeleteView):
    """
    View para exclusão de documento
    """
    model = Documento
    template_name = 'documentos/documento_confirm_delete.html'
    success_url = reverse_lazy('documentos:documento_list')
    
    def delete(self, request, *args, **kwargs):
        """Processa exclusão"""
        documento = self.get_object()
        
        # Criar registro no histórico antes de excluir
        HistoricoDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            acao='exclusao',
            descricao=f'Documento {documento.nome} foi excluído'
        )
        
        # Remover arquivo físico
        if documento.arquivo and os.path.isfile(documento.arquivo.path):
            os.remove(documento.arquivo.path)
        
        messages.success(request, 'Documento excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


class CategoriaDocumentoCreateView(LoginRequiredMixin, CreateView):
    """
    View para criação de categoria de documento
    """
    model = CategoriaDocumento
    form_class = CategoriaDocumentoForm
    template_name = 'documentos/categoria_form.html'
    success_url = reverse_lazy('documentos:categoria_list')
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Categoria criada com sucesso!')
        return super().form_valid(form)


class CategoriaDocumentoUpdateView(LoginRequiredMixin, UpdateView):
    """
    View para edição de categoria de documento
    """
    model = CategoriaDocumento
    form_class = CategoriaDocumentoForm
    template_name = 'documentos/categoria_form.html'
    success_url = reverse_lazy('documentos:categoria_list')
    
    def form_valid(self, form):
        """Processa formulário válido"""
        messages.success(self.request, 'Categoria atualizada com sucesso!')
        return super().form_valid(form)


@login_required
def documento_dashboard(request):
    """
    Dashboard de documentos
    """
    # Estatísticas gerais
    total_documentos = Documento.objects.count()
    documentos_pendentes = Documento.objects.filter(status='pendente').count()
    documentos_vencendo = Documento.objects.filter(
        data_vencimento__lte=timezone.now().date() + timedelta(days=7),
        data_vencimento__gte=timezone.now().date(),
        status='ativo'
    ).count()
    
    # Documentos por categoria
    documentos_por_categoria = CategoriaDocumento.objects.annotate(
        total=Count('documento')
    ).order_by('-total')[:5]
    
    # Documentos recentes
    documentos_recentes = Documento.objects.select_related(
        'processo', 'cliente', 'categoria'
    ).order_by('-data_upload')[:10]
    
    # Documentos vencendo
    documentos_vencendo_lista = Documento.objects.filter(
        data_vencimento__lte=timezone.now().date() + timedelta(days=7),
        data_vencimento__gte=timezone.now().date(),
        status='ativo'
    ).select_related('processo', 'cliente').order_by('data_vencimento')[:10]
    
    context = {
        'total_documentos': total_documentos,
        'documentos_pendentes': documentos_pendentes,
        'documentos_vencendo': documentos_vencendo,
        'documentos_por_categoria': documentos_por_categoria,
        'documentos_recentes': documentos_recentes,
        'documentos_vencendo_lista': documentos_vencendo_lista,
    }
    
    return render(request, 'documentos/dashboard.html', context)


@login_required
def documento_busca_ajax(request):
    """
    Busca AJAX de documentos
    """
    query = request.GET.get('q', '')
    documentos = []
    
    if query:
        docs = Documento.objects.filter(
            Q(nome__icontains=query) |
            Q(descricao__icontains=query)
        ).select_related('processo', 'cliente')[:10]
        
        for doc in docs:
            documentos.append({
                'id': doc.id,
                'nome': doc.nome,
                'tipo': doc.get_tipo_display(),
                'processo': doc.processo.numero if doc.processo else '',
                'cliente': doc.cliente.nome if doc.cliente else '',
                'url': reverse('documentos:documento_detail', kwargs={'pk': doc.pk})
            })
    
    return JsonResponse({'documentos': documentos})


@login_required
def documento_download(request, pk):
    """
    Download de documento
    """
    documento = get_object_or_404(Documento, pk=pk)
    
    if not documento.arquivo:
        raise Http404("Arquivo não encontrado")
    
    # Criar registro no histórico
    HistoricoDocumento.objects.create(
        documento=documento,
        usuario=request.user,
        acao='download',
        descricao=f'Download do documento {documento.nome}'
    )
    
    # Preparar resposta para download
    response = HttpResponse(
        documento.arquivo.read(),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{documento.nome}"'
    
    return response


@login_required
def documento_relatorio(request):
    """
    Relatório de documentos
    """
    # Filtros do relatório
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    categoria = request.GET.get('categoria')
    
    # Query base
    documentos = Documento.objects.select_related(
        'processo', 'cliente', 'categoria'
    ).order_by('-data_upload')
    
    # Aplicar filtros
    if data_inicio:
        documentos = documentos.filter(data_upload__gte=data_inicio)
    if data_fim:
        documentos = documentos.filter(data_upload__lte=data_fim)
    if tipo:
        documentos = documentos.filter(tipo=tipo)
    if status:
        documentos = documentos.filter(status=status)
    if categoria:
        documentos = documentos.filter(categoria_id=categoria)
    
    # Estatísticas
    total_documentos = documentos.count()
    documentos_por_tipo = documentos.values('tipo').annotate(
        total=Count('id')
    ).order_by('-total')
    documentos_por_status = documentos.values('status').annotate(
        total=Count('id')
    ).order_by('-total')
    
    context = {
        'documentos': documentos,
        'total_documentos': total_documentos,
        'documentos_por_tipo': documentos_por_tipo,
        'documentos_por_status': documentos_por_status,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'tipo': tipo,
            'status': status,
            'categoria': categoria,
        },
        'categorias': CategoriaDocumento.objects.all(),
        'tipos': Documento.TIPO_CHOICES,
        'status_choices': Documento.STATUS_CHOICES,
    }
    
    return render(request, 'documentos/relatorio.html', context)


@login_required
def documento_exportar(request):
    """
    Exportar documentos para CSV
    """
    # Aplicar mesmos filtros do relatório
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    categoria = request.GET.get('categoria')
    
    documentos = Documento.objects.select_related(
        'processo', 'cliente', 'categoria'
    ).order_by('-data_upload')
    
    if data_inicio:
        documentos = documentos.filter(data_upload__gte=data_inicio)
    if data_fim:
        documentos = documentos.filter(data_upload__lte=data_fim)
    if tipo:
        documentos = documentos.filter(tipo=tipo)
    if status:
        documentos = documentos.filter(status=status)
    if categoria:
        documentos = documentos.filter(categoria_id=categoria)
    
    # Criar resposta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="documentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Nome', 'Tipo', 'Status', 'Categoria', 'Processo', 'Cliente',
        'Data Upload', 'Data Vencimento', 'Tamanho', 'Usuário Upload'
    ])
    
    for doc in documentos:
        writer.writerow([
            doc.nome,
            doc.get_tipo_display(),
            doc.get_status_display(),
            doc.categoria.nome if doc.categoria else '',
            doc.processo.numero if doc.processo else '',
            doc.cliente.nome if doc.cliente else '',
            doc.data_upload.strftime('%d/%m/%Y %H:%M'),
            doc.data_vencimento.strftime('%d/%m/%Y') if doc.data_vencimento else '',
            doc.tamanho_formatado(),
            doc.usuario_upload.get_full_name() if doc.usuario_upload else ''
        ])
    
    return response


@login_required
def categoria_list(request):
    """
    Lista de categorias de documentos
    """
    categorias = CategoriaDocumento.objects.annotate(
        total_documentos=Count('documento')
    ).order_by('nome')
    
    context = {
        'categorias': categorias
    }
    
    return render(request, 'documentos/categoria_list.html', context)


@login_required
def documentos_vencendo(request):
    """
    Lista de documentos vencendo
    """
    dias = int(request.GET.get('dias', 7))
    
    documentos = Documento.objects.filter(
        data_vencimento__lte=timezone.now().date() + timedelta(days=dias),
        data_vencimento__gte=timezone.now().date(),
        status='ativo'
    ).select_related('processo', 'cliente').order_by('data_vencimento')
    
    context = {
        'documentos': documentos,
        'dias': dias
    }
    
    return render(request, 'documentos/documentos_vencendo.html', context)
