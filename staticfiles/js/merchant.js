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

        // Get the Management sidebar
        const managementSidebar = document.querySelector(".management-sidebar");

        // Hide all sidebars
        orderSidebar.style.display = "none";
        itemSidebar.style.display = "none";
        if (managementSidebar) managementSidebar.style.display = "none";

        // Show the relevant sidebar
        if (tabName === "items") {
            itemSidebar.style.display = "block";
            loadCategories();  // ✅ **Load categories**
        } else if (tabName === "orders") {
            orderSidebar.style.display = "block";
        } else if (tabName === "management") {
            if (managementSidebar) {
                managementSidebar.style.display = "block"; // ✅ **Show Management sidebar**
            }
            loadReviews(); // Load user reviews
        }
    }

    // Bind click events
    tabs.forEach(tab => {
        tab.addEventListener("click", function () {
            switchTab(this.getAttribute("data-tab"));
        });
    });

    // Initial load
    loadCategories();
    loadItems();

    // Listen for file selection events
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

        setupCategoryClickEvents();  // ✅ **Rebind click events after updating categories**
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
                const confirmSwitch = confirm("You are editing a product. Switching categories will discard unsaved changes. Do you want to continue?");
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

// ✅ Bind the `Enter` event for adding a new category
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
            "X-CSRFToken": getCSRFToken(),  // ✅ Ensure CSRF token is included
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

// Show category form
function showCategoryForm() {
    document.getElementById("add-category-form").style.display = "block";
}

// Hide category form
function hideCategoryForm() {
    document.getElementById("add-category-form").style.display = "none";
}

// Fetch user reviews
function loadReviews() {
    console.log("🚀 Loading user reviews...");

    fetch("/merchant/reviews/")
        .then(response => response.json())
        .then(data => {
            console.log("✅ Review data:", data.reviews);  // **Debugging**

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
                        <strong>${review.username || "Anonymous User"}</strong>
                        <span class="review-date">${review.timestamp}</span>
                    </div>
                    <div class="review-content">${review.comment || "No comments"}</div>
                    <div class="review-rating" data-rating="${review.rating}">
                        Rating: ${"⭐".repeat(review.rating)}
                    </div>
                `;
                reviewContainer.appendChild(reviewCard);
            });
        })
        .catch(error => {
            console.error("❌ Failed to fetch user reviews:", error);
            document.getElementById("review-list").innerHTML = "<p>Unable to load reviews. Please try again later.</p>";
        });
}

function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith("csrftoken="))
        ?.split('=')[1];
}