document.addEventListener("DOMContentLoaded", function () {
    updateCartDisplay();  // ✅ Refresh cart when the page loads
});

function loadItemDetail(itemId) {
    fetch(`/item/${itemId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("detail-name").innerText = data.name;
            document.getElementById("detail-price").innerText = data.price;
            document.getElementById("detail-description").innerText = data.description;

            // Display product image
            const imageElement = document.getElementById("detail-image");
            if (data.image) {
                imageElement.src = data .image;
                imageElement.style.display = "block";  // Show image
            } else {
                imageElement.style.display = "none";   // Hide if no image is available
            }

            // Bind add-to-cart functionality
            document.getElementById("detail-add-cart").setAttribute("onclick", `addToBasket(${data.id})`);

            // Show popup
            document.getElementById("product-detail").style.display = "block";
        })
        .catch(error => {
            console.error('Error loading product details:', error);
            alert('Unable to load product details, please try again later.');
        });
}

function closeItemDetail() {
    document.getElementById("product-detail").style.display = "none";  // Close popup
}

// Add to cart
function addToBasket(itemId) {
    fetch(`/add-to-basket/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),  // ✅ Pass CSRF token
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartDisplay();  // ✅ Update cart
        } else {
            alert('Failed to add: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error adding to cart:', error);
        alert('Network error, please try again later.');
    });
}

// Update cart display
function updateCartDisplay() {
    fetch('/get-cart/')
        .then(response => response.json())
        .then(data => {
            const cartHtml = data.items.map(item => `
                <div class="cart-item" data-item-id="${item.id}">
                    <div class="item-info">
                        <span class="item-name">${item.name}</span>
                        <div class="quantity-control">
                            <button class="btn-quantity" onclick="decreaseQuantity(${item.id})">-</button>
                            <span class="quantity">${item.quantity}</span>
                            <button class="btn-quantity" onclick="addToBasket(${item.id})">+</button>
                        </div>
                    </div>
                    <div class="item-actions">
                        <span class="price">£${item.total_price.toFixed(2)}</span>
                        <button class="btn-remove" onclick="removeItem(${item.id})">Remove</button>
                    </div>
                </div>
            `).join('');

            const cartElement = document.getElementById('cart-items');
            if (data.items.length) {
                cartElement.innerHTML = cartHtml;
            } else {
                cartElement.innerHTML = '<p class="empty-cart">Cart is empty</p>';
            }

            // ✅ Update total price display
            document.getElementById("cart-total-price").innerText = `Total: £${data.total_price.toFixed(2)}`;
        })
        .catch(error => console.error("❌ Failed to fetch cart data:", error));
}

// Decrease quantity
function decreaseQuantity(itemId) {
    fetch(`/decrease-from-basket/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),  // ✅ Replace with method to get CSRF token
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || `HTTP ${response.status}`); });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            updateCartDisplay();  // ✅ Update cart
        } else {
            alert(`Failed to decrease quantity: ${data.error}`);
        }
    })
    .catch(error => {
        console.error("❌ Failed to decrease item quantity:", error);
        alert("Network error, please try again later.");
    });
}

// Completely remove item
function removeItem(itemId) {
    fetch(`/remove-from-basket/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartDisplay();
        } else {
            alert("❌ Failed to remove item: " + data.error);
        }
    })
    .catch(error => {
        console.error("❌ Error removing item:", error);
        alert("❌ Network error, please try again later.");
    });
}

function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.startsWith("csrftoken=")) {
                cookieValue = decodeURIComponent(cookie.substring("csrftoken=".length));
                break;
            }
        }
    }
    return cookieValue;
}

// Checkout function
function checkout() {
    fetch('/checkout/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),  // Get CSRF token
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Checkout successful!');
            updateCartDisplay(); // Update cart after successful checkout
        } else {
            alert('❌ Checkout failed: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('❌ Checkout error:', error);
        alert('Network error, please try again later.');
    });
}