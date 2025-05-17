// Track current active section
let currentActiveTag = null;

// Setup intersection observer for tag highlighting
function setupScrollTracking() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const tag = entry.target.dataset.tag;
            const tagItem = document.querySelector(`.tag-item[data-tag="${tag}"]`);
            
            if (entry.isIntersecting) {
                // Update current active tag
                currentActiveTag = tag;
                
                // Remove active class from all tags
                document.querySelectorAll('.tag-item').forEach(item => {
                    item.classList.remove('active');
                });
                
                // Add active class to current tag
                if (tagItem) {
                    tagItem.classList.add('active');
                    // Ensure the active tag is visible in the sidebar
                    tagItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
        });
    }, {
        rootMargin: '-20% 0px -79% 0px',
        threshold: [0, 0.25, 0.5, 0.75, 1]
    });

    // Observe all section markers
    document.querySelectorAll('.tag-section-marker').forEach(marker => {
        observer.observe(marker);
    });
}

// Setup tag click navigation
function setupTagNavigation() {
    document.querySelectorAll('.tag-item').forEach(item => {
        item.addEventListener('click', () => {
            const tag = item.dataset.tag;
            const section = document.getElementById(`tag-section-${tag}`);
            if (section) {
                // Remove active class from all tags
                document.querySelectorAll('.tag-item').forEach(tagItem => {
                    tagItem.classList.remove('active');
                });
                
                // Add active class to clicked tag
                item.classList.add('active');
                
                // Scroll to section
                section.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Setup precise scroll tracking
function setupPreciseScrollTracking() {
    const mainContent = document.querySelector('.main-content');
    mainContent.addEventListener('scroll', () => {
        // Find all tag sections
        const sections = document.querySelectorAll('.tag-section');
        
        // Get the current scroll position
        const scrollPosition = mainContent.scrollTop + mainContent.offsetHeight * 0.2;
        
        // Find the current section
        let currentSection = null;
        sections.forEach(section => {
            if (section.offsetTop <= scrollPosition) {
                currentSection = section;
            }
        });
        
        if (currentSection) {
            const tag = currentSection.querySelector('.tag-section-marker').dataset.tag;
            if (tag !== currentActiveTag) {
                // Update active tag
                document.querySelectorAll('.tag-item').forEach(item => {
                    item.classList.remove('active');
                    if (item.dataset.tag === tag) {
                        item.classList.add('active');
                        currentActiveTag = tag;
                    }
                });
            }
        }
    });
}

// Initialize all navigation features when the page loads
document.addEventListener('DOMContentLoaded', () => {
    setupScrollTracking();
    setupTagNavigation();
    setupPreciseScrollTracking();
}); 