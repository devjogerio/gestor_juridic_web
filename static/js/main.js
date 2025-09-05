// Sistema de Gestão Jurídica - JavaScript Principal

// Configurações globais
const CONFIG = {
    CSRF_TOKEN: document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
    BASE_URL: window.location.origin,
    DEBOUNCE_DELAY: 300,
    TOAST_DURATION: 5000
};

// Utilitários
const Utils = {
    /**
     * Função de debounce para otimizar chamadas de API
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Formatar moeda brasileira
     */
    formatCurrency: function(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },

    /**
     * Formatar data brasileira
     */
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    },

    /**
     * Formatar CPF/CNPJ
     */
    formatDocument: function(value) {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length === 11) {
            return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
        } else if (numbers.length === 14) {
            return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
        }
        return value;
    },

    /**
     * Formatar telefone
     */
    formatPhone: function(value) {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length === 10) {
            return numbers.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
        } else if (numbers.length === 11) {
            return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
        }
        return value;
    },

    /**
     * Formatar CEP
     */
    formatCEP: function(value) {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length === 8) {
            return numbers.replace(/(\d{5})(\d{3})/, '$1-$2');
        }
        return value;
    },

    /**
     * Validar email
     */
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * Mostrar loading spinner
     */
    showLoading: function(element) {
        const spinner = '<span class="loading-spinner me-2"></span>';
        element.innerHTML = spinner + element.innerHTML;
        element.disabled = true;
    },

    /**
     * Esconder loading spinner
     */
    hideLoading: function(element, originalText) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
};

// Sistema de Notificações
const Notifications = {
    /**
     * Mostrar toast de sucesso
     */
    success: function(message) {
        this.show(message, 'success');
    },

    /**
     * Mostrar toast de erro
     */
    error: function(message) {
        this.show(message, 'danger');
    },

    /**
     * Mostrar toast de aviso
     */
    warning: function(message) {
        this.show(message, 'warning');
    },

    /**
     * Mostrar toast de informação
     */
    info: function(message) {
        this.show(message, 'info');
    },

    /**
     * Mostrar toast genérico
     */
    show: function(message, type = 'info') {
        const toastContainer = this.getToastContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: CONFIG.TOAST_DURATION
        });
        
        toast.show();
        
        // Remove o toast do DOM após ser escondido
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    },

    /**
     * Obter ou criar container de toasts
     */
    getToastContainer: function() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        return container;
    }
};

// Sistema de Busca AJAX
const Search = {
    /**
     * Configurar busca em tempo real
     */
    setupLiveSearch: function(inputSelector, resultsSelector, url, minLength = 2) {
        const input = document.querySelector(inputSelector);
        const results = document.querySelector(resultsSelector);
        
        if (!input || !results) return;
        
        const debouncedSearch = Utils.debounce((query) => {
            if (query.length >= minLength) {
                this.performSearch(query, url, results);
            } else {
                results.innerHTML = '';
                results.style.display = 'none';
            }
        }, CONFIG.DEBOUNCE_DELAY);
        
        input.addEventListener('input', (e) => {
            debouncedSearch(e.target.value.trim());
        });
        
        // Esconder resultados ao clicar fora
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !results.contains(e.target)) {
                results.style.display = 'none';
            }
        });
    },

    /**
     * Realizar busca AJAX
     */
    performSearch: function(query, url, resultsContainer) {
        fetch(`${url}?q=${encodeURIComponent(query)}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': CONFIG.CSRF_TOKEN
            }
        })
        .then(response => response.json())
        .then(data => {
            this.displayResults(data, resultsContainer);
        })
        .catch(error => {
            console.error('Erro na busca:', error);
            Notifications.error('Erro ao realizar busca');
        });
    },

    /**
     * Exibir resultados da busca
     */
    displayResults: function(data, container) {
        if (!data.results || data.results.length === 0) {
            container.innerHTML = '<div class="p-3 text-muted">Nenhum resultado encontrado</div>';
        } else {
            const resultsHTML = data.results.map(item => `
                <div class="search-result-item p-2 border-bottom cursor-pointer" data-id="${item.id}">
                    <div class="fw-bold">${item.title}</div>
                    <div class="text-muted small">${item.subtitle || ''}</div>
                </div>
            `).join('');
            container.innerHTML = resultsHTML;
            
            // Adicionar eventos de clique nos resultados
            container.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', () => {
                    const id = item.dataset.id;
                    const title = item.querySelector('.fw-bold').textContent;
                    this.selectResult(id, title);
                    container.style.display = 'none';
                });
            });
        }
        
        container.style.display = 'block';
    },

    /**
     * Selecionar resultado da busca
     */
    selectResult: function(id, title) {
        // Implementar lógica específica para cada tipo de busca
        console.log('Resultado selecionado:', { id, title });
    }
};

// Sistema de Formulários
const Forms = {
    /**
     * Configurar validação de formulários
     */
    setupValidation: function() {
        // Validação do Bootstrap
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', (event) => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
        
        // Máscaras de input
        this.setupInputMasks();
        
        // Validação em tempo real
        this.setupRealTimeValidation();
    },

    /**
     * Configurar máscaras de input
     */
    setupInputMasks: function() {
        // CPF/CNPJ
        document.querySelectorAll('[data-mask="document"]').forEach(input => {
            input.addEventListener('input', (e) => {
                e.target.value = Utils.formatDocument(e.target.value);
            });
        });
        
        // Telefone
        document.querySelectorAll('[data-mask="phone"]').forEach(input => {
            input.addEventListener('input', (e) => {
                e.target.value = Utils.formatPhone(e.target.value);
            });
        });
        
        // CEP
        document.querySelectorAll('[data-mask="cep"]').forEach(input => {
            input.addEventListener('input', (e) => {
                e.target.value = Utils.formatCEP(e.target.value);
            });
        });
        
        // Moeda
        document.querySelectorAll('[data-mask="currency"]').forEach(input => {
            input.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, '');
                value = (value / 100).toFixed(2);
                e.target.value = Utils.formatCurrency(value);
            });
        });
    },

    /**
     * Configurar validação em tempo real
     */
    setupRealTimeValidation: function() {
        // Email
        document.querySelectorAll('input[type="email"]').forEach(input => {
            input.addEventListener('blur', (e) => {
                const isValid = Utils.validateEmail(e.target.value);
                if (e.target.value && !isValid) {
                    e.target.classList.add('is-invalid');
                    this.showFieldError(e.target, 'Email inválido');
                } else {
                    e.target.classList.remove('is-invalid');
                    this.hideFieldError(e.target);
                }
            });
        });
    },

    /**
     * Mostrar erro em campo
     */
    showFieldError: function(field, message) {
        this.hideFieldError(field);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    },

    /**
     * Esconder erro em campo
     */
    hideFieldError: function(field) {
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    },

    /**
     * Submeter formulário via AJAX
     */
    submitAjax: function(form, successCallback, errorCallback) {
        const formData = new FormData(form);
        const submitBtn = form.querySelector('[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        Utils.showLoading(submitBtn);
        
        fetch(form.action, {
            method: form.method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': CONFIG.CSRF_TOKEN
            }
        })
        .then(response => response.json())
        .then(data => {
            Utils.hideLoading(submitBtn, originalText);
            if (data.success) {
                if (successCallback) successCallback(data);
                Notifications.success(data.message || 'Operação realizada com sucesso!');
            } else {
                if (errorCallback) errorCallback(data);
                Notifications.error(data.message || 'Erro ao processar solicitação');
            }
        })
        .catch(error => {
            Utils.hideLoading(submitBtn, originalText);
            console.error('Erro:', error);
            if (errorCallback) errorCallback(error);
            Notifications.error('Erro de conexão');
        });
    }
};

// Sistema de Modais
const Modals = {
    /**
     * Abrir modal de confirmação
     */
    confirm: function(title, message, onConfirm, onCancel) {
        const modalId = 'confirm-modal-' + Date.now();
        const modalHTML = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-danger" id="confirm-btn">Confirmar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        const modalElement = document.getElementById(modalId);
        const modal = new bootstrap.Modal(modalElement);
        
        // Eventos
        modalElement.querySelector('#confirm-btn').addEventListener('click', () => {
            if (onConfirm) onConfirm();
            modal.hide();
        });
        
        modalElement.addEventListener('hidden.bs.modal', () => {
            if (onCancel) onCancel();
            modalElement.remove();
        });
        
        modal.show();
    },

    /**
     * Carregar conteúdo via AJAX em modal
     */
    loadContent: function(url, modalSelector) {
        const modal = document.querySelector(modalSelector);
        const modalBody = modal.querySelector('.modal-body');
        
        modalBody.innerHTML = '<div class="text-center"><div class="loading-spinner"></div> Carregando...</div>';
        
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': CONFIG.CSRF_TOKEN
            }
        })
        .then(response => response.text())
        .then(html => {
            modalBody.innerHTML = html;
            // Reconfigurar formulários no modal
            Forms.setupValidation();
        })
        .catch(error => {
            console.error('Erro ao carregar conteúdo:', error);
            modalBody.innerHTML = '<div class="alert alert-danger">Erro ao carregar conteúdo</div>';
        });
    }
};

// Sistema de Tabelas
const Tables = {
    /**
     * Configurar ordenação de tabelas
     */
    setupSorting: function(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (!table) return;
        
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sortTable(table, header.dataset.sort);
            });
        });
    },

    /**
     * Ordenar tabela
     */
    sortTable: function(table, column) {
        // Implementar lógica de ordenação
        console.log('Ordenando tabela por:', column);
    },

    /**
     * Configurar seleção múltipla
     */
    setupMultiSelect: function(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (!table) return;
        
        const selectAll = table.querySelector('#select-all');
        const checkboxes = table.querySelectorAll('input[type="checkbox"][name="selected_items"]');
        
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                checkboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
                this.updateBulkActions();
            });
        }
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkActions();
            });
        });
    },

    /**
     * Atualizar ações em lote
     */
    updateBulkActions: function() {
        const selected = document.querySelectorAll('input[type="checkbox"][name="selected_items"]:checked');
        const bulkActions = document.querySelector('.bulk-actions');
        
        if (bulkActions) {
            if (selected.length > 0) {
                bulkActions.style.display = 'block';
                bulkActions.querySelector('.selected-count').textContent = selected.length;
            } else {
                bulkActions.style.display = 'none';
            }
        }
    }
};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Configurar formulários
    Forms.setupValidation();
    
    // Configurar tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Configurar popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Configurar confirmações de exclusão
    document.querySelectorAll('[data-confirm-delete]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const message = this.dataset.confirmDelete || 'Tem certeza que deseja excluir este item?';
            Modals.confirm(
                'Confirmar Exclusão',
                message,
                () => {
                    if (this.tagName === 'A') {
                        window.location.href = this.href;
                    } else if (this.form) {
                        this.form.submit();
                    }
                }
            );
        });
    });
    
    // Configurar auto-hide para alertas
    setTimeout(() => {
        document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            setTimeout(() => {
                bsAlert.close();
            }, CONFIG.TOAST_DURATION);
        });
    }, 1000);
    
    console.log('Sistema de Gestão Jurídica inicializado com sucesso!');
});

// Exportar para uso global
window.GestaoJuridica = {
    Utils,
    Notifications,
    Search,
    Forms,
    Modals,
    Tables,
    CONFIG
};