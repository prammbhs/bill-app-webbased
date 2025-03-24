// Enhanced Footer Component
document.addEventListener('DOMContentLoaded', function() {
    // Create footer element
    const footer = document.createElement('footer');
    footer.className = 'footer';
    
    // Set footer content with improved design
    footer.innerHTML = `
        <div class="footer-content">
            <div class="footer-logo">
                <i class="fas fa-receipt"></i> BillTracker
            </div>
            <p>&copy; 2025 BillTracker</p>
            <p>Designed and developed by 
                <a href="https://www.linkedin.com/in/paramjitpatel" target="_blank" rel="noopener">
                    Paramjit Patel
                </a> 
                <span class="reg-number">(12312522)</span>
            </p>
            <div class="footer-links">
                <a href="https://github.com/prammbhs" target="_blank" rel="noopener">
                    <i class="fab fa-github"></i> GitHub
                </a>
                <a href="https://paramjitpatel.me" target="_blank" rel="noopener">
                    <i class="fas fa-globe"></i> Portfolio
                </a>
            </div>
        </div>
    `;
    
    // Add footer styles
    const style = document.createElement('style');
    style.textContent = `
        .footer {
            background-color: white;
            padding: 20px 30px;
            text-align: center;
            border-top: 1px solid rgba(0,0,0,0.05);
            margin-left: var(--sidebar-width, 240px);
            transition: all 0.3s;
            font-size: 0.9rem;
            color: #666;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.03);
        }
        
        .footer-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        
        .footer-logo {
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--primary-color, #4361ee);
            margin-bottom: 5px;
        }
        
        .footer p {
            margin: 0;
        }
        
        .footer a {
            color: var(--primary-color, #4361ee);
            text-decoration: none;
            transition: all 0.2s;
        }
        
        .footer a:hover {
            color: var(--primary-dark, #3a56d4);
            text-decoration: underline;
        }
        
        .footer .reg-number {
            background: rgba(67, 97, 238, 0.1);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            color: var(--primary-color, #4361ee);
        }
        
        .footer-links {
            display: flex;
            gap: 15px;
            margin-top: 5px;
        }
        
        .footer-links a {
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .dark-mode .footer {
            background-color: #1e1e1e;
            color: #aaa;
            border-top-color: #333;
        }
        
        .dark-mode .footer-logo,
        .dark-mode .footer a {
            color: var(--secondary-color, #48bfe3);
        }
        
        .dark-mode .footer .reg-number {
            background: rgba(72, 191, 227, 0.2);
            color: var(--secondary-color, #48bfe3);
        }
        
        @media (max-width: 992px) {
            .footer {
                margin-left: 70px;
            }
        }
        
        @media (max-width: 576px) {
            .footer {
                margin-left: 0;
                padding-bottom: 80px;
            }
        }
    `;
    
    // Append footer and styles to the document
    document.head.appendChild(style);
    document.body.appendChild(footer);
    
    // Handle responsive footer
    const mediaQuery576 = window.matchMedia('(max-width: 576px)');
    const mediaQuery992 = window.matchMedia('(max-width: 992px)');
    
    function handleMediaQueryChange() {
        if (mediaQuery576.matches) {
            footer.style.marginLeft = '0';
            footer.style.paddingBottom = '80px';
        } else if (mediaQuery992.matches) {
            footer.style.marginLeft = '70px';
            footer.style.paddingBottom = '20px';
        } else {
            footer.style.marginLeft = 'var(--sidebar-width, 240px)';
            footer.style.paddingBottom = '20px';
        }
    }
    
    // Initial check
    handleMediaQueryChange();
    
    // Add listeners for responsive design
    mediaQuery576.addEventListener('change', handleMediaQueryChange);
    mediaQuery992.addEventListener('change', handleMediaQueryChange);
});