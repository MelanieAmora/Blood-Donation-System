/**
 * Custom JavaScript for enhancing UI interactivity on inventory management page
 */

document.addEventListener('DOMContentLoaded', function () {
    // Auto-focus on the first input in the Add Inventory modal when shown
    var addInventoryModal = document.getElementById('addInventoryModal');
    if (addInventoryModal) {
        addInventoryModal.addEventListener('shown.bs.modal', function () {
            var firstInput = addInventoryModal.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });
    }

    // Confirmation dialog for delete buttons
    var deleteButtons = document.querySelectorAll('a.btn-danger[href*="delete-inventory"]');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (event) {
            var confirmed = confirm('Are you sure you want to delete this inventory item?');
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    // Optional: Add fade out effect for success messages
    var alertSuccess = document.querySelector('.alert-success');
    if (alertSuccess) {
        setTimeout(function () {
            alertSuccess.classList.add('fade');
            setTimeout(function () {
                alertSuccess.remove();
            }, 500);
        }, 3000);
    }
});
