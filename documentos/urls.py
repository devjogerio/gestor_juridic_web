from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    # Lista de documentos
    path('', views.DocumentoListView.as_view(), name='documento_list'),
    
    # Detalhes do documento
    path('<int:pk>/', views.DocumentoDetailView.as_view(), name='documento_detail'),
    
    # Criar novo documento
    path('novo/', views.DocumentoCreateView.as_view(), name='documento_create'),
    
    # Editar documento
    path('<int:pk>/editar/', views.DocumentoUpdateView.as_view(), name='documento_update'),
    
    # Excluir documento
    path('<int:pk>/excluir/', views.DocumentoDeleteView.as_view(), name='documento_delete'),
    
    # Categorias
    path('categorias/nova/', views.CategoriaDocumentoCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaDocumentoUpdateView.as_view(), name='categoria_update'),
    
    # Dashboard
    path('dashboard/', views.documento_dashboard, name='documento_dashboard'),
    
    # Relatórios e exportação
    path('relatorio/', views.documento_relatorio, name='documento_relatorio'),
    path('exportar/', views.documento_exportar, name='documento_exportar'),
]