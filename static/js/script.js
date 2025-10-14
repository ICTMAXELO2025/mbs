// JavaScript for interactive features
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.style.borderColor = '#dc3545';
                } else {
                    field.style.borderColor = '#ddd';
                }
            });
            
            if (!valid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Todo item interactions
    const todoItems = document.querySelectorAll('.todo-item');
    todoItems.forEach(item => {
        const toggleBtn = item.querySelector('.toggle-todo');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() {
                item.classList.toggle('completed');
            });
        }
    });

    // Confirmation for delete actions
    const deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Dynamic form for sending to all employees
    const receiverSelect = document.getElementById('receiver_id');
    if (receiverSelect) {
        receiverSelect.addEventListener('change', function() {
            const allEmployeesNote = document.getElementById('all-employees-note');
            if (allEmployeesNote) {
                if (this.value === 'all') {
                    allEmployeesNote.style.display = 'block';
                } else {
                    allEmployeesNote.style.display = 'none';
                }
            }
        });
    }
});