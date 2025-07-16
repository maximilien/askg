// Chat application JavaScript
class AskGChatApp {
    constructor() {
        this.socket = null;
        this.messages = [];
        this.chatHistory = [];
        this.currentChatId = null;
        this.isTyping = false;
        
        this.initializeElements();
        this.initializeSocket();
        this.bindEvents();
        this.loadChatHistory();
    }

    initializeElements() {
        // UI Elements
        this.hamburgerMenu = document.getElementById('hamburgerMenu');
        this.menuDropdown = document.getElementById('menuDropdown');
        this.newChatBtn = document.getElementById('newChat');
        this.saveChatBtn = document.getElementById('saveChat');
        this.settingsBtn = document.getElementById('settings');
        this.collapseSidebarBtn = document.getElementById('collapseSidebar');
        this.chatHistorySidebar = document.getElementById('chatHistorySidebar');
        this.chatHistoryList = document.getElementById('chatHistoryList');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        this.knowledgeGraphContent = document.getElementById('knowledgeGraphContent');
        this.resizeDivider = document.getElementById('resizeDivider');
        this.knowledgeGraphSidebar = document.getElementById('knowledgeGraphSidebar');
    }

    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.addSystemMessage('Connected to askg AI agent');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.addSystemMessage('Disconnected from server');
        });

        this.socket.on('chat_response', (response) => {
            this.addMessage(response.content, 'ai', response.timestamp);
            this.isTyping = false;
            this.updateSendButton();
        });

        this.socket.on('mcp_servers_result', (result) => {
            console.log('Received MCP servers:', result);
            this.displayMCPServers(result);
        });

        this.socket.on('chat_cleared', () => {
            this.clearMessages();
            this.addSystemMessage('New chat started');
        });

        this.socket.on('chat_saved', (result) => {
            if (result.success) {
                this.showNotification('Chat saved successfully', 'success');
            } else {
                this.showNotification('Failed to save chat', 'error');
            }
        });
    }

    bindEvents() {
        // Hamburger menu
        this.hamburgerMenu.addEventListener('click', () => {
            this.toggleMenu();
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.hamburgerMenu.contains(e.target) && !this.menuDropdown.contains(e.target)) {
                this.hideMenu();
            }
        });

        // Menu items
        this.newChatBtn.addEventListener('click', () => {
            this.startNewChat();
            this.hideMenu();
        });

        this.saveChatBtn.addEventListener('click', () => {
            this.saveCurrentChat();
            this.hideMenu();
        });

        this.settingsBtn.addEventListener('click', () => {
            this.openSettings();
            this.hideMenu();
        });

        // Sidebar collapse
        this.collapseSidebarBtn.addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Chat input
        this.chatInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendButton();
        });

        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send button
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // Resize divider
        this.initializeResizeDivider();
    }

    toggleMenu() {
        this.menuDropdown.classList.toggle('show');
    }

    hideMenu() {
        this.menuDropdown.classList.remove('show');
    }

    toggleSidebar() {
        this.chatHistorySidebar.classList.toggle('collapsed');
        const icon = this.collapseSidebarBtn.querySelector('i');
        if (this.chatHistorySidebar.classList.contains('collapsed')) {
            icon.className = 'fas fa-chevron-right';
        } else {
            icon.className = 'fas fa-chevron-left';
        }
    }

    autoResizeTextarea() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
    }

    updateSendButton() {
        const hasText = this.chatInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isTyping;
    }

    sendMessage() {
        const content = this.chatInput.value.trim();
        if (!content || this.isTyping) return;

        // Add user message to UI
        this.addMessage(content, 'user');
        
        // Show loading indicator in knowledge graph pane
        this.knowledgeGraphContent.innerHTML = `
            <div class="loading-indicator">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Searching for MCP servers...</p>
            </div>
        `;
        
        // Send to server
        this.socket.emit('chat_message', {
            content: content,
            timestamp: new Date().toISOString()
        });

        // Clear input and reset
        this.chatInput.value = '';
        this.autoResizeTextarea();
        this.isTyping = true;
        this.updateSendButton();

        // Add typing indicator
        this.addTypingIndicator();
    }

    addMessage(content, type, timestamp = null) {
        const message = {
            id: Date.now().toString(),
            content: content,
            type: type,
            timestamp: timestamp || new Date().toISOString()
        };

        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    addSystemMessage(content) {
        this.addMessage(content, 'system');
    }

    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    renderMessage(message) {
        // Remove typing indicator if it exists
        this.removeTypingIndicator();

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.type}`;
        messageDiv.dataset.messageId = message.id;

        const time = new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessageContent(message.content)}
                <div class="message-time">${time}</div>
            </div>
        `;

        this.chatMessages.appendChild(messageDiv);
    }

    formatMessageContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    clearMessages() {
        this.messages = [];
        this.chatMessages.innerHTML = '';
    }

    startNewChat() {
        this.socket.emit('new_chat');
        this.currentChatId = Date.now().toString();
        this.addChatToHistory('New Chat', this.currentChatId);
    }

    saveCurrentChat() {
        if (this.messages.length === 0) {
            this.showNotification('No messages to save', 'warning');
            return;
        }

        const chatData = {
            id: this.currentChatId || Date.now().toString(),
            title: this.generateChatTitle(),
            messages: this.messages,
            timestamp: new Date().toISOString()
        };

        this.socket.emit('save_chat', chatData);
    }

    generateChatTitle() {
        const firstUserMessage = this.messages.find(m => m.type === 'user');
        if (firstUserMessage) {
            return firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '');
        }
        return 'Untitled Chat';
    }

    loadChatHistory() {
        // Load from localStorage for now
        const savedChats = JSON.parse(localStorage.getItem('askg_chat_history') || '[]');
        this.chatHistory = savedChats;
        this.renderChatHistory();
    }

    addChatToHistory(title, id) {
        const chatItem = {
            id: id,
            title: title,
            timestamp: new Date().toISOString()
        };

        this.chatHistory.unshift(chatItem);
        this.saveChatHistory();
        this.renderChatHistory();
    }

    saveChatHistory() {
        localStorage.setItem('askg_chat_history', JSON.stringify(this.chatHistory));
    }

    renderChatHistory() {
        this.chatHistoryList.innerHTML = '';
        
        this.chatHistory.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-history-item';
            chatItem.dataset.chatId = chat.id;
            
            const time = new Date(chat.timestamp).toLocaleDateString();
            chatItem.innerHTML = `
                <div class="chat-title">${chat.title}</div>
                <div class="chat-time">${time}</div>
            `;
            
            chatItem.addEventListener('click', () => {
                this.loadChat(chat.id);
            });
            
            this.chatHistoryList.appendChild(chatItem);
        });
    }

    loadChat(chatId) {
        // In a real app, this would load from the server
        console.log('Loading chat:', chatId);
        this.showNotification('Chat loading functionality would be implemented here', 'info');
    }

    openSettings() {
        this.showNotification('Settings panel would open here', 'info');
    }

    displayMCPServers(result) {
        if (!result || !result.servers || result.servers.length === 0) {
            this.knowledgeGraphContent.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No MCP servers found for your query.</p>
                </div>
            `;
            return;
        }

        const serversHtml = result.servers.map(server => `
            <div class="server-card">
                <div class="server-header">
                    <h4 class="server-name">${server.name || 'Unknown Server'}</h4>
                    <span class="server-author">by ${server.author || 'Unknown'}</span>
                </div>
                <div class="server-description">
                    ${server.description || 'No description available'}
                </div>
                <div class="server-meta">
                    ${server.repository ? `<a href="${server.repository}" target="_blank" class="server-repo">
                        <i class="fab fa-github"></i> Repository
                    </a>` : ''}
                    ${server.implementation_language ? `<span class="server-language">
                        <i class="fas fa-code"></i> ${server.implementation_language}
                    </span>` : ''}
                    ${server.popularity_score ? `<span class="server-stars">
                        <i class="fas fa-star"></i> ${server.popularity_score}
                    </span>` : ''}
                    ${server.download_count ? `<span class="server-downloads">
                        <i class="fas fa-download"></i> ${server.download_count}
                    </span>` : ''}
                </div>
                ${server.categories && server.categories.length > 0 ? `
                    <div class="server-categories">
                        ${server.categories.map(cat => `<span class="category-tag">${cat}</span>`).join('')}
                    </div>
                ` : ''}
                ${server.installation_command ? `<div class="server-install">
                    <span class="install-label">Install:</span>
                    <code class="install-command">${server.installation_command}</code>
                </div>` : ''}
            </div>
        `).join('');

        this.knowledgeGraphContent.innerHTML = `
            <div class="knowledge-graph-header">
                <h3>MCP Servers Found (${result.total_found})</h3>
                <div class="search-meta">
                    <small>Search confidence: ${result.search_metadata?.search_strategy || 'semantic'}</small>
                </div>
            </div>
            <div class="servers-list">
                ${serversHtml}
            </div>
        `;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        `;
        
        // Set background color based on type
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    initializeResizeDivider() {
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;

        const startResize = (e) => {
            isResizing = true;
            startX = e.clientX;
            startWidth = this.knowledgeGraphSidebar.offsetWidth;
            
            this.resizeDivider.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            
            e.preventDefault();
        };

        const doResize = (e) => {
            if (!isResizing) return;
            
            const deltaX = startX - e.clientX;
            const newWidth = Math.max(250, Math.min(600, startWidth + deltaX));
            
            this.knowledgeGraphSidebar.style.width = newWidth + 'px';
        };

        const stopResize = () => {
            if (!isResizing) return;
            
            isResizing = false;
            this.resizeDivider.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };

        // Mouse events
        this.resizeDivider.addEventListener('mousedown', startResize);
        document.addEventListener('mousemove', doResize);
        document.addEventListener('mouseup', stopResize);

        // Touch events for mobile
        this.resizeDivider.addEventListener('touchstart', (e) => {
            startResize(e.touches[0]);
        });
        
        document.addEventListener('touchmove', (e) => {
            doResize(e.touches[0]);
        });
        
        document.addEventListener('touchend', stopResize);

        // Prevent text selection during resize
        this.resizeDivider.addEventListener('selectstart', (e) => {
            e.preventDefault();
        });
    }
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .typing-dots {
        display: flex;
        gap: 4px;
        align-items: center;
    }
    
    .typing-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #999;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .chat-history-item .chat-title {
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    
    .chat-history-item .chat-time {
        font-size: 0.75rem;
        color: #666;
    }
`;
document.head.appendChild(style);

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AskGChatApp();
}); 