document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM Loaded");

    // 顶部导航切换
    document.querySelectorAll(".nav-link").forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
            this.classList.add("active");
            document.querySelectorAll(".tab-content").forEach(section => section.classList.add("hidden"));
            document.getElementById(this.dataset.target).classList.remove("hidden");
        });
    });

    // 订单状态筛选
    document.querySelectorAll(".status-link").forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            document.querySelectorAll(".status-link").forEach(l => l.classList.remove("active"));
            this.classList.add("active");
        });
    });

    // 订单完成、取消
    document.querySelectorAll(".finish-btn, .cancel-btn").forEach(button => {
        button.addEventListener("click", function () {
            let orderId = this.dataset.orderId;
            let newStatus = this.classList.contains("finish-btn") ? "Finished" : "Canceled";
            console.log(`订单 ${orderId} 状态变更为 ${newStatus}`);
        });
    });

    // 商品上下架
    document.querySelectorAll(".delist-btn").forEach(button => {
        button.addEventListener("click", function () {
            console.log("商品下架成功！");
        });
    });

    // 回复用户评论
    document.querySelectorAll(".reply-btn").forEach(button => {
        button.addEventListener("click", function () {
            console.log("商家回复评论！");
        });
    });
});