document.addEventListener("DOMContentLoaded", function () {
    const tabs = document.querySelectorAll(".nav-links .tab");
    const tabContents = document.querySelectorAll(".tab-content");
    const orderSidebar = document.querySelector(".orders-sidebar");
    const itemSidebar = document.querySelector(".items-sidebar");

    const addCategoryTab = document.getElementById("add-category-tab");
    if (addCategoryTab) {
        addCategoryTab.addEventListener("click", function () {
            document.getElementById("add-category-form").style.display = "block";
            document.getElementById("new-category-name").focus();
        });
    }

    function switchTab(tabName) {
        tabs.forEach(tab => tab.classList.remove("active"));
        tabContents.forEach(content => content.style.display = "none");

        document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add("active");
        document.getElementById(tabName).style.display = "block";

        // ✅ Get the Management sidebar
        const managementSidebar = document.querySelector(".management-sidebar");

        // ✅ Hide all sidebars
        orderSidebar.style.display = "none";
        itemSidebar.style.display = "none";
        if (managementSidebar) managementSidebar.style.display = "none";

        // ✅ Conditionally show sidebars
        if (tabName === "items") {
            itemSidebar.style.display = "block";
            loadCategories();  // ✅ Load categories
        } else if (tabName === "orders") {
            orderSidebar.style.display = "block";
        } else if (tabName === "management") {
            if (managementSidebar) {
                managementSidebar.style.display = "block"; // ✅ Show Management sidebar
            }
            loadReviews(); // ✅ Load user reviews
        }
    }

    // ✅ Bind click events
    tabs.forEach(tab => {
        tab.addEventListener("click", function () {
            switchTab(this.getAttribute("data-tab"));
        });
    });

    // ✅ Initial loading
    loadCategories();
    loadItems();

    // ✅ Listen for file selection event
    const imageInput = document.getElementById("edit-item-image");
    const previewImage = document.getElementById("preview-item-image");

    if (imageInput) {
        imageInput.addEventListener("change", function (event) {
            const file = event.target.files[0];
            const preview = document.getElementById("preview-item-image");

            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    preview.src = e.target.result;
                    preview.style.display = "block";
                };
                reader.readAsDataURL(file);
            }
        });
    }
});

