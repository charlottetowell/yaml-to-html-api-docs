// Handle endpoint expansion/collapse
document.querySelectorAll('.endpoint-preview').forEach(endpoint => {
    endpoint.addEventListener('click', (e) => {
        // Don't toggle if clicking inside a code block or table
        if (e.target.closest('.code-block') || e.target.closest('.parameter-table')) {
            return;
        }
        
        // Close any other open endpoints
        document.querySelectorAll('.endpoint-preview.expanded').forEach(openEndpoint => {
            if (openEndpoint !== endpoint) {
                openEndpoint.classList.remove('expanded');
            }
        });
        
        // Toggle current endpoint
        endpoint.classList.toggle('expanded');
    });
}); 