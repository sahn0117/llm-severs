// C:\llm_service\frontend\static\js\app.js

// 建立一個全域物件來存放設定
window.LLMApp = {
    apiBaseUrl: 'http://localhost:5000/api', // 您的後端 API 位址
};

document.addEventListener('DOMContentLoaded', () => {
    const featureItems = document.querySelectorAll('.feature-item');
    const featureContainers = document.querySelectorAll('.feature-container');
    const pageTitle = document.getElementById('pageTitle');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');

    // 功能頁面切換邏輯
    featureItems.forEach(item => {
        item.addEventListener('click', () => {
            featureItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            const feature = item.getAttribute('data-feature');
            pageTitle.textContent = item.querySelector('span').textContent;

            featureContainers.forEach(container => {
                container.style.display = container.id.toLowerCase().includes(feature) ? 'flex' : 'none';
            });
            
            // 在手機上，點擊後自動關閉側邊欄
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
            }
        });
    });

    // 手機版選單按鈕
    mobileMenuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // 初始化聊天模組
    if (window.chat && typeof window.chat.init === 'function') {
        window.chat.init();
    }
    // ... 未來會在這裡初始化其他模組 (voice, ocr 等)
});