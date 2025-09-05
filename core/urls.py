from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Página inicial - Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Configurações
    path('configuracoes/', views.ConfiguracoesView.as_view(), name='configuracoes'),
    
    # Perfil do usuário
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    
    # Busca global
    path('busca/', views.BuscaGlobalView.as_view(), name='busca_global'),
]