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

        // ✅ **获取 Management 侧边栏**
        const managementSidebar = document.querySelector(".management-sidebar");

        // ✅ **隐藏所有侧边栏**
        orderSidebar.style.display = "none";
        itemSidebar.style.display = "none";
        if (managementSidebar) managementSidebar.style.display = "none";

        // ✅ **选择性显示侧边栏**
        if (tabName === "items") {
            itemSidebar.style.display = "block";
            loadCategories();  // ✅ **加载类别**
        } else if (tabName === "orders") {
            orderSidebar.style.display = "block";
        } else if (tabName === "management") {
            if (managementSidebar) {
                managementSidebar.style.display = "block"; // ✅ **显示 Management 侧边栏**
            }
            loadReviews(); // ✅ **加载用户评论**
        }
    }

    // ✅ **绑定点击事件**
    tabs.forEach(tab => {
        tab.addEventListener("click", function () {
            switchTab(this.getAttribute("data-tab"));
        });
    });

    // ✅ **初始加载**
    loadCategories();
    loadItems();

    // ✅ 监听文件选择事件
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
    fetch(`/merchant/orders/update/${orderId}/`, {  // ✅ 确保和 Django URL 匹配
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",  // ✅ 传递 FormData
            "X-CSRFToken": getCSRFToken()  // 确保 CSRF Token 存在
        },
        body: `status=${encodeURIComponent(newStatus)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`✅ 订单 ${orderId} 状态已更新为 ${newStatus}`);
            location.reload(); // 刷新页面，更新订单状态
        } else {
            alert(`❌ 更新失败: ${data.error}`);
        }
    })
    .catch(error => {
        console.error("❌ 更新订单状态失败:", error);
        alert("❌ 网络错误，无法更新订单状态！");
    });
}


function loadCategories() {
    console.log("🚀 正在获取商品类别...");
    fetch(`/merchant/categories/`, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
    .then(response => response.json())
    .then(data => {
        console.log("✅ 类别数据:", data.categories);  // **调试**

        const categorySidebar = document.querySelector(".items-sidebar");
        categorySidebar.innerHTML = '<a href="javascript:void(0);" class="category-link active" data-category-id="">全部商品</a>';

        if (data.categories.length > 0) {
            data.categories.forEach(category => {
                categorySidebar.innerHTML += `<a href="javascript:void(0);" class="category-link" data-category-id="${category.id}">${category.name}</a>`;
            });
        } else {
            categorySidebar.innerHTML += `<p class="no-category">暂无商品类别</p>`;
        }
        categorySidebar.innerHTML += `
                <a href="javascript:void(0);" id="add-category-tab" class="category-link add-category">+ 新增类别</a>
                <div id="add-category-form" style="display: none; padding: 10px;">
                    <input type="text" id="new-category-name" placeholder="输入类别名称">
                    <button onclick="submitCategory()">提交</button>
                    <button onclick="hideCategoryForm()">取消</button>
                </div>
            `;

        setupCategoryClickEvents();  // ✅ **类别更新后重新绑定点击事件**
        document.getElementById("add-category-tab").addEventListener("click", function () {
            document.getElementById("add-category-form").style.display = "block";
            document.getElementById("new-category-name").focus();
        });
    })
    .catch(error => console.error("❌ 获取商品类别失败:", error));
}

function setupCategoryClickEvents() {
    document.querySelectorAll(".category-link").forEach(link => {
        link.addEventListener("click", function () {
            // 如果编辑窗口是打开的，弹出警告
            const editModal = document.getElementById("edit-item-modal");
            if (editModal.style.display === "block") {
                const confirmSwitch = confirm("您正在编辑商品，切换类别将丢失未保存的更改，是否继续？");
                if (!confirmSwitch) return;
            }

            // 切换类别
            document.querySelectorAll(".category-link").forEach(el => el.classList.remove("active"));
            this.classList.add("active");

            const categoryId = this.getAttribute("data-category-id");
            loadItems(categoryId);
        });
    });
}

// ✅ 绑定新增类别输入框的 `Enter` 事件
function setupAddCategoryEvents() {
    const categoryInput = document.getElementById("new-category-name");
    categoryInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            submitCategory();
        }
    });
}

// ✅ 提交新增类别
function submitCategory() {
    const categoryName = document.getElementById("new-category-name").value.trim();
    if (!categoryName) {
        alert("请输入类别名称！");
        return;
    }

    fetch(`/merchant/category/add/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),  // ✅ 确保 CSRF 令牌存在
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `category_name=${encodeURIComponent(categoryName)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("✅ 类别添加成功！");
            document.getElementById("add-category-form").style.display = "none";
            loadCategories();
        } else {
            alert("❌ 添加失败: " + data.error);
        }
    })
    .catch(error => console.error("❌ 添加类别失败:", error));
}
// 显示添加类别表单
function showCategoryForm() {
    document.getElementById("add-category-form").style.display = "block";
}

// 隐藏添加类别表单
function hideCategoryForm() {
    document.getElementById("add-category-form").style.display = "none";
}

function loadItems(categoryId = "") {
    console.log(`🚀 加载类别 ${categoryId} 的商品...`);
    fetch(`/merchant/manage_items/?category_id=${categoryId}`, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
    .then(response => response.json())
    .then(data => {
        const itemContainer = document.getElementById("item-list");
        itemContainer.innerHTML = "";  // 先清空商品列表

        if (data.items.length > 0) {
            data.items.forEach(item => {
                // ✅ 创建商品卡片
                let itemCard = document.createElement("div");
                itemCard.classList.add("item-card");

                // ✅ 创建商品图片
                let img = document.createElement("img");
                img.src = item.image ? item.image : "/static/img/1.jpeg";
                img.alt = item.name;
                itemCard.appendChild(img);

                // ✅ 商品信息
                let itemInfo = document.createElement("div");
                itemInfo.classList.add("item-info");
                itemInfo.innerHTML = `
                    <h3>${item.name}</h3>
                    <p>ID: ${ item.id }</p>
                    <p>价格: £${item.price}</p>
                    <p>分类: ${item.category}</p>
                `;
                itemCard.appendChild(itemInfo);

                // ✅ 创建 "上架/下架" 按钮
                let toggleBtn = document.createElement("button");
                toggleBtn.textContent = item.is_available ? "Delist" : "List";
                toggleBtn.classList.add("toggle-availability-btn");
                toggleBtn.onclick = () => toggleItemAvailability(item.id, item.is_available);
                itemCard.appendChild(toggleBtn);

                // ✅ 创建 "编辑" 按钮
                let editBtn = document.createElement("button");
                editBtn.textContent = "✏️ 编辑";
                editBtn.classList.add("edit-btn");
                editBtn.onclick = () => editItem(item.id);
                itemCard.appendChild(editBtn);

                // ✅ 创建 "删除" 按钮
                let deleteBtn = document.createElement("button");
                deleteBtn.textContent = "🗑️ 删除";
                deleteBtn.classList.add("delete-btn");
                deleteBtn.onclick = () => deleteItem(item.id);
                itemCard.appendChild(deleteBtn);

                // ✅ 添加到商品列表
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
    .catch(error => console.error("获取商品失败:", error));
}

//上架、下架商品
function toggleItemAvailability(itemId, isAvailable) {
    console.log(`🚀 切换商品 ID: ${itemId} 状态, 当前状态: ${isAvailable}`);

    fetch(`/merchant/item/toggle/${itemId}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken(), "Content-Type": "application/json" },
        body: JSON.stringify({ is_available: !isAvailable })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("✅ 商品状态更新成功！");

            // ✅ 重新加载商品，确保按钮绑定正常
            loadItems();
        } else {
            alert("❌ 更新失败: " + data.error);
        }
    })
    .catch(error => console.error("❌ 更新商品状态失败:", error));
}

