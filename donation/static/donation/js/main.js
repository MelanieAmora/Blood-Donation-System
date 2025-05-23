// Main JavaScript file for Blood Donation System
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    initializeBootstrapComponents();
    
    // Initialize animations
    initializeAnimations();
    
    // Initialize dashboard features
    if (document.querySelector('.dashboard-header')) {
        initializeDashboard();
    }
});

function initializeBootstrapComponents() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

function initializeAnimations() {
    // Add fade-in animation to cards
    document.querySelectorAll('.card').forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
        card.classList.add('fade-in');
    });

    // Add hover animations to buttons
    document.querySelectorAll('.btn').forEach(function(btn) {
        btn.addEventListener('mouseover', function() {
            this.style.transform = 'translateY(-2px)';
        });
        btn.addEventListener('mouseout', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

function initializeDashboard() {
    // Update time-based elements
    updateTimeBasedElements();
    
    // Initialize progress bars with animation
    initializeProgressBars();
    
    // Add interactivity to stat cards
    initializeStatCards();
}

function updateTimeBasedElements() {
    // Update next donation countdown if element exists
    const countdownElement = document.querySelector('.next-donation-countdown');
    if (countdownElement) {
        const targetDate = new Date(countdownElement.dataset.targetDate);
        updateCountdown(countdownElement, targetDate);
        setInterval(() => updateCountdown(countdownElement, targetDate), 1000);
    }
}

function updateCountdown(element, targetDate) {
    const now = new Date();
    const difference = targetDate - now;
    
    if (difference > 0) {
        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        
        element.innerHTML = `${days}d ${hours}h ${minutes}m`;
    } else {
        element.innerHTML = 'Ready to donate!';
    }
}

function initializeProgressBars() {
    document.querySelectorAll('.progress-bar').forEach(function(bar) {
        const targetWidth = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = targetWidth;
        }, 100);
    });
}

function initializeStatCards() {
    document.querySelectorAll('.stat-card').forEach(function(card) {
        // Add click effect
        card.addEventListener('click', function() {
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'translateY(-5px)';
            }, 100);
        });
        
        // Add hover effect
        card.addEventListener('mouseover', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseout', function() {
            this.style.transform = 'translateY(0)';
        });
    });
} 