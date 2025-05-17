// Copy functionality for base URL and other copyable elements
function setupCopyButtons() {
    document.querySelectorAll('.copy-button').forEach(button => {
        button.addEventListener('click', async () => {
            const textToCopy = button.getAttribute('data-copy');
            const copyIcon = button.querySelector('.copy-icon');
            const tickIcon = button.querySelector('.tick-icon');
            
            try {
                await navigator.clipboard.writeText(textToCopy);
                
                // Show tick icon
                copyIcon.style.display = 'none';
                tickIcon.style.display = 'block';
                button.classList.add('copied');
                
                // Reset after 2 seconds
                setTimeout(() => {
                    copyIcon.style.display = 'block';
                    tickIcon.style.display = 'none';
                    button.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy text:', err);
            }
        });
    });
}

// Initialize copy buttons when the page loads
document.addEventListener('DOMContentLoaded', setupCopyButtons); 