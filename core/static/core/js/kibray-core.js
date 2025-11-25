/**
 * Kibray Core JavaScript
 * 
 * Global namespace and reusable modules for the Kibray app.
 * Handles photo galleries, modals, toast notifications, etc.
 */

// Global namespace
window.Kibray = window.Kibray || {};

/**
 * Toast Notification System
 */
Kibray.Toast = {
    show: function(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const icons = {
            success: 'check-circle-fill',
            error: 'exclamation-triangle-fill',
            warning: 'exclamation-circle-fill',
            info: 'info-circle-fill'
        };
        
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };
        
        const toast = document.createElement('div');
        toast.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 min-w-[300px] animate-slide-in`;
        toast.innerHTML = `
            <i class="bi bi-${icons[type]} text-xl"></i>
            <span class="flex-1">${message}</span>
            <button onclick="this.parentElement.remove()" class="hover:bg-white/20 rounded p-1 transition">
                <i class="bi bi-x-lg"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        if (duration > 0) {
            setTimeout(() => toast.remove(), duration);
        }
        
        return toast;
    }
};

/**
 * Photo Gallery Module
 * Handles photo editing, deletion, and annotation rendering
 */
Kibray.PhotoGallery = {
    init: function() {
        console.log('[Kibray.PhotoGallery] Initializing...');
        
        // Attach event listeners to edit buttons
        document.querySelectorAll('.photo-edit-btn').forEach(btn => {
            btn.addEventListener('click', this.handleEdit.bind(this));
        });
        
        // Attach event listeners to delete buttons
        document.querySelectorAll('.photo-delete-btn').forEach(btn => {
            btn.addEventListener('click', this.handleDelete.bind(this));
        });
        
        // Initialize thumbnail annotations
        this.initThumbnails();
        
        console.log('[Kibray.PhotoGallery] Initialized successfully');
    },
    
    handleEdit: function(e) {
        const btn = e.currentTarget;
        const photoId = btn.dataset.photoId;
        const imageUrl = btn.dataset.imageUrl;
        const photoItem = btn.closest('[data-photo-id]');
        const scriptTag = photoItem.querySelector('.photo-annotations-data');
        const annotations = scriptTag ? scriptTag.textContent.trim() : '[]';
        
        console.log('[PhotoGallery] Edit clicked:', { photoId, imageUrl });
        
        // Call global editor function if it exists
        if (typeof window.openPhotoEditor === 'function') {
            window.openPhotoEditor(imageUrl, photoId, annotations);
        } else {
            console.warn('[PhotoGallery] openPhotoEditor function not found');
            Kibray.Toast.show('Photo editor not available', 'error');
        }
    },
    
    handleDelete: function(e) {
        const btn = e.currentTarget;
        const photoId = btn.dataset.photoId;
        
        if (!confirm('¿Eliminar esta foto permanentemente? / Delete this photo permanently?')) {
            return;
        }
        
        console.log('[PhotoGallery] Delete clicked:', photoId);
        
        // Call global delete function if it exists
        if (typeof window.deletePhoto === 'function') {
            window.deletePhoto(photoId);
        } else {
            console.warn('[PhotoGallery] deletePhoto function not found');
            Kibray.Toast.show('Delete function not available', 'error');
        }
    },
    
    initThumbnails: function() {
        console.log('[PhotoGallery] Initializing thumbnails...');
        
        document.querySelectorAll('[data-photo-id]').forEach(photoItem => {
            const photoId = photoItem.dataset.photoId;
            const scriptTag = photoItem.querySelector('.photo-annotations-data');
            
            if (!scriptTag || !scriptTag.textContent.trim()) {
                return;
            }
            
            let annotations = null;
            try {
                annotations = JSON.parse(scriptTag.textContent);
            } catch (e) {
                console.error(`[PhotoGallery] Failed to parse annotations for photo ${photoId}:`, e);
                return;
            }
            
            if (Array.isArray(annotations) && annotations.length > 0) {
                this.redrawThumbnail(photoId, annotations);
            }
        });
        
        console.log('[PhotoGallery] Thumbnails initialized');
    },
    
    redrawThumbnail: function(photoId, annotations) {
        const photoItem = document.querySelector(`[data-photo-id="${photoId}"]`);
        if (!photoItem) return;
        
        const canvas = photoItem.querySelector('.photo-annotations-canvas');
        const img = photoItem.querySelector('img');
        if (!canvas || !img) return;
        
        const ctx = canvas.getContext('2d');
        canvas.width = img.naturalWidth || img.width || 500;
        canvas.height = img.naturalHeight || img.height || 500;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (!annotations || annotations.length === 0) return;
        
        annotations.forEach(ann => {
            ctx.strokeStyle = ann.color || '#dc2626';
            ctx.fillStyle = ann.color || '#dc2626';
            ctx.lineWidth = ann.lineWidth || 3;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            
            if (ann.type === 'line') {
                ctx.beginPath();
                ctx.moveTo(ann.x1, ann.y1);
                ctx.lineTo(ann.x2, ann.y2);
                ctx.stroke();
            } else if (ann.type === 'arrow') {
                const headLength = 20;
                const angle = Math.atan2(ann.y2 - ann.y1, ann.x2 - ann.x1);
                
                // Draw line
                ctx.beginPath();
                ctx.moveTo(ann.x1, ann.y1);
                ctx.lineTo(ann.x2, ann.y2);
                ctx.stroke();
                
                // Draw arrowhead
                ctx.beginPath();
                ctx.moveTo(ann.x2, ann.y2);
                ctx.lineTo(
                    ann.x2 - headLength * Math.cos(angle - Math.PI / 6),
                    ann.y2 - headLength * Math.sin(angle - Math.PI / 6)
                );
                ctx.lineTo(
                    ann.x2 - headLength * Math.cos(angle + Math.PI / 6),
                    ann.y2 - headLength * Math.sin(angle + Math.PI / 6)
                );
                ctx.closePath();
                ctx.fill();
            } else if (ann.type === 'text') {
                ctx.font = `${ann.fontSize || 24}px Arial`;
                ctx.fillText(ann.text, ann.x, ann.y);
            }
        });
    }
};

/**
 * Form Utilities
 */
Kibray.Forms = {
    // Add client-side validation helpers
    validateRequired: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return true;
        
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('border-red-500');
                isValid = false;
            } else {
                field.classList.remove('border-red-500');
            }
        });
        
        return isValid;
    }
};

/**
 * Auto-initialize on DOM ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Kibray] Core JS loaded');
    
    // Initialize photo gallery if photos exist
    if (document.querySelector('.photo-edit-btn') || document.querySelector('.photo-delete-btn')) {
        Kibray.PhotoGallery.init();
    }
    
    // Add animation classes
    document.body.classList.add('fade-in');
});

// Export for backward compatibility
window.KibrayToast = Kibray.Toast;
window.KibrayPhotoGallery = Kibray.PhotoGallery;
