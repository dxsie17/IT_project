    document.addEventListener("DOMContentLoaded", function () {
        updateCartDisplay();  // ✅ 页面加载时刷新购物车
    });

function loadItemDetail(itemId) {
    fetch(`/item/${itemId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("detail-name").innerText = data.name;
            document.getElementById("detail-price").innerText = data.price;
            document.getElementById("detail-description").innerText = data.description;

            // **显示商品图片**
            const imageElement = document.getElementById("detail-image");
            if (data.image) {
                imageElement.src = data.image;
                imageElement.style.display = "block";  // 显示图片
            } else {
                imageElement.style.display = "none";   // 没有图片时隐藏
            }

            // **绑定加入购物车功能**
            document.getElementById("detail-add-cart").setAttribute("onclick", `addToBasket(${data.id})`);

            // **显示弹窗**
            document.getElementById("product-detail").style.display = "block";
        })
        .catch(error => {
            console.error('加载商品详情错误:', error);
            alert('无法加载商品详情，请稍后再试');
        });
}

function closeItemDetail() {
    document.getElementById("product-detail").style.display = "none";  // 关闭弹窗
}

      // 添加到购物车
function addToBasket(itemId) {
    fetch(`/add-to-basket/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),  // ✅ 传递 CSRF 令牌
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartDisplay();  // ✅ 更新购物车
        } else {
            alert('添加失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        console.error('添加购物车错误:', error);
        alert('网络错误，请稍后再试');
    });
}

      // 更新购物车显示
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
                        <button class="btn-remove" onclick="removeItem(${item.id})">移除</button>
                    </div>
                </div>
            `).join('');

            const cartElement = document.getElementById('cart-items');
            if (data.items.length) {
                cartElement.innerHTML = cartHtml;
            } else {
                cartElement.innerHTML = '<p class="empty-cart">购物车为空</p>';
            }

            // ✅ 更新总价显示
            document.getElementById("cart-total-price").innerText = `总价: £${data.total_price.toFixed(2)}`;
        })
        .catch(error => console.error("❌ 获取购物车数据失败:", error));
}

      // 减少数量
function decreaseQuantity(itemId) {
    fetch(`/decrease-from-basket/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),  // ✅ 这里替换成获取 CSRF 令牌的方法
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
            updateCartDisplay();  // ✅ 更新购物车
        } else {
            alert(`减少数量失败: ${data.error}`);
        }
    })
    .catch(error => {
        console.error("❌ 购物车减少数量失败:", error);
        alert("网络错误，请稍后重试");
    });
}

      // 完全移除
      function removeItem(itemId) {
        fetch(`/remove-from-basket/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => data.success && updateCartDisplay());
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
function checkout() {
    fetch('/checkout/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),  // 获取 CSRF 令牌
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ 结算成功！');
            updateCartDisplay(); // 结算成功后更新购物车
        } else {
            alert('❌ 结算失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        console.error('❌ 结算错误:', error);
        alert('网络错误，请稍后再试');
    });
}