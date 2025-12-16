// Notes Web UI - Minimal JavaScript
// Most interactions are handled by htmx

document.addEventListener('DOMContentLoaded', function() {
    // Auto-resize textarea as content grows
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
});
