<script>
        // Simple JavaScript for interactive elements
        document.addEventListener('DOMContentLoaded', function() {
            const buttons = document.querySelectorAll('.btn');
            
            buttons.forEach(button => {
                button.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-2px)';
                });
                
                button.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                });
            });
            
            // Search functionality placeholder
            const searchButton = document.querySelector('.search-box button');
            const searchInput = document.querySelector('.search-box input');
            
            searchButton.addEventListener('click', function() {
                if (searchInput.value.trim() !== '') {
                    alert(`Searching for recipes with: ${searchInput.value}`);
                    searchInput.value = '';
                } else {
                    alert('Please enter some ingredients to search');
                }
            });
            
            // Allow pressing Enter to search
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchButton.click();
                }
            });
        });
    </script>