function updateOrderStatus(orderId, newStatus) {
    fetch(`/merchant/orders/update/${orderId}/`, {  // ✅ Ensure it matches the Django URL
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",  // ✅ Send FormData
            "X-CSRFToken": getCSRFToken()  // Ensure CSRF Token is included
        },
        body: `status=${encodeURIComponent(newStatus)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`✅ Order ${orderId} status updated to ${newStatus}`);
            location.reload(); // Refresh the page to update order status
        } else {
            alert(`❌ Update failed: ${data.error}`);
        }
    })
    .catch(error => {
        console.error("❌ Failed to update order status:", error);
        alert("❌ Network error, unable to update order status!");
    });
}

function loadCategories() {
    console.log("🚀 Fetching product categories...");
    fetch(`/merchant/categories/`, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
    .then(response => response.json())
    .then(data => {
        console.log("✅ Category data:", data.categories);  // **Debugging**

        const categorySidebar = document.querySelector(".items-sidebar");
        categorySidebar.innerHTML = '<a href="javascript:void(0);" class="category-link active" data-category-id="">All Products</a>';

        if (data.categories.length > 0) {
            data.categories.forEach(category => {
                categorySidebar.innerHTML += `<a href="javascript:void(0);" class="category-link" data-category-id="${category.id}">${category.name}</a>`;
            });
        } else {
            categorySidebar.innerHTML += `<p class="no-category">No categories available</p>`;
        }
        categorySidebar.innerHTML += `
                <a href="javascript:void(0);" id="add-category-tab" class="category-link add-category">+ Add Category</a>
                <div id="add-category-form" style="display: none; padding: 10px;">
                    <input type="text" id="new-category-name" placeholder="Enter category name">
                    <button onclick="submitCategory()">Submit</button>
                    <button onclick="hideCategoryForm()">Cancel</button>
                </div>
            `;

        setupCategoryClickEvents();  // ✅ Rebind click events after updating categories
        document.getElementById("add-category-tab").addEventListener("click", function () {
            document.getElementById("add-category-form").style.display = "block";
            document.getElementById("new-category-name").focus();
        });
    })
    .catch(error => console.error("❌ Failed to fetch categories:", error));
}

function setupCategoryClickEvents() {
    document.querySelectorAll(".category-link").forEach(link => {
        link.addEventListener("click", function () {
            // If the edit window is open, show a warning
            const editModal = document.getElementById("edit-item-modal");
            if (editModal.style.display === "block") {
                const confirmSwitch = confirm("You are editing a product. Switching categories will discard unsaved changes. Continue?");
                if (!confirmSwitch) return;
            }

            // Switch category
            document.querySelectorAll(".category-link").forEach(el => el.classList.remove("active"));
            this.classList.add("active");

            const categoryId = this.getAttribute("data-category-id");
            loadItems(categoryId);
        });
    });
}

// ✅ Bind "Enter" key event for adding categories
function setupAddCategoryEvents() {
    const categoryInput = document.getElementById("new-category-name");
    categoryInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            submitCategory();
        }
    });
}

// ✅ Submit new category
function submitCategory() {
    const categoryName = document.getElementById("new-category-name").value.trim();
    if (!categoryName) {
        alert("Please enter a category name!");
        return;
    }

    fetch(`/merchant/category/add/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),  // ✅ Ensure CSRF token exists
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `category_name=${encodeURIComponent(categoryName)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("✅ Category added successfully!");
            document.getElementById("add-category-form").style.display = "none";
            loadCategories();
        } else {
            alert("❌ Failed to add category: " + data.error);
        }
    })
    .catch(error => console.error("❌ Failed to add category:", error));
}

// Show add category form
function showCategoryForm() {
    document.getElementById("add-category-form").style.display = "block";
}

// Hide add category form
function hideCategoryForm() {
    document.getElementById("add-category-form").style.display = "none";
}

function loadItems(categoryId = "") {
    console.log(`🚀 Loading products for category ${categoryId}...`);
    fetch(`/merchant/manage_items/?category_id=${categoryId}`, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
    .then(response => response.json())
    .then(data => {
        const itemContainer = document.getElementById("item-list");
        itemContainer.innerHTML = "";  // Clear the product list

        if (data.items.length > 0) {
            data.items.forEach(item => {
                // ✅ Create product card
                let itemCard = document.createElement("div");
                itemCard.classList.add("item-card");

                // ✅ Create product image
                let img = document.createElement("img");
                img.src = item.image ? item.image : "/static/img/1.jpeg";
                img.alt = item.name;
                itemCard.appendChild(img);

                // ✅ Product information
                let itemInfo = document.createElement("div");
                itemInfo.classList.add("item-info");
                itemInfo.innerHTML = `
                    <h3>${item.name}</h3>
                    <p>ID: ${ item.id }</p>
                    <p>Price: £${item.price}</p>
                    <p>Category: ${item.category}</p>
                `;
                itemCard.appendChild(itemInfo);

                // ✅ Create "List/Delist" button
                let toggleBtn = document.createElement("button");
                toggleBtn.textContent = item.is_available ? "Delist" : "List";
                toggleBtn.classList.add("toggle-availability-btn");
                toggleBtn.onclick = () => toggleItemAvailability(item.id, item.is_available);
                itemCard.appendChild(toggleBtn);

                // ✅ Create "Edit" button
                let editBtn = document.createElement("button");
                editBtn.textContent = "✏️ Edit";
                editBtn.classList.add("edit-btn");
                editBtn.onclick = () => editItem(item.id);
                itemCard.appendChild(editBtn);

                // ✅ Create "Delete" button
                let deleteBtn = document.createElement("button");
                deleteBtn.textContent = "🗑️ Delete";
                deleteBtn.classList.add("delete-btn");
                deleteBtn.onclick = () => deleteItem(item.id);
                itemCard.appendChild(deleteBtn);

                // ✅ Add to product list
                itemContainer.appendChild(itemCard);
            });
        }
        let addItemCard = document.getElementById("add-item-card");
        if (!addItemCard) {
            addItemCard = document.createElement("div");
            addItemCard.id = "add-item-card";
            addItemCard.classList.add("item-card", "add-item-card");
            addItemCard.innerHTML = `<span class="add-icon">+</span>`;
            addItemCard.onclick = showAddItemForm;
            itemContainer.appendChild(addItemCard);
        }
    })
    .catch(error => console.error("Failed to fetch products:", error));
}

// List/Delist product
function toggleItemAvailability(itemId, isAvailable) {
    console.log(`🚀 Toggling product ID: ${itemId}, Current status: ${isAvailable}`);

    fetch(`/merchant/item/toggle/${itemId}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken(), "Content-Type": "application/json" },
        body: JSON.stringify({ is_available: !isAvailable })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("✅ Product status updated successfully!");

            // ✅ Reload products to ensure button bindings work correctly
            loadItems();
        } else {
            alert("❌ Update failed: " + data.error);
        }
    })
    .catch(error => console.error("❌ Failed to update product status:", error));
}

// Show edit product modal
function editItem(itemId = null, categoryId = "") {
    const itemIdField = document.getElementById("edit-item-id");
    const nameField = document.getElementById("edit-item-name");
    const priceField = document.getElementById("edit-item-price");
    const descriptionField = document.getElementById("edit-item-description");
    const categorySelect = document.getElementById("edit-item-category");
    const previewImage = document.getElementById("preview-item-image"); // ✅ Get the preview image element

    if (itemId) {
        // ✅ Edit mode
        fetch(`/merchant/item/details/${itemId}/`, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(response => response.json())
        .then(item => {
            console.log("📌 Retrieved product data:", item);

            itemIdField.value = item.id;
            nameField.value = item.name;
            priceField.value = item.price;
            descriptionField.value = item.description;

            categorySelect.innerHTML = "";
            item.categories.forEach(category => {
                let option = document.createElement("option");
                option.value = category.id;
                option.text = category.name;
                option.selected = category.id == item.category;
                categorySelect.appendChild(option);
            });

            // ✅ Display preview image if available
            if (previewImage) {
                if (item.image) {
                    previewImage.src = item.image;
                    previewImage.style.display = "block";
                } else {
                    previewImage.style.display = "none";
                }
            }

            document.getElementById("edit-item-modal").style.display = "flex";
            document.getElementById("edit-item-modal").style.justifyContent = "center";
            document.getElementById("edit-item-modal").style.alignItems = "center";
        })
        .catch(error => {
            console.error("❌ Failed to fetch product details:", error);
            alert("❌ An error occurred, please check if the API is correct!");
        });
    } else {
        // ✅ Add new product mode
        itemIdField.value = "";
        nameField.value = "";
        priceField.value = "";
        descriptionField.value = "";
        categorySelect.innerHTML = "";
        if (previewImage) previewImage.style.display = "none";

        fetch(`/merchant/categories/`, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(response => response.json())
        .then(data => {
            data.categories.forEach(category => {
                let option = document.createElement("option");
                option.value = category.id;
                option.text = category.name;
                option.selected = categoryId && category.id == categoryId;
                categorySelect.appendChild(option);
            });

            document.getElementById("edit-item-modal").style.display = "flex";
            document.getElementById("edit-item-modal").style.justifyContent = "center";
            document.getElementById("edit-item-modal").style.alignItems = "center";
        })
        .catch(error => console.error("❌ Failed to fetch category list:", error));
    }
}

// When adding a new product, pass in the currently selected category ID
function showAddItemForm() {
    let activeCategory = document.querySelector(".category-link.active");
    let categoryId = activeCategory ? activeCategory.getAttribute("data-category-id") : ""; // Avoid undefined
    if (categoryId === "undefined" || categoryId === null) {
        categoryId = ""; // Ensure it does not become undefined
    }

    console.log("📌 showAddItemForm called, category ID:", categoryId);
    editItem(null, categoryId); // Enter add product mode and pass the category ID
}

// Close modal
function closeEditItemModal() {
    document.getElementById("edit-item-modal").style.display = "none";
}

// Submit product edit
function saveItemEdit() {
    let itemId = document.getElementById("edit-item-id").value.trim() || "new"; // ✅ If empty, pass "new"
    const url = `/merchant/item/update/${itemId}/`;  // ✅ Ensure the URL is correct

    const name = document.getElementById("edit-item-name").value.trim();
    const price = parseFloat(document.getElementById("edit-item-price").value);
    const description = document.getElementById("edit-item-description").value.trim();
    const newCategory = parseInt(document.getElementById("edit-item-category").value, 10);
    const imageFile = document.getElementById("edit-item-image").files[0];

    // ✅ Form validation: Prevent submission of empty data
    if (!name) {
        alert("⚠️ Please enter the product name!");
        return;
    }
    if (!price || isNaN(price) || price <= 0) {
        alert("⚠️ Please enter a valid price!");
        return;
    }
    if (!newCategory) {
        alert("⚠️ Please select a product category!");
        return;
    }

    let formData = new FormData();
    formData.append("name", name);
    formData.append("price", price);
    formData.append("description", description);
    formData.append("category", newCategory);
    if (imageFile) {
        formData.append("image", imageFile);
    }

    fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken() },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || `HTTP ${response.status}`); });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(`✅ ${data.message}`);
            closeEditItemModal();
            loadItems(newCategory);
        } else {
            alert(`❌ Update failed: ${data.error}`);
        }
    })
    .catch(error => {
        console.error("❌ Failed to update product information:", error);
        alert("❌ Product update failed, please check the network or backend logs.");
    });
}

// Delete product
function deleteItem(itemId) {
    if (!confirm("Are you sure you want to delete this product?")) return;

    fetch(`/merchant/item/delete/${itemId}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken(), "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("✅ Product deleted!");
            loadItems();
        } else {
            alert("❌ Deletion failed: " + data.error);
        }
    })
    .catch(error => console.error("❌ Failed to delete product:", error));
}

// Fetch user reviews
function loadReviews() {
    console.log("🚀 Loading user reviews...");

    fetch("/merchant/reviews/")
        .then(response => response.json())
        .then(data => {
            console.log("✅ Retrieved review data:", data.reviews);  // **Debugging output**

            const reviewContainer = document.getElementById("review-list");
            reviewContainer.innerHTML = "";

            if (data.reviews.length === 0) {
                reviewContainer.innerHTML = "<p>No user reviews available</p>";
                return;
            }

            data.reviews.forEach(review => {
                let reviewCard = document.createElement("div");
                reviewCard.classList.add("review-card");

                reviewCard.innerHTML = `
                    <div class="review-header">
                        <strong>${review.username || "Anonymous"}</strong>
                        <span class="review-date">${review.timestamp}</span>
                    </div>
                    <div class="review-content">${review.comment || "No comment"}</div>
                    <div class="review-rating" data-rating="${review.rating}">
                        Rating: ${"⭐".repeat(review.rating)}
                    </div>
                `;
                reviewContainer.appendChild(reviewCard);
            });
        })
        .catch(error => {
            console.error("❌ Failed to fetch user reviews:", error);
            document.getElementById("review-list").innerHTML = "<p>Unable to load user reviews, please try again later.</p>";
        });
}

// Get CSRF token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith("csrftoken="))
        ?.split('=')[1];
}

