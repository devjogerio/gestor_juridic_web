from django.urls import path
from . import views

app_name = 'processos'

urlpatterns = [
    # Lista de processos
    path('', views.ProcessoListView.as_view(), name='processo_list'),
    
    # Detalhes do processo
    path('<int:pk>/', views.ProcessoDetailView.as_view(), name='processo_detail'),
    
    # Criar novo processo
    path('novo/', views.ProcessoCreateView.as_view(), name='processo_create'),
    
    # Editar processo
    path('<int:pk>/editar/', views.ProcessoUpdateView.as_view(), name='processo_update'),
    
    # Excluir processo
    path('<int:pk>/excluir/', views.ProcessoDeleteView.as_view(), name='processo_delete'),
    
    # Andamentos do processo
    path('<int:processo_id>/andamentos/novo/', views.AndamentoCreateView.as_view(), name='andamento_create'),
    path('andamentos/<int:pk>/editar/', views.AndamentoUpdateView.as_view(), name='andamento_update'),
    
    # Prazos do processo
    path('<int:processo_id>/prazos/novo/', views.PrazoCreateView.as_view(), name='prazo_create'),
    path('prazos/<int:pk>/editar/', views.PrazoUpdateView.as_view(), name='prazo_update'),
    
    # Buscar processos (AJAX)
    path('buscar/', views.processo_busca_ajax, name='processo_buscar'),
    
    # Relatórios
    path('relatorio/', views.processo_relatorio, name='processo_relatorio'),
    
    # Dashboard
    path('dashboard/', views.processo_dashboard, name='processo_dashboard'),
    
    # Prazos vencendo
    path('prazos-vencendo/', views.prazos_vencendo, name='prazos_vencendo'),
    
    # Exportar
    path('exportar/', views.processo_exportar, name='processo_exportar'),
]