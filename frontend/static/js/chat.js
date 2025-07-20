// C:\llm_service\frontend\static\js\chat.js (最終版 - 匹配 vFinal app.py)

window.chat = {
    currentSessionId: null,
    conversationHistory: [],

    // 初始化，綁定事件並獲取或創建 session
    init: function() {
        const sendBtn = document.getElementById('sendBtn');
        const messageInput = document.getElementById('messageInput');
        
        sendBtn.addEventListener('click', () => this.sendMessage());
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 嘗試從 localStorage 獲取 session_id，如果沒有就設為 null
        this.currentSessionId = localStorage.getItem('llm_session_id');
        console.log('Chat module initialized. Session ID:', this.currentSessionId);
    },

    // 核心功能：發送訊息到後端 API
    sendMessage: async function() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message) return;

        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) welcomeMessage.remove();

        this.addMessageToUI('user', message);
        messageInput.value = '';
        messageInput.style.height = 'auto';

        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) typingIndicator.style.display = 'inline-block';

        try {
            // 準備請求的 JSON body，格式與您的 app.py 完全匹配
            const requestBody = {
                message: message, // 參數名改回 'message'
                session_id: this.currentSessionId, // 傳送當前的 session_id
                conversation_history: this.conversationHistory // 傳送對話歷史
            };

            const response = await fetch(`${window.LLMApp.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
            });

            if (typingIndicator) typingIndicator.style.display = 'none';

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`伺服器錯誤: ${response.status}. ${errorData.error || '未知錯誤'}`);
            }

            const result = await response.json();
            
            // 更新 session_id (如果是新對話，後端會回傳一個新的)
            if (result.session_id && !this.currentSessionId) {
                this.currentSessionId = result.session_id;
                localStorage.setItem('llm_session_id', this.currentSessionId);
                console.log('New session started:', this.currentSessionId);
            }
            
            // 更新對話歷史
            this.conversationHistory.push({ "role": "user", "content": message });
            this.conversationHistory.push({ "role": "assistant", "content": result.response });

            // 保持歷史紀錄不要太長 (例如只保留最近10輪對話)
            if (this.conversationHistory.length > 20) {
                this.conversationHistory = this.conversationHistory.slice(-20);
            }
            
            this.addMessageToUI('assistant', result.response);

        } catch (error) {
            console.error('Fetch error:', error);
            if (typingIndicator) typingIndicator.style.display = 'none';
            this.addMessageToUI('assistant', `抱歉，發生錯誤。請檢查後端日誌。\n錯誤: ${error.message}`);
        }
    },

    // 將訊息新增到 UI 的輔助函數
    addMessageToUI: function(sender, text) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const messageEntry = document.createElement('div');
        messageEntry.className = 'message-entry';

        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${sender}-bubble`;
        bubble.innerHTML = text.replace(/\n/g, '<br>');

        messageEntry.appendChild(bubble);

        if (sender === 'user') {
            messageEntry.style.justifyContent = 'flex-end';
        } else {
            messageEntry.style.justifyContent = 'flex-start';
        }
        
        messagesContainer.appendChild(messageEntry);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
};