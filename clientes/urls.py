from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # Lista de clientes
    path('', views.ClienteListView.as_view(), name='cliente_list'),
    
    # Detalhes do cliente
    path('<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    
    # Criar novo cliente
    path('novo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    
    # Editar cliente
    path('<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    
    # Excluir cliente
    path('<int:pk>/excluir/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
    
    # Buscar clientes (AJAX)
    path('buscar/', views.cliente_busca_ajax, name='cliente_buscar'),
    
    # Relatório de clientes
    path('relatorio/', views.cliente_relatorio, name='cliente_relatorio'),
    
    # Dashboard de clientes
    path('dashboard/', views.cliente_dashboard, name='cliente_dashboard'),
    
    # Toggle status do cliente
    path('<int:pk>/toggle-status/', views.cliente_toggle_status, name='cliente_toggle_status'),
    
    # Exportar clientes
    path('exportar/', views.cliente_exportar, name='cliente_exportar'),
]