// 弹出编辑商品窗口
function editItem(itemId = null, categoryId = "") {
    const itemIdField = document.getElementById("edit-item-id");
    const nameField = document.getElementById("edit-item-name");
    const priceField = document.getElementById("edit-item-price");
    const descriptionField = document.getElementById("edit-item-description");
    const categorySelect = document.getElementById("edit-item-category");
    const previewImage = document.getElementById("preview-item-image"); // ✅ 这里获取预览图片的标签

    if (itemId) {
        // ✅ 编辑模式
        fetch(`/merchant/item/details/${itemId}/`, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(response => response.json())
        .then(item => {
            console.log("📌 获取商品数据:", item);

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

            // ✅ 如果商品有图片，显示预览
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
            console.error("❌ 获取商品信息失败:", error);
            alert("❌ 发生错误，请检查 API 是否正确！");
        });
    } else {
        // ✅ 新增模式
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
        .catch(error => console.error("❌ 获取类别列表失败:", error));
    }
}

// 新增商品时，传入当前选中的类别 ID
function showAddItemForm() {
    let activeCategory = document.querySelector(".category-link.active");
    let categoryId = activeCategory ? activeCategory.getAttribute("data-category-id") : ""; // 避免 undefined
    if (categoryId === "undefined" || categoryId === null) {
        categoryId = ""; // 确保不会变成 undefined
    }

    console.log("📌 showAddItemForm 被调用，类别 ID:", categoryId);
    editItem(null, categoryId); // 进入新增商品模式，并传入类别 ID
}

// 关闭弹窗
function closeEditItemModal() {
    document.getElementById("edit-item-modal").style.display = "none";
}

// 提交商品编辑
function saveItemEdit() {
    let itemId = document.getElementById("edit-item-id").value.trim() || "new"; // ✅ 为空时传 "new"
    const url = `/merchant/item/update/${itemId}/`;  // ✅ 确保 URL 正确

    const name = document.getElementById("edit-item-name").value.trim();
    const price = parseFloat(document.getElementById("edit-item-price").value);
    const description = document.getElementById("edit-item-description").value.trim();
    const newCategory = parseInt(document.getElementById("edit-item-category").value, 10);
    const imageFile = document.getElementById("edit-item-image").files[0];

    // ✅ 表单验证：防止提交空数据
    if (!name) {
        alert("⚠️ 请输入商品名称！");
        return;
    }
    if (!price || isNaN(price) || price <= 0) {
        alert("⚠️ 请输入有效的价格！");
        return;
    }
    if (!newCategory) {
        alert("⚠️ 请选择商品类别！");
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
            alert(`❌ 更新失败: ${data.error}`);
        }
    })
    .catch(error => {
        console.error("❌ 更新商品信息失败:", error);
        alert("❌ 商品更新失败，请检查网络或后端日志。");
    });
}

// 删除商品
function deleteItem(itemId) {
    if (!confirm("确定要删除该商品吗？")) return;

    fetch(`/merchant/item/delete/${itemId}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken(), "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("✅ 商品已删除！");
            loadItems();
        } else {
            alert("❌ 删除失败: " + data.error);
        }
    })
    .catch(error => console.error("❌ 删除商品失败:", error));
}

// 获取用户评论
function loadReviews() {
    console.log("🚀 正在加载用户评论...");

    fetch("/merchant/reviews/")
        .then(response => response.json())
        .then(data => {
            console.log("✅ 获取评论数据:", data.reviews);  // **调试输出**

            const reviewContainer = document.getElementById("review-list");
            reviewContainer.innerHTML = "";

            if (data.reviews.length === 0) {
                reviewContainer.innerHTML = "<p>暂无用户评论</p>";
                return;
            }

            data.reviews.forEach(review => {
                let reviewCard = document.createElement("div");
                reviewCard.classList.add("review-card");

                reviewCard.innerHTML = `
                    <div class="review-header">
                        <strong>${review.username || "匿名用户"}</strong>
                        <span class="review-date">${review.timestamp}</span>
                    </div>
                    <div class="review-content">${review.comment || "无评论"}</div>
                    <div class="review-rating" data-rating="${review.rating}">
                        评分: ${"⭐".repeat(review.rating)}
                    </div>
                `;
                reviewContainer.appendChild(reviewCard);
            });
        })
        .catch(error => {
            console.error("❌ 获取用户评论失败:", error);
            document.getElementById("review-list").innerHTML = "<p>无法加载用户评论，请稍后重试。</p>";
        });
}


function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith("csrftoken="))
        ?.split('=')[1];
}

