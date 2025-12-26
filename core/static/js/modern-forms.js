/* ============================================
   MODERN FORMS - JavaScript Enhancements
   Date pickers, validation, file uploads
   ============================================ */

(function() {
    'use strict';
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initDatePickers();
        initFileUploads();
        initFormValidation();
        initSelectWrappers();
        initInputIcons();
        initCharacterCounters();
        initFormAutoSave();
    });
    
    /* ============================================
       DATE PICKER INITIALIZATION
       Using Flatpickr if available
       ============================================ */
    function initDatePickers() {
        // Check if Flatpickr is loaded
        if (typeof flatpickr !== 'undefined') {
            // Date inputs
            document.querySelectorAll('input[type="date"]:not(.no-picker)').forEach(function(input) {
                wrapDateInput(input);
                flatpickr(input, {
                    dateFormat: 'Y-m-d',
                    altInput: true,
                    altFormat: 'd M Y',
                    locale: getLocale(),
                    allowInput: true,
                    disableMobile: false,
                    animate: true,
                    onOpen: function() {
                        input.closest('.date-picker-wrapper')?.classList.add('active');
                    },
                    onClose: function() {
                        input.closest('.date-picker-wrapper')?.classList.remove('active');
                    }
                });
            });
            
            // Datetime inputs
            document.querySelectorAll('input[type="datetime-local"]:not(.no-picker)').forEach(function(input) {
                wrapDateInput(input);
                flatpickr(input, {
                    enableTime: true,
                    dateFormat: 'Y-m-d H:i',
                    altInput: true,
                    altFormat: 'd M Y, H:i',
                    locale: getLocale(),
                    time_24hr: true,
                    allowInput: true
                });
            });
            
            // Time inputs
            document.querySelectorAll('input[type="time"]:not(.no-picker)').forEach(function(input) {
                flatpickr(input, {
                    enableTime: true,
                    noCalendar: true,
                    dateFormat: 'H:i',
                    time_24hr: true,
                    allowInput: true
                });
            });
        } else {
            // Fallback: Just wrap date inputs with icon
            document.querySelectorAll('input[type="date"], input[type="datetime-local"]').forEach(function(input) {
                wrapDateInput(input);
            });
        }
    }
    
    function wrapDateInput(input) {
        if (input.closest('.date-picker-wrapper')) return;
        
        const wrapper = document.createElement('div');
        wrapper.className = 'date-picker-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        
        const icon = document.createElement('i');
        icon.className = 'bi bi-calendar3 calendar-icon';
        wrapper.appendChild(icon);
        
        // Make icon clickable
        icon.style.cursor = 'pointer';
        icon.addEventListener('click', function() {
            input.focus();
            if (input._flatpickr) {
                input._flatpickr.open();
            }
        });
    }
    
    function getLocale() {
        const lang = document.documentElement.lang || navigator.language;
        if (lang.startsWith('es')) {
            return {
                weekdays: {
                    shorthand: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
                    longhand: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
                },
                months: {
                    shorthand: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
                    longhand: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                },
                firstDayOfWeek: 1,
                rangeSeparator: ' a ',
                time_24hr: true
            };
        }
        return 'default';
    }
    
    /* ============================================
       FILE UPLOAD ENHANCEMENT
       ============================================ */
    function initFileUploads() {
        document.querySelectorAll('.modern-file-upload, .file-upload-zone').forEach(function(zone) {
            const input = zone.querySelector('input[type="file"]');
            if (!input) return;
            
            // Click to upload
            zone.addEventListener('click', function(e) {
                if (e.target !== input) {
                    input.click();
                }
            });
            
            // Drag and drop
            ['dragenter', 'dragover'].forEach(function(event) {
                zone.addEventListener(event, function(e) {
                    e.preventDefault();
                    zone.classList.add('drag-over');
                });
            });
            
            ['dragleave', 'drop'].forEach(function(event) {
                zone.addEventListener(event, function(e) {
                    e.preventDefault();
                    zone.classList.remove('drag-over');
                });
            });
            
            zone.addEventListener('drop', function(e) {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    input.files = files;
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
            
            // Show selected files
            input.addEventListener('change', function() {
                const fileText = zone.querySelector('.upload-text, .file-name');
                if (fileText && input.files.length > 0) {
                    const names = Array.from(input.files).map(f => f.name).join(', ');
                    fileText.innerHTML = '<i class="bi bi-check-circle text-success me-2"></i>' + names;
                }
            });
        });
    }
    
    /* ============================================
       FORM VALIDATION ENHANCEMENT
       ============================================ */
    function initFormValidation() {
        document.querySelectorAll('form').forEach(function(form) {
            // Real-time validation on blur
            form.querySelectorAll('input, select, textarea').forEach(function(field) {
                field.addEventListener('blur', function() {
                    validateField(field);
                });
                
                // Clear error on input
                field.addEventListener('input', function() {
                    clearFieldError(field);
                });
            });
            
            // Form submission validation
            form.addEventListener('submit', function(e) {
                let isValid = true;
                
                form.querySelectorAll('[required]').forEach(function(field) {
                    if (!validateField(field)) {
                        isValid = false;
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    // Focus first invalid field
                    const firstError = form.querySelector('.has-error input, .has-error select, .has-error textarea');
                    if (firstError) {
                        firstError.focus();
                        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                } else {
                    // Add loading state to submit button
                    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                    if (submitBtn) {
                        submitBtn.classList.add('is-loading');
                        submitBtn.disabled = true;
                    }
                }
            });
        });
    }
    
    function validateField(field) {
        const group = field.closest('.modern-form-group, .form-group, .mb-3');
        
        // Skip non-required empty fields
        if (!field.hasAttribute('required') && !field.value) {
            return true;
        }
        
        let isValid = true;
        let message = '';
        
        // Required check
        if (field.hasAttribute('required') && !field.value.trim()) {
            isValid = false;
            message = 'Este campo es requerido';
        }
        
        // Email validation
        if (isValid && field.type === 'email' && field.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
                isValid = false;
                message = 'Ingrese un email válido';
            }
        }
        
        // Min length
        if (isValid && field.minLength > 0 && field.value.length < field.minLength) {
            isValid = false;
            message = `Mínimo ${field.minLength} caracteres`;
        }
        
        // Max length
        if (isValid && field.maxLength > 0 && field.value.length > field.maxLength) {
            isValid = false;
            message = `Máximo ${field.maxLength} caracteres`;
        }
        
        // Number range
        if (isValid && field.type === 'number') {
            const value = parseFloat(field.value);
            if (field.min && value < parseFloat(field.min)) {
                isValid = false;
                message = `El valor mínimo es ${field.min}`;
            }
            if (field.max && value > parseFloat(field.max)) {
                isValid = false;
                message = `El valor máximo es ${field.max}`;
            }
        }
        
        // Pattern validation
        if (isValid && field.pattern && field.value) {
            const regex = new RegExp(field.pattern);
            if (!regex.test(field.value)) {
                isValid = false;
                message = field.title || 'Formato inválido';
            }
        }
        
        if (!isValid) {
            showFieldError(field, message, group);
        } else {
            clearFieldError(field, group);
        }
        
        return isValid;
    }
    
    function showFieldError(field, message, group) {
        field.classList.add('is-invalid');
        if (group) {
            group.classList.add('has-error');
            group.classList.remove('has-success');
            
            // Remove existing error message
            const existingError = group.querySelector('.error-message, .invalid-feedback');
            if (existingError) {
                existingError.remove();
            }
            
            // Add error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            field.parentNode.appendChild(errorDiv);
        }
    }
    
    function clearFieldError(field, group) {
        field.classList.remove('is-invalid');
        group = group || field.closest('.modern-form-group, .form-group, .mb-3');
        if (group) {
            group.classList.remove('has-error');
            const errorDiv = group.querySelector('.error-message');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    }
    
    /* ============================================
       SELECT WRAPPER ENHANCEMENT
       ============================================ */
    function initSelectWrappers() {
        document.querySelectorAll('select:not([multiple])').forEach(function(select) {
            if (select.closest('.modern-select-wrapper')) return;
            
            const wrapper = document.createElement('div');
            wrapper.className = 'modern-select-wrapper';
            select.parentNode.insertBefore(wrapper, select);
            wrapper.appendChild(select);
        });
    }
    
    /* ============================================
       INPUT ICON ENHANCEMENT
       ============================================ */
    function initInputIcons() {
        // Add icons to specific input types
        const iconMap = {
            'email': 'bi-envelope',
            'tel': 'bi-telephone',
            'url': 'bi-link-45deg',
            'search': 'bi-search',
            'password': 'bi-lock'
        };
        
        Object.keys(iconMap).forEach(function(type) {
            document.querySelectorAll('input[type="' + type + '"]:not(.no-icon)').forEach(function(input) {
                if (input.closest('.input-with-icon')) return;
                
                const wrapper = document.createElement('div');
                wrapper.className = 'input-with-icon';
                input.parentNode.insertBefore(wrapper, input);
                wrapper.appendChild(input);
                
                const icon = document.createElement('i');
                icon.className = 'bi ' + iconMap[type] + ' input-icon';
                wrapper.appendChild(icon);
            });
        });
    }
    
    /* ============================================
       CHARACTER COUNTER
       ============================================ */
    function initCharacterCounters() {
        document.querySelectorAll('textarea[maxlength], input[maxlength]').forEach(function(field) {
            const maxLength = parseInt(field.getAttribute('maxlength'));
            if (maxLength <= 0) return;
            
            const counter = document.createElement('div');
            counter.className = 'character-counter';
            counter.style.cssText = 'font-size: 0.75rem; color: #9ca3af; text-align: right; margin-top: 4px;';
            
            function updateCounter() {
                const remaining = maxLength - field.value.length;
                counter.textContent = field.value.length + ' / ' + maxLength;
                counter.style.color = remaining < 20 ? '#f59e0b' : remaining < 10 ? '#ef4444' : '#9ca3af';
            }
            
            field.parentNode.appendChild(counter);
            field.addEventListener('input', updateCounter);
            updateCounter();
        });
    }
    
    /* ============================================
       AUTO-SAVE (Optional)
       ============================================ */
    function initFormAutoSave() {
        document.querySelectorAll('form[data-autosave]').forEach(function(form) {
            const key = 'autosave_' + (form.id || form.action);
            let saveTimeout;
            
            // Load saved data
            const savedData = localStorage.getItem(key);
            if (savedData) {
                try {
                    const data = JSON.parse(savedData);
                    Object.keys(data).forEach(function(name) {
                        const field = form.elements[name];
                        if (field && !field.value) {
                            field.value = data[name];
                        }
                    });
                } catch (e) {}
            }
            
            // Save on change
            form.addEventListener('input', function() {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(function() {
                    const data = {};
                    new FormData(form).forEach(function(value, key) {
                        data[key] = value;
                    });
                    localStorage.setItem(key, JSON.stringify(data));
                }, 1000);
            });
            
            // Clear on submit
            form.addEventListener('submit', function() {
                localStorage.removeItem(key);
            });
        });
    }
    
    /* ============================================
       UTILITY: Format Currency Input
       ============================================ */
    window.formatCurrencyInput = function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^\d.]/g, '');
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }
            if (parts[1] && parts[1].length > 2) {
                value = parts[0] + '.' + parts[1].substring(0, 2);
            }
            e.target.value = value;
        });
    };
    
    /* ============================================
       UTILITY: Format Phone Input
       ============================================ */
    window.formatPhoneInput = function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) {
                value = value.substring(0, 10);
            }
            if (value.length >= 6) {
                value = '(' + value.substring(0, 3) + ') ' + value.substring(3, 6) + '-' + value.substring(6);
            } else if (value.length >= 3) {
                value = '(' + value.substring(0, 3) + ') ' + value.substring(3);
            }
            e.target.value = value;
        });
    };
    
})();
