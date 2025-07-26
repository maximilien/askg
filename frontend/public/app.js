// Chat application JavaScript
class AskGChatApp {
    constructor() {
        this.socket = null;
        this.messages = [];
        this.chatHistory = [];
        this.currentChatId = null;
        this.isTyping = false;
        this.nextChatId = 1;
        this.currentServers = null; // Store current servers for redrawing
        this.resizeTimeout = null; // For debouncing resize events
        
        this.initializeElements();
        this.initializeSocket();
        this.bindEvents();
        this.loadChatHistory();
        
        // Start with a new chat if no history exists
        if (this.chatHistory.length === 0) {
            this.startNewChat();
        }
    }

    initializeElements() {
        // UI Elements
        this.hamburgerMenu = document.getElementById('hamburgerMenu');
        this.menuDropdown = document.getElementById('menuDropdown');
        this.newChatBtn = document.getElementById('newChat');
        this.clearCurrentChatBtn = document.getElementById('clearCurrentChat');
        this.clearHistoryBtn = document.getElementById('clearHistory');
        this.clearEverythingBtn = document.getElementById('clearEverything');
        this.settingsBtn = document.getElementById('settings');
        this.collapseSidebarBtn = document.getElementById('collapseSidebar');
        this.chatHistorySidebar = document.getElementById('chatHistorySidebar');
        this.chatHistoryList = document.getElementById('chatHistoryList');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        this.restoreSidebarBtn = document.getElementById('restoreSidebarBtn');
        this.restoreKnowledgeGraphBtn = document.getElementById('restoreKnowledgeGraphBtn');
        this.collapseKnowledgeGraphBtn = document.getElementById('collapseKnowledgeGraph');
        this.graphToggleBtn = document.getElementById('graphToggleBtn');
        this.graphVisualization = document.getElementById('graphVisualization');
        this.knowledgeGraphContent = document.getElementById('knowledgeGraphContent');
        this.resizeDivider = document.getElementById('resizeDivider');
        this.knowledgeGraphSidebar = document.getElementById('knowledgeGraphSidebar');
        
        // Settings modal elements
        this.settingsModal = document.getElementById('settingsModal');
        this.closeSettingsBtn = document.getElementById('closeSettings');
        this.cancelSettingsBtn = document.getElementById('cancelSettings');
        this.saveSettingsBtn = document.getElementById('saveSettings');
        this.maxResultsInput = document.getElementById('maxResults');
        
        // Server details modal elements
        this.serverDetailsModal = document.getElementById('serverDetailsModal');
        this.closeServerDetailsBtn = document.getElementById('closeServerDetails');
        this.closeServerDetailsBtn2 = document.getElementById('closeServerDetailsBtn');
        this.serverDetailsTitle = document.getElementById('serverDetailsTitle');
        this.serverDetailsBody = document.getElementById('serverDetailsBody');
        

        

        
        // Debug element initialization
        console.log('Element initialization:');
        console.log('hamburgerMenu:', this.hamburgerMenu);
        console.log('menuDropdown:', this.menuDropdown);
        console.log('newChatBtn:', this.newChatBtn);
        console.log('clearHistoryBtn:', this.clearHistoryBtn);
        console.log('settingsBtn:', this.settingsBtn);
        
        // Load settings
        this.maxResults = parseInt(localStorage.getItem('askg_max_results') || '20');
        if (this.maxResultsInput) {
            this.maxResultsInput.value = this.maxResults;
        }
        // Remove debug test code for menuDropdown background color
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
            
            // Store the full result for potential expansion
            this.currentMCPResult = result;
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
        console.log('Binding hamburger menu event to:', this.hamburgerMenu);
        if (this.hamburgerMenu) {
            this.hamburgerMenu.addEventListener('click', (e) => {
                console.log('Hamburger menu clicked!', e);
                this.toggleMenu();
            });
        } else {
            console.error('Hamburger menu element not found!');
        }

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

        this.clearCurrentChatBtn.addEventListener('click', () => {
            this.clearCurrentChat();
            this.hideMenu();
        });

        this.clearHistoryBtn.addEventListener('click', () => {
            this.clearChatHistory();
            this.hideMenu();
        });

        this.clearEverythingBtn.addEventListener('click', () => {
            this.clearEverything();
            this.hideMenu();
        });

        this.settingsBtn.addEventListener('click', () => {
            console.log('Settings button clicked');
            this.openSettings();
            this.hideMenu();
        });

        // Settings modal events
        this.closeSettingsBtn.addEventListener('click', () => {
            this.closeSettings();
        });

        this.cancelSettingsBtn.addEventListener('click', () => {
            this.closeSettings();
        });

        this.saveSettingsBtn.addEventListener('click', () => {
            this.saveSettings();
        });

        // Close modal when clicking outside
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettings();
            }
        });

        // Sidebar collapse
        this.collapseSidebarBtn.addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Restore sidebar
        this.restoreSidebarBtn.addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Knowledge graph collapse/restore
        this.collapseKnowledgeGraphBtn.addEventListener('click', () => {
            this.toggleKnowledgeGraph();
        });

        this.restoreKnowledgeGraphBtn.addEventListener('click', () => {
            this.toggleKnowledgeGraph();
        });

        // Graph toggle
        this.graphToggleBtn.addEventListener('click', () => {
            this.toggleGraphVisualization();
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



        // Server details modal events
        this.closeServerDetailsBtn.addEventListener('click', () => {
            this.closeServerDetails();
        });

        this.closeServerDetailsBtn2.addEventListener('click', () => {
            this.closeServerDetails();
        });

        // Close server details modal when clicking outside
        this.serverDetailsModal.addEventListener('click', (e) => {
            if (e.target === this.serverDetailsModal) {
                this.closeServerDetails();
            }
        });

        // Resize divider
        this.initializeResizeDivider();

        // Event delegation for show-more links
        this.chatMessages.addEventListener('click', (e) => {
            console.log('Chat message clicked:', e.target);
            console.log('Target classes:', e.target.classList);
            console.log('Target dataset:', e.target.dataset);
            
            if (e.target.classList.contains('show-more-link') && e.target.dataset.action === 'expand-servers') {
                console.log('Show more link clicked!');
                e.preventDefault();
                this.expandServerList();
            }
        });
    }

    toggleMenu() {
        console.log('Toggle menu clicked');
        console.log('Menu dropdown element:', this.menuDropdown);
        console.log('Current display style:', this.menuDropdown.style.display);
        console.log('Current classes:', this.menuDropdown.className);
        
        const isVisible = this.menuDropdown.classList.contains('show');
        
        if (isVisible) {
            this.menuDropdown.classList.remove('show');
            this.menuDropdown.style.display = 'none';
        } else {
            this.menuDropdown.classList.add('show');
            this.menuDropdown.style.display = 'block';
        }
        
        console.log('After toggle - classes:', this.menuDropdown.className);
        console.log('After toggle - display style:', this.menuDropdown.style.display);
    }

    hideMenu() {
        this.menuDropdown.classList.remove('show');
    }

    toggleSidebar() {
        this.chatHistorySidebar.classList.toggle('collapsed');
        const icon = this.collapseSidebarBtn.querySelector('i');
        
        if (this.chatHistorySidebar.classList.contains('collapsed')) {
            // Sidebar is collapsed - show restore button and update collapse button
            icon.className = 'fas fa-chevron-right';
            this.restoreSidebarBtn.style.display = 'block';
        } else {
            // Sidebar is expanded - hide restore button and update collapse button
            icon.className = 'fas fa-chevron-left';
            this.restoreSidebarBtn.style.display = 'none';
        }
    }

    toggleKnowledgeGraph() {
        this.knowledgeGraphSidebar.classList.toggle('collapsed');
        const icon = this.collapseKnowledgeGraphBtn.querySelector('i');
        
        if (this.knowledgeGraphSidebar.classList.contains('collapsed')) {
            // Knowledge graph is collapsed - show restore button and update collapse button
            icon.className = 'fas fa-chevron-left';
            this.restoreKnowledgeGraphBtn.style.display = 'block';
            // Hide resize divider when collapsed
            this.resizeDivider.style.display = 'none';
        } else {
            // Knowledge graph is expanded - hide restore button and update collapse button
            icon.className = 'fas fa-chevron-right';
            this.restoreKnowledgeGraphBtn.style.display = 'none';
            // Show resize divider when expanded
            this.resizeDivider.style.display = 'flex';
        }
    }

    toggleGraphVisualization() {
        this.graphVisualization.classList.toggle('collapsed');
        const icon = this.graphToggleBtn.querySelector('i');
        
        if (this.graphVisualization.classList.contains('collapsed')) {
            // Graph is collapsed - show eye icon to indicate it can be shown
            icon.className = 'fas fa-eye';
        } else {
            // Graph is expanded - show eye-slash icon to indicate it can be hidden
            icon.className = 'fas fa-eye-slash';
        }
        
        // Redraw the graph if it's being shown and we have current servers
        if (!this.graphVisualization.classList.contains('collapsed') && this.currentServers) {
            setTimeout(() => {
                this.redrawGraphVisualization();
            }, 300); // Wait for animation to complete
        }
    }

    initializeGraphResizeHandle() {
        let isResizing = false;
        let startY = 0;
        let startHeight = 0;

        const startResize = (e) => {
            if (this.graphVisualization.classList.contains('collapsed')) {
                return;
            }
            
            isResizing = true;
            startY = e.clientY;
            startHeight = this.graphVisualization.offsetHeight;
            
            this.graphVisualization.classList.add('resizing');
            document.body.style.cursor = 'row-resize';
            document.body.style.userSelect = 'none';
            
            e.preventDefault();
        };

        const doResize = (e) => {
            if (!isResizing) return;
            
            const deltaY = e.clientY - startY;
            const containerHeight = this.graphVisualization.parentElement.offsetHeight;
            const minHeight = containerHeight * 0.2; // 20% of container height
            const maxHeight = containerHeight * 0.5; // 50% of container height
            const newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight + deltaY));
            
            this.graphVisualization.style.height = newHeight + 'px';
        };

        const stopResize = () => {
            if (!isResizing) return;
            
            isResizing = false;
            this.graphVisualization.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            // Redraw the graph visualization after resize
            this.redrawGraphVisualization();
        };

        // Mouse wheel resize for graph height
        const handleGraphWheelResize = (e) => {
            if (this.graphVisualization.classList.contains('collapsed')) {
                return;
            }
            
            e.preventDefault();
            
            const currentHeight = this.graphVisualization.offsetHeight;
            const containerHeight = this.graphVisualization.parentElement.offsetHeight;
            const minHeight = containerHeight * 0.2; // 20% of container height
            const maxHeight = containerHeight * 0.5; // 50% of container height
            const delta = e.deltaY > 0 ? -20 : 20; // Scroll down = smaller, scroll up = larger
            const newHeight = Math.max(minHeight, Math.min(maxHeight, currentHeight + delta));
            
            // Smooth resize animation
            this.graphVisualization.style.transition = 'height 0.2s ease';
            this.graphVisualization.style.height = newHeight + 'px';
            
            // Remove transition after animation
            setTimeout(() => {
                this.graphVisualization.style.transition = '';
            }, 200);
            
            // Debounced redraw
            setTimeout(() => {
                this.redrawGraphVisualization();
            }, 250);
        };

        // Add resize handle to graph visualization
        const resizeHandle = document.createElement('div');
        resizeHandle.className = 'graph-resize-handle';
        resizeHandle.innerHTML = '<i class="fas fa-grip-horizontal"></i>';
        this.graphVisualization.appendChild(resizeHandle);

        // Mouse events
        resizeHandle.addEventListener('mousedown', startResize);
        document.addEventListener('mousemove', doResize);
        document.addEventListener('mouseup', stopResize);

        // Touch events for mobile
        resizeHandle.addEventListener('touchstart', (e) => {
            e.preventDefault();
            startResize(e.touches[0]);
        });
        
        document.addEventListener('touchmove', (e) => {
            if (isResizing) {
                e.preventDefault();
                doResize(e.touches[0]);
            }
        });
        
        document.addEventListener('touchend', stopResize);

        // Wheel events for scroll-based resizing
        this.graphVisualization.addEventListener('wheel', handleGraphWheelResize, { passive: false });

        // Prevent text selection during resize
        resizeHandle.addEventListener('selectstart', (e) => {
            e.preventDefault();
        });
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

        // Create chat if this is the first message
        if (!this.currentChatId) {
            this.currentChatId = this.nextChatId.toString();
            this.nextChatId++;
            this.addChatToHistory('New Chat', this.currentChatId);
        }

        // Add user message to UI
        this.addMessage(content, 'user');
        
        // Show loading indicator in knowledge graph pane
        this.knowledgeGraphContent.innerHTML = `
            <div class="graph-visualization" id="graphVisualization">
                <div class="graph-header">
                    <h4>Graph Visualization</h4>
                    <button class="graph-toggle-btn" id="graphToggleBtn">
                        <i class="fas fa-eye-slash"></i>
                    </button>
                </div>
                <div class="graph-content" id="graphContent">
                    <div class="loading-indicator">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Searching for MCP servers...</p>
                    </div>
                </div>
            </div>
            <div class="server-list-container" id="serverListContainer">
            </div>
        `;

        // Re-bind the graph toggle button after DOM update
        this.graphToggleBtn = document.getElementById('graphToggleBtn');
        this.graphVisualization = document.getElementById('graphVisualization');
        if (this.graphToggleBtn) {
            this.graphToggleBtn.addEventListener('click', () => {
                this.toggleGraphVisualization();
            });
        }
        
        // Send to server
        this.socket.emit('chat_message', {
            content: content,
            timestamp: new Date().toISOString(),
            maxResults: this.maxResults
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
        
        // Update the current chat in history with the new message
        if (this.currentChatId) {
            const chatIndex = this.chatHistory.findIndex(c => c.id === this.currentChatId);
            if (chatIndex !== -1) {
                this.chatHistory[chatIndex].messages = [...this.messages];
                
                // Update chat title if it's still "New Chat" and this is a user message
                if (type === 'user' && this.chatHistory[chatIndex].title === 'New Chat') {
                    const newTitle = this.generateChatTitle();
                    if (newTitle !== 'Untitled Chat') {
                        this.chatHistory[chatIndex].title = newTitle;
                    }
                }
                
                this.saveChatHistory();
                this.renderChatHistory();
            }
        }
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
        // Enhanced markdown-like formatting with links
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
                // Special handling for show-more link
                if (url === '#show-more') {
                    return `<a href="#" class="show-more-link" data-action="expand-servers">${text}</a>`;
                }
                return `<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`;
            })
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
        this.currentChatId = this.nextChatId.toString();
        this.nextChatId++;
        this.addChatToHistory('New Chat', this.currentChatId, []);
        
        // Clear current messages
        this.clearMessages();
        
        // Clear knowledge graph pane
        this.knowledgeGraphContent.innerHTML = `
            <div class="graph-visualization" id="graphVisualization">
                <div class="graph-header">
                    <h4>Graph Visualization</h4>
                    <button class="graph-toggle-btn" id="graphToggleBtn">
                        <i class="fas fa-eye-slash"></i>
                    </button>
                </div>
                <div class="graph-content" id="graphContent">
                    <div class="graph-placeholder">
                        <i class="fas fa-project-diagram"></i>
                        <p>Knowledge Graph Visualization</p>
                        <p class="graph-description">
                            This area will display the askg knowledge graph representation 
                            showing MCP servers, relationships, and connections.
                        </p>
                    </div>
                </div>
            </div>
            <div class="server-list-container" id="serverListContainer">
            </div>
        `;

        // Re-bind the graph toggle button after DOM update
        this.graphToggleBtn = document.getElementById('graphToggleBtn');
        this.graphVisualization = document.getElementById('graphVisualization');
        if (this.graphToggleBtn) {
            this.graphToggleBtn.addEventListener('click', () => {
                this.toggleGraphVisualization();
            });
        }
    }

    saveCurrentChat() {
        if (this.messages.length === 0) {
            this.showNotification('No messages to save', 'warning');
            return;
        }

        // Create chat if it doesn't exist
        if (!this.currentChatId) {
            this.currentChatId = this.nextChatId.toString();
            this.nextChatId++;
            this.addChatToHistory(this.generateChatTitle(), this.currentChatId);
        }

        const chatData = {
            id: this.currentChatId,
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
        
        // Find the highest chat ID to set nextChatId
        if (this.chatHistory.length > 0) {
            this.nextChatId = Math.max(...this.chatHistory.map(chat => parseInt(chat.id))) + 1;
        }
        
        this.renderChatHistory();
    }

    addChatToHistory(title, id, messages = []) {
        const chatItem = {
            id: id,
            title: title,
            messages: messages,
            timestamp: new Date().toISOString()
        };

        // Check if chat already exists and update it
        const existingIndex = this.chatHistory.findIndex(chat => chat.id === id);
        if (existingIndex !== -1) {
            this.chatHistory[existingIndex] = chatItem;
        } else {
            this.chatHistory.unshift(chatItem);
        }
        
        this.saveChatHistory();
        this.renderChatHistory();
    }

    saveChatHistory() {
        localStorage.setItem('askg_chat_history', JSON.stringify(this.chatHistory));
    }

    renderChatHistory() {
        this.chatHistoryList.innerHTML = '';
        
        if (this.chatHistory.length === 0) {
            this.chatHistoryList.innerHTML = `
                <div class="no-chats">
                    <i class="fas fa-comments"></i>
                    <p>No chat history yet</p>
                    <small>Start a conversation to see it here</small>
                </div>
            `;
            return;
        }
        
        this.chatHistory.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-history-item';
            chatItem.dataset.chatId = chat.id;
            
            const date = new Date(chat.timestamp);
            const timeString = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            chatItem.innerHTML = `
                <div class="chat-id">#${chat.id}</div>
                <div class="chat-title" data-chat-id="${chat.id}">${chat.title}</div>
                <div class="chat-time">${timeString}</div>
                <button class="chat-delete-btn" data-chat-id="${chat.id}" title="Delete chat">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            
            // Add click handler for loading chat
            chatItem.addEventListener('click', (e) => {
                // Don't load chat if clicking on the title (for editing) or delete button
                if (!e.target.classList.contains('chat-title') && !e.target.closest('.chat-delete-btn')) {
                    this.loadChat(chat.id);
                }
            });
            
            // Add click handler for editing title
            const titleElement = chatItem.querySelector('.chat-title');
            titleElement.addEventListener('click', (e) => {
                e.stopPropagation();
                this.editChatTitle(chat.id, chat.title);
            });
            
            // Add click handler for deleting chat
            const deleteBtn = chatItem.querySelector('.chat-delete-btn');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteChat(chat.id);
            });
            
            this.chatHistoryList.appendChild(chatItem);
        });
    }

    loadChat(chatId) {
        console.log('Loading chat:', chatId);
        
        // Find the chat in history
        const chat = this.chatHistory.find(c => c.id === chatId);
        if (!chat) {
            this.showNotification('Chat not found', 'error');
            return;
        }
        
        // Set current chat ID
        this.currentChatId = chatId;
        
        // Clear current messages and load chat messages
        this.clearMessages();
        
        // Load messages from the chat
        if (chat.messages && chat.messages.length > 0) {
            this.messages = [...chat.messages];
            this.messages.forEach(message => {
                this.renderMessage(message);
            });
        }
        
        // Update chat title in history if it's still "New Chat" and we have messages
        if (chat.title === 'New Chat' && this.messages.length > 0) {
            const newTitle = this.generateChatTitle();
            if (newTitle !== 'Untitled Chat') {
                chat.title = newTitle;
                this.saveChatHistory();
                this.renderChatHistory();
            }
        }
        
        this.showNotification(`Loaded chat: ${chat.title}`, 'success');
    }

    editChatTitle(chatId, currentTitle) {
        const titleElement = document.querySelector(`[data-chat-id="${chatId}"]`);
        if (!titleElement) return;
        
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentTitle;
        input.className = 'chat-title-edit';
        input.style.cssText = `
            width: 100%;
            padding: 2px 4px;
            border: 1px solid #3b82f6;
            border-radius: 4px;
            font-size: inherit;
            font-family: inherit;
            background: white;
            color: #374151;
        `;
        
        const saveTitle = () => {
            const newTitle = input.value.trim();
            if (newTitle && newTitle !== currentTitle) {
                const chatIndex = this.chatHistory.findIndex(c => c.id === chatId);
                if (chatIndex !== -1) {
                    this.chatHistory[chatIndex].title = newTitle;
                    this.saveChatHistory();
                    this.renderChatHistory();
                    this.showNotification('Chat title updated', 'success');
                }
            }
            titleElement.textContent = newTitle || currentTitle;
        };
        
        const cancelEdit = () => {
            titleElement.textContent = currentTitle;
        };
        
        input.addEventListener('blur', saveTitle);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                saveTitle();
            } else if (e.key === 'Escape') {
                cancelEdit();
            }
        });
        
        titleElement.textContent = '';
        titleElement.appendChild(input);
        input.focus();
        input.select();
    }

    deleteChat(chatId) {
        const chat = this.chatHistory.find(c => c.id === chatId);
        if (!chat) {
            this.showNotification('Chat not found', 'error');
            return;
        }
        
        const confirmMessage = `Are you sure you want to delete "${chat.title}"? This action cannot be undone.`;
        if (!confirm(confirmMessage)) {
            return;
        }
        
        // Remove chat from history
        this.chatHistory = this.chatHistory.filter(c => c.id !== chatId);
        
        // If this was the current chat, clear it
        if (this.currentChatId === chatId) {
            this.currentChatId = null;
            this.clearMessages();
        }
        
        // Save updated history
        this.saveChatHistory();
        this.renderChatHistory();
        
        this.showNotification(`Deleted chat: ${chat.title}`, 'success');
    }

    clearChatHistory() {
        if (confirm('Are you sure you want to clear all chat history? This action cannot be undone.')) {
            this.chatHistory = [];
            this.nextChatId = 1;
            localStorage.removeItem('askg_chat_history');
            this.renderChatHistory();
            this.showNotification('Chat history cleared', 'success');
        }
    }

    clearCurrentChat() {
        if (confirm('Are you sure you want to clear the current chat? This action cannot be undone.')) {
            this.clearMessages();
            this.currentChatId = null;
            
            // Reset knowledge graph area to initial state
            this.knowledgeGraphContent.innerHTML = `
                <div class="graph-visualization" id="graphVisualization">
                    <div class="graph-placeholder">
                        <i class="fas fa-project-diagram"></i>
                        <p>Knowledge Graph Visualization</p>
                        <p class="graph-description">
                            This area will display the askg knowledge graph representation 
                            showing MCP servers, relationships, and connections.
                        </p>
                    </div>
                </div>
                <div class="server-list-container" id="serverListContainer">
                </div>
            `;
            
            this.showNotification('Current chat cleared', 'success');
        }
    }

    clearEverything() {
        if (confirm('Are you sure you want to clear everything? This will clear all chat history and the current chat. This action cannot be undone.')) {
            // Clear chat history
            this.chatHistory = [];
            this.nextChatId = 1;
            localStorage.removeItem('askg_chat_history');
            this.renderChatHistory();
            
            // Clear current chat
            this.clearMessages();
            this.currentChatId = null;
            
            // Reset knowledge graph area
            this.knowledgeGraphContent.innerHTML = `
                <div class="graph-visualization" id="graphVisualization">
                    <div class="graph-placeholder">
                        <i class="fas fa-project-diagram"></i>
                        <p>Knowledge Graph Visualization</p>
                        <p class="graph-description">
                            This area will display the askg knowledge graph representation 
                            showing MCP servers, relationships, and connections.
                        </p>
                    </div>
                </div>
                <div class="server-list-container" id="serverListContainer">
                </div>
            `;
            
            this.showNotification('Everything cleared successfully', 'success');
        }
    }

    openSettings() {
        console.log('openSettings called');
        console.log('settingsModal element:', this.settingsModal);
        console.log('settingsModal classes before:', this.settingsModal.className);
        
        this.settingsModal.classList.add('show');
        console.log('settingsModal classes after:', this.settingsModal.className);
        
        // Force visibility with inline styles as backup
        this.settingsModal.style.display = 'flex';
        this.settingsModal.style.opacity = '1';
        this.settingsModal.style.visibility = 'visible';
        this.settingsModal.style.zIndex = '99999';
        
        this.maxResultsInput.value = this.maxResults;
        console.log('Settings modal should now be visible');
    }

    closeSettings() {
        this.settingsModal.classList.remove('show');
        // Reset inline styles
        this.settingsModal.style.display = '';
        this.settingsModal.style.opacity = '';
        this.settingsModal.style.visibility = '';
        this.settingsModal.style.zIndex = '';
    }

    saveSettings() {
        const newMaxResults = parseInt(this.maxResultsInput.value);
        if (newMaxResults >= 1 && newMaxResults <= 100) {
            this.maxResults = newMaxResults;
            localStorage.setItem('askg_max_results', this.maxResults.toString());
            this.closeSettings();
            this.showNotification('Settings saved successfully', 'success');
        } else {
            this.showNotification('Max results must be between 1 and 100', 'error');
        }
    }

    displayMCPServers(result) {
        console.log('displayMCPServers called with:', result);
        
        // Store the servers data for potential redrawing and node clicking
        this.currentServers = result.servers || [];
        this.currentSearchResults = result;
        
        if (!result || !result.servers || result.servers.length === 0) {
            console.log('No servers found, showing empty state');
            this.currentServers = [];
            this.knowledgeGraphContent.innerHTML = `
                <div class="graph-visualization" id="graphVisualization">
                    <div class="graph-header">
                        <h4>Graph Visualization</h4>
                        <button class="graph-toggle-btn" id="graphToggleBtn">
                            <i class="fas fa-eye-slash"></i>
                        </button>
                    </div>
                    <div class="graph-content" id="graphContent">
                        <div class="no-results">
                            <i class="fas fa-search"></i>
                            <p>No MCP servers found for your query.</p>
                        </div>
                    </div>
                </div>
                <div class="server-list-container" id="serverListContainer">
                </div>
            `;

                    // Re-bind the graph toggle button after DOM update
        this.graphToggleBtn = document.getElementById('graphToggleBtn');
        this.graphVisualization = document.getElementById('graphVisualization');
        if (this.graphToggleBtn) {
            this.graphToggleBtn.addEventListener('click', () => {
                this.toggleGraphVisualization();
            });
        }
        return;
        }

        console.log('Creating visualization for', result.servers.length, 'servers');

        // Create server list HTML first
        console.log('Creating server cards for', result.servers.length, 'servers');
        const serversHtml = result.servers.map((server, index) => `
            <div class="server-card" data-server-index="${index}" style="cursor: pointer;">
                <div class="server-header">
                    <h4 class="server-name">${server.name || 'Unknown Server'}</h4>
                    <span class="server-author">by ${server.author || 'Unknown'}</span>
                </div>
                <div class="server-description">
                    ${server.description || 'No description available'}
                </div>
                <div class="server-meta">
                    ${server.repository ? `<a href="${server.repository}" target="_blank" class="server-repo" onclick="event.stopPropagation();">
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

        // Update the content structure
        this.knowledgeGraphContent.innerHTML = `
            <div class="graph-visualization" id="graphVisualization">
                <div class="graph-header">
                    <h4>Graph Visualization</h4>
                    <button class="graph-toggle-btn" id="graphToggleBtn">
                        <i class="fas fa-eye-slash"></i>
                    </button>
                </div>
                <div class="graph-content" id="graphContent">
                    <!-- Graph will be rendered here -->
                </div>
            </div>
            <div class="server-list-container" id="serverListContainer">
                <div class="knowledge-graph-header">
                    <h3>MCP Servers Found (${result.total_found})</h3>
                    <div class="search-meta">
                        <small>Search confidence: ${result.search_metadata?.search_strategy || 'semantic'}</small>
                    </div>
                </div>
                <div class="servers-list">
                    ${serversHtml}
                </div>
            </div>
        `;

        // Re-bind the graph toggle button after DOM update
        this.graphToggleBtn = document.getElementById('graphToggleBtn');
        this.graphVisualization = document.getElementById('graphVisualization');
        if (this.graphToggleBtn) {
            this.graphToggleBtn.addEventListener('click', () => {
                this.toggleGraphVisualization();
            });
        }
        
        // Initialize graph resize handle
        if (this.graphVisualization) {
            this.initializeGraphResizeHandle();
        }

        // Add click handlers to server cards
        const serverCards = document.querySelectorAll('.server-card');
        console.log('Found server cards:', serverCards.length);
        serverCards.forEach((card, index) => {

            card.addEventListener('click', (e) => {
                const serverIndex = parseInt(card.getAttribute('data-server-index'));
                const server = result.servers[serverIndex];
                this.showServerDetails(server);
            });
        });

        console.log('DOM updated, creating graph visualization');
        console.log('Graph container after DOM update:', document.getElementById('graphVisualization'));
        
        // Create graph visualization after DOM is updated
        setTimeout(() => {
            console.log('Timeout fired, calling createGraphVisualization...');
            this.createGraphVisualization(result.servers);
        }, 100);
    }

    showServerDetails(server) {
        try {
            // Check if modal elements exist
            if (!this.serverDetailsModal || !this.serverDetailsTitle || !this.serverDetailsBody) {
                console.error('Modal elements not found!');
                return;
            }
            
            // Update modal title
            this.serverDetailsTitle.textContent = server.name || 'Unknown Server';

            // Generate tools HTML
            const toolsHtml = this.generateToolsHtml(server);

            // Generate modal content
            const modalContent = `
                <div class="server-details-header">
                    <div>
                        <h2 class="server-details-name">${server.name || 'Unknown Server'}</h2>
                        <div class="server-details-author">by ${server.author || 'Unknown'}</div>
                    </div>
                </div>
                
                <div class="server-details-description">
                    ${server.description || 'No description available'}
                </div>
                
                <div class="server-details-meta">
                    ${server.repository ? `
                        <div class="server-details-meta-item">
                            <i class="fab fa-github"></i>
                            <div>
                                <div class="server-details-meta-label">Repository</div>
                                <div class="server-details-meta-value">
                                    <a href="${server.repository}" target="_blank">${server.repository}</a>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                    ${server.implementation_language ? `
                        <div class="server-details-meta-item">
                            <i class="fas fa-code"></i>
                            <div>
                                <div class="server-details-meta-label">Language</div>
                                <div class="server-details-meta-value">${server.implementation_language}</div>
                            </div>
                        </div>
                    ` : ''}
                    ${server.popularity_score ? `
                        <div class="server-details-meta-item">
                            <i class="fas fa-star"></i>
                            <div>
                                <div class="server-details-meta-label">Popularity</div>
                                <div class="server-details-meta-value">${server.popularity_score}</div>
                            </div>
                        </div>
                    ` : ''}
                    ${server.download_count ? `
                        <div class="server-details-meta-item">
                            <i class="fas fa-download"></i>
                            <div>
                                <div class="server-details-meta-label">Downloads</div>
                                <div class="server-details-meta-value">${server.download_count}</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
                
                ${server.categories && server.categories.length > 0 ? `
                    <div class="server-details-categories">
                        <h4>Categories</h4>
                        <div class="server-details-categories-list">
                            ${server.categories.map(cat => `<span class="server-details-category">${cat}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${toolsHtml}
                
                ${server.installation_command ? `
                    <div class="server-details-install">
                        <h4>Installation</h4>
                        <div class="server-details-install-command">${server.installation_command}</div>
                    </div>
                ` : ''}
            `;

            // Update modal body
            this.serverDetailsBody.innerHTML = modalContent;

            // Show modal with proper centering
            this.serverDetailsModal.classList.add('show');
            
            // Ensure modal is visible and centered
            this.serverDetailsModal.style.display = 'flex';
            this.serverDetailsModal.style.opacity = '1';
            this.serverDetailsModal.style.visibility = 'visible';
            this.serverDetailsModal.style.zIndex = '99999';
            
        } catch (error) {
            console.error('Error showing server details:', error);
            
            // Show error message in modal
            this.serverDetailsTitle.textContent = 'Error Loading Server Details';
            this.serverDetailsBody.innerHTML = `
                <div class="server-details-error">
                    <p>Sorry, there was an error loading the server details.</p>
                    <p>Error: ${error.message}</p>
                </div>
            `;
            this.serverDetailsModal.classList.add('show');
        }
    }

    generateToolsHtml(server) {
        // Defensive check for server object
        if (!server) {
            return `
                <div class="server-details-tools">
                    <h4>Tools <span class="server-details-tools-count">0</span></h4>
                    <div class="server-details-tools-list">
                        <div class="server-details-tool">
                            <div class="server-details-tool-description">Server data not available.</div>
                        </div>
                    </div>
                </div>
            `;
        }

        if (!server.tools || server.tools.length === 0) {
            return `
                <div class="server-details-tools">
                    <h4>Tools <span class="server-details-tools-count">0</span></h4>
                    <div class="server-details-tools-list">
                        <div class="server-details-tool">
                            <div class="server-details-tool-description">No tools available for this server.</div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Sort tools by name, with defensive programming
        const sortedTools = [...server.tools]
            .filter(tool => tool && typeof tool === 'object') // Filter out null/undefined tools
            .sort((a, b) => {
                const nameA = (a.name || '').toString();
                const nameB = (b.name || '').toString();
                return nameA.localeCompare(nameB);
            });

        const toolsHtml = sortedTools.map(tool => {
            const toolName = tool.name || 'Unnamed Tool';
            const toolDescription = tool.description || 'No description available';
            const inputsHtml = tool.input_schema ? this.formatToolInputs(tool.input_schema) : '';
            
            return `
                <div class="server-details-tool">
                    <div class="server-details-tool-header">
                        <div class="server-details-tool-name">${toolName}</div>
                    </div>
                    <div class="server-details-tool-description">
                        ${toolDescription}
                    </div>
                    ${inputsHtml ? `
                        <div class="server-details-tool-inputs">
                            ${inputsHtml}
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');

        return `
            <div class="server-details-tools">
                <h4>Tools <span class="server-details-tools-count">${sortedTools.length}</span></h4>
                <div class="server-details-tools-list">
                    ${toolsHtml}
                </div>
            </div>
        `;
    }

    formatToolInputs(inputSchema) {
        if (!inputSchema || !inputSchema.properties) {
            return '';
        }

        const inputs = Object.entries(inputSchema.properties).map(([name, prop]) => {
            const type = prop.type || 'unknown';
            const description = prop.description || '';
            const required = inputSchema.required && inputSchema.required.includes(name);
            
            return `
                <div><strong>${name}</strong> (${type})${required ? ' <span style="color: #dc3545;">*required</span>' : ''}${description ? `: ${description}` : ''}</div>
            `;
        }).join('');

        return inputs ? `<div><strong>Inputs:</strong></div>${inputs}` : '';
    }

    closeServerDetails() {
        this.serverDetailsModal.classList.remove('show');
        // Reset inline styles
        this.serverDetailsModal.style.display = '';
        this.serverDetailsModal.style.opacity = '';
        this.serverDetailsModal.style.visibility = '';
        this.serverDetailsModal.style.zIndex = '';
    }

    scrollToServerAndShowDetails(serverId) {
        // Find the server card with the matching ID
        const serverCards = document.querySelectorAll('.server-card');
        let targetCard = null;
        let serverData = null;

        // Find the card and get the server data
        serverCards.forEach((card, index) => {
            const cardServerIndex = parseInt(card.getAttribute('data-server-index'));
            if (cardServerIndex !== null && this.currentSearchResults && this.currentSearchResults.servers[cardServerIndex]) {
                const server = this.currentSearchResults.servers[cardServerIndex];
                if (server.id === serverId) {
                    targetCard = card;
                    serverData = server;
                }
            }
        });

        if (targetCard && serverData) {
            // Scroll to the server card
            targetCard.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });

            // Add a brief highlight effect
            targetCard.style.transition = 'all 0.3s ease';
            targetCard.style.transform = 'scale(1.05)';
            targetCard.style.boxShadow = '0 8px 25px rgba(102, 126, 234, 0.3)';
            targetCard.style.borderColor = 'rgba(102, 126, 234, 0.6)';

            // Remove highlight after animation
            setTimeout(() => {
                targetCard.style.transform = 'scale(1)';
                targetCard.style.boxShadow = '';
                targetCard.style.borderColor = '';
            }, 1500);

            // Show server details modal
            setTimeout(() => {
                this.showServerDetails(serverData);
            }, 300); // Small delay to let scroll animation complete
        } else {
            console.warn('Server not found in current results:', serverId);
        }
    }

    scrollToServer(serverId) {
        // Find the server card with the matching ID
        const serverCards = document.querySelectorAll('.server-card');
        let targetCard = null;

        // Find the card
        serverCards.forEach((card, index) => {
            const cardServerIndex = parseInt(card.getAttribute('data-server-index'));
            if (cardServerIndex !== null && this.currentSearchResults && this.currentSearchResults.servers[cardServerIndex]) {
                const server = this.currentSearchResults.servers[cardServerIndex];
                if (server.id === serverId) {
                    targetCard = card;
                }
            }
        });

        if (targetCard) {
            // Scroll to the server card
            targetCard.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });

            // Add a brief highlight effect
            targetCard.style.transition = 'all 0.3s ease';
            targetCard.style.transform = 'scale(1.05)';
            targetCard.style.boxShadow = '0 8px 25px rgba(102, 126, 234, 0.3)';
            targetCard.style.borderColor = 'rgba(102, 126, 234, 0.6)';

            // Remove highlight after animation
            setTimeout(() => {
                targetCard.style.transform = 'scale(1)';
                targetCard.style.boxShadow = '';
                targetCard.style.borderColor = '';
            }, 1500);
        } else {
            console.warn('Server not found in current results:', serverId);
        }
    }

    createGraphVisualization(servers) {
        console.log('=== D3.js GRAPH VISUALIZATION DEBUG START ===');
        console.log('createGraphVisualization called with:', servers);
        console.log('Servers data:', servers);
        
        // Check D3.js availability first
        console.log('D3.js availability check:');
        console.log('- typeof d3:', typeof d3);
        console.log('- window.d3:', window.d3);
        console.log('- global d3:', typeof global !== 'undefined' ? global.d3 : 'global not available');
        
        // Check for D3.js script in DOM
        const d3Scripts = document.querySelectorAll('script[src*="d3"]');
        console.log('- D3.js scripts in DOM:', d3Scripts.length);
        d3Scripts.forEach((script, index) => {
            console.log(`  Script ${index + 1}:`, script.src, 'loaded:', script.loaded);
        });
        
        if (typeof d3 === 'undefined') {
            console.error('❌ D3.js is NOT available!');
            console.log('Available global objects:', Object.keys(window).filter(key => key.includes('d3') || key.includes('D3')));
            console.log('Scripts loaded:', Array.from(document.scripts).map(s => s.src));
        } else {
            console.log('✅ D3.js is available!');
            console.log('- d3.version:', d3.version);
            console.log('- d3.select:', typeof d3.select);
            console.log('- d3.forceSimulation:', typeof d3.forceSimulation);
        }
        
        const graphContainer = document.getElementById('graphContent');
        console.log('Looking for graphContent element:', graphContainer);
        
        if (!graphContainer) {
            console.error('❌ Graph container not found!');
            console.log('Available elements with graph in name:');
            document.querySelectorAll('[id*="graph"]').forEach(el => {
                console.log('Found element:', el.id, el);
            });
            return;
        }

        console.log('✅ Graph container found:', graphContainer);
        console.log('Container dimensions:', graphContainer.clientWidth, 'x', graphContainer.clientHeight);
        console.log('Container computed styles:', window.getComputedStyle(graphContainer));

        // Clear existing content
        graphContainer.innerHTML = '';

        // Check if D3.js is available
        if (typeof d3 === 'undefined') {
            console.warn('❌ D3.js not available, attempting to load dynamically...');
            
                    // Check if we can access the local D3.js file
        fetch('d3.v7.min.js', { method: 'HEAD' })
            .then(response => {
                console.log('✅ Local D3.js file is accessible:', response.status);
                this.loadD3AndRetry(servers, graphContainer);
            })
            .catch(error => {
                console.error('❌ Local D3.js file is not accessible:', error);
                console.log('Using fallback visualization due to file access issues');
                this.createFallbackVisualization(servers, graphContainer);
            });
            return;
        }

        // Create SVG
        const width = graphContainer.clientWidth || 400;
        const height = graphContainer.clientHeight || 200;

        console.log('Creating SVG with dimensions:', width, 'x', height);
        console.log('Container rect:', graphContainer.getBoundingClientRect());
        
        // If dimensions are too small, use fallback
        if (width < 100 || height < 100) {
            console.warn('Container too small, using fallback visualization');
            this.createFallbackVisualization(servers, graphContainer);
            return;
        }

        // Create SVG
        let svg;
        try {
            svg = d3.select(graphContainer)
                .append('svg')
                .attr('width', width)
                .attr('height', height);
            
            console.log('SVG created successfully:', svg);
        } catch (error) {
            console.error('Error creating SVG:', error);
            this.createFallbackVisualization(servers, graphContainer);
            return;
        }

        // Create force simulation with better parameters
        const simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(120))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(35));

        // Create nodes from servers
        const nodes = servers.map((server, index) => ({
            id: server.id || `server-${index}`,
            name: server.name || 'Unknown',
            category: server.categories && server.categories.length > 0 ? server.categories[0] : 'other',
            popularity: server.popularity_score || 0,
            author: server.author || 'Unknown',
            description: server.description || '',
            repository: server.repository || ''
        }));

        console.log('Created nodes:', nodes);

        // Create meaningful links between nodes based on relationships
        const links = [];
        const linkMap = new Map(); // Track existing links to prevent duplicates
        
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const node1 = nodes[i];
                const node2 = nodes[j];
                
                // Create a unique key for this node pair (sorted to ensure consistency)
                const linkKey = [node1.id, node2.id].sort().join('--');
                
                // Skip if we already have a link between these nodes
                if (linkMap.has(linkKey)) {
                    continue;
                }
                
                // Find the strongest relationship type between these nodes
                let relationshipType = 'related';
                let relationshipDescription = 'Related servers';
                let relationshipStrength = 1;
                
                // Check for author similarity (highest priority)
                if (node1.author === node2.author && node1.author !== 'Unknown') {
                    relationshipType = 'same_author';
                    relationshipDescription = `Both by ${node1.author}`;
                    relationshipStrength = 3;
                }
                // Check for category similarity (medium priority)
                else if (node1.category === node2.category && node1.category !== 'other') {
                    relationshipType = 'same_category';
                    relationshipDescription = `Both are ${node1.category} servers`;
                    relationshipStrength = 2;
                }
                // Check for popularity similarity (lowest priority)
                else {
                    const pop1 = node1.popularity > 1000;
                    const pop2 = node2.popularity > 1000;
                    if (pop1 === pop2 && (pop1 || (node1.popularity < 100 && node2.popularity < 100))) {
                        relationshipType = 'similar_popularity';
                        relationshipDescription = pop1 ? 'Both popular servers' : 'Both niche servers';
                        relationshipStrength = 1.5;
                    }
                }
                
                // Only create links for meaningful relationships
                if (relationshipStrength > 1) {
                    const link = {
                        source: node1.id,
                        target: node2.id,
                        type: relationshipType,
                        description: relationshipDescription,
                        strength: relationshipStrength,
                        value: relationshipStrength
                    };
                    
                    links.push(link);
                    linkMap.set(linkKey, link); // Track this link
                }
            }
        }

        console.log('Created links:', links);
        
        // Determine if legend should be shown based on graph complexity
        const shouldShowLegend = nodes.length <= 10 && links.length <= 5 * nodes.length;
        console.log('Graph complexity - Nodes:', nodes.length, 'Links:', links.length);
        console.log('Legend will be shown:', shouldShowLegend);

        // Color scale for categories
        const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

        // Create tooltip for links
        const linkTooltip = d3.select('body')
            .append('div')
            .attr('class', 'link-tooltip')
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.9)')
            .style('color', 'white')
            .style('padding', '10px 14px')
            .style('border-radius', '8px')
            .style('font-size', '12px')
            .style('font-weight', '500')
            .style('pointer-events', 'none')
            .style('z-index', '1000')
            .style('opacity', '0')
            .style('transition', 'opacity 0.1s ease')
            .style('box-shadow', '0 4px 12px rgba(0,0,0,0.3)')
            .style('border', '1px solid rgba(255,255,255,0.1)')
            .style('max-width', '200px')
            .style('white-space', 'nowrap');

        // Create tooltip for nodes
        const nodeTooltip = d3.select('body')
            .append('div')
            .attr('class', 'node-tooltip')
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.95)')
            .style('color', 'white')
            .style('padding', '12px 16px')
            .style('border-radius', '8px')
            .style('font-size', '12px')
            .style('font-weight', '400')
            .style('pointer-events', 'none')
            .style('z-index', '1001')
            .style('opacity', '0')
            .style('transition', 'opacity 0.15s ease')
            .style('box-shadow', '0 6px 16px rgba(0,0,0,0.4)')
            .style('border', '1px solid rgba(255,255,255,0.15)')
            .style('max-width', '280px')
            .style('line-height', '1.4');

        // Create links with relationship-based styling
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'graph-link')
            .attr('stroke', d => {
                switch(d.type) {
                    case 'same_author': return 'rgba(255, 99, 132, 0.8)'; // Red for same author
                    case 'same_category': return 'rgba(54, 162, 235, 0.8)'; // Blue for same category
                    case 'similar_popularity': return 'rgba(255, 205, 86, 0.8)'; // Yellow for popularity
                    default: return 'rgba(102, 126, 234, 0.6)'; // Default blue
                }
            })
            .attr('stroke-width', d => Math.max(1, Math.min(4, d.strength)))
            .attr('stroke-dasharray', d => d.type === 'same_author' ? 'none' : '5,5')
            .style('cursor', 'pointer')
            .style('transition', 'all 0.15s ease')
            .style('pointer-events', 'all')
            .on('mouseover', function(event, d) {
                d3.select(this)
                    .attr('stroke-width', Math.max(3, Math.min(8, d.strength + 2)))
                    .style('filter', 'drop-shadow(0 3px 6px rgba(0,0,0,0.4))');
                
                // Show tooltip immediately with smart positioning
                const tooltip = linkTooltip
                    .style('opacity', '1')
                    .style('transition', 'opacity 0.1s ease')
                    .html(`
                        <strong>${d.description}</strong><br>
                        <small>Relationship strength: ${d.strength}</small>
                    `);
                
                // Smart positioning to avoid screen edges
                const tooltipNode = tooltip.node();
                const tooltipRect = tooltipNode.getBoundingClientRect();
                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight;
                
                let left = event.pageX + 10;
                let top = event.pageY - 10;
                
                // Adjust if tooltip would go off right edge
                if (left + tooltipRect.width > viewportWidth - 20) {
                    left = event.pageX - tooltipRect.width - 10;
                }
                
                // Adjust if tooltip would go off bottom edge
                if (top + tooltipRect.height > viewportHeight - 20) {
                    top = event.pageY - tooltipRect.height - 10;
                }
                
                // Ensure tooltip doesn't go off left or top edges
                left = Math.max(10, left);
                top = Math.max(10, top);
                
                tooltip
                    .style('left', left + 'px')
                    .style('top', top + 'px');
            })
            .on('mouseout', function(event, d) {
                d3.select(this)
                    .attr('stroke-width', Math.max(1, Math.min(4, d.strength)))
                    .style('filter', 'none');
                
                // Hide tooltip with slight delay to prevent flickering
                setTimeout(() => {
                    linkTooltip.style('opacity', '0');
                }, 100);
            });

        // Create invisible wider hover areas for better sensitivity
        const hoverArea = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'graph-link-hover')
            .attr('stroke', 'transparent')
            .attr('stroke-width', 12) // Much wider invisible area
            .style('cursor', 'pointer')
            .style('pointer-events', 'all')
            .on('mouseover', function(event, d) {
                // Directly show tooltip for better reliability
                const tooltip = linkTooltip
                    .style('opacity', '1')
                    .style('transition', 'opacity 0.1s ease')
                    .html(`
                        <strong>${d.description}</strong><br>
                        <small>Relationship strength: ${d.strength}</small>
                    `);
                
                // Smart positioning to avoid screen edges
                const tooltipNode = tooltip.node();
                const tooltipRect = tooltipNode.getBoundingClientRect();
                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight;
                
                let left = event.pageX + 10;
                let top = event.pageY - 10;
                
                // Adjust if tooltip would go off right edge
                if (left + tooltipRect.width > viewportWidth - 20) {
                    left = event.pageX - tooltipRect.width - 10;
                }
                
                // Adjust if tooltip would go off bottom edge
                if (top + tooltipRect.height > viewportHeight - 20) {
                    top = event.pageY - tooltipRect.height - 10;
                }
                
                // Ensure tooltip doesn't go off left or top edges
                left = Math.max(10, left);
                top = Math.max(10, top);
                
                tooltip
                    .style('left', left + 'px')
                    .style('top', top + 'px');
                
                // Also highlight the visible link
                const visibleLink = d3.select(`.graph-link[data-index="${d3.select(this).attr('data-index')}"]`);
                if (!visibleLink.empty()) {
                    visibleLink
                        .attr('stroke-width', Math.max(3, Math.min(8, d.strength + 2)))
                        .style('filter', 'drop-shadow(0 3px 6px rgba(0,0,0,0.4))');
                }
            })
            .on('mouseout', function(event, d) {
                // Hide tooltip with slight delay to prevent flickering
                setTimeout(() => {
                    linkTooltip.style('opacity', '0');
                }, 100);
                
                // Reset the visible link
                const visibleLink = d3.select(`.graph-link[data-index="${d3.select(this).attr('data-index')}"]`);
                if (!visibleLink.empty()) {
                    visibleLink
                        .attr('stroke-width', Math.max(1, Math.min(4, d.strength)))
                        .style('filter', 'none');
                }
            });

        // Add data-index attributes to both visible and hover areas for linking
        link.each(function(d, i) {
            d3.select(this).attr('data-index', i);
        });
        hoverArea.each(function(d, i) {
            d3.select(this).attr('data-index', i);
        });

        // Create nodes
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('class', 'graph-node')
            .attr('r', d => Math.max(12, Math.min(25, Math.sqrt(d.popularity + 1) * 2)))
            .attr('fill', d => colorScale(d.category))
            .attr('stroke', '#fff')
            .attr('stroke-width', 3)
            .style('cursor', 'pointer')
            .style('transition', 'all 0.2s ease')
            .on('mouseover', function(event, d) {
                d3.select(this)
                    .attr('r', d => Math.max(15, Math.min(30, Math.sqrt(d.popularity + 1) * 2.5)))
                    .attr('stroke-width', 4)
                    .style('filter', 'drop-shadow(0 4px 8px rgba(0,0,0,0.3))');
                
                // Show node tooltip with server details
                const tooltip = nodeTooltip
                    .style('opacity', '1')
                    .style('transition', 'opacity 0.15s ease');
                
                // Create tooltip content
                const description = d.description && d.description !== '-' ? 
                    (d.description.length > 80 ? d.description.substring(0, 80) + '...' : d.description) : 
                    'No description available';
                
                const tooltipContent = `
                    <div style="margin-bottom: 8px;">
                        <strong style="color: #667eea; font-size: 14px;">${d.name}</strong>
                    </div>
                    <div style="margin-bottom: 6px; font-size: 11px; color: #ccc;">
                        <span style="color: #ff6b6b;">👤</span> ${d.author}
                        ${d.popularity > 0 ? `<span style="margin-left: 8px; color: #ffd93d;">⭐</span> ${d.popularity.toLocaleString()}` : ''}
                    </div>
                    <div style="margin-bottom: 6px; font-size: 11px; color: #ccc;">
                        <span style="color: #4ecdc4;">📂</span> ${d.category}
                    </div>
                    <div style="font-size: 11px; color: #ddd; line-height: 1.3;">
                        ${description}
                    </div>
                `;
                
                tooltip.html(tooltipContent);
                
                // Smart positioning to avoid screen edges
                const tooltipNode = tooltip.node();
                const tooltipRect = tooltipNode.getBoundingClientRect();
                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight;
                
                let left = event.pageX + 15;
                let top = event.pageY - 15;
                
                // Adjust if tooltip would go off right edge
                if (left + tooltipRect.width > viewportWidth - 20) {
                    left = event.pageX - tooltipRect.width - 15;
                }
                
                // Adjust if tooltip would go off bottom edge
                if (top + tooltipRect.height > viewportHeight - 20) {
                    top = event.pageY - tooltipRect.height - 15;
                }
                
                // Ensure tooltip doesn't go off left or top edges
                left = Math.max(10, left);
                top = Math.max(10, top);
                
                tooltip
                    .style('left', left + 'px')
                    .style('top', top + 'px');
            })
            .on('mouseout', function(event, d) {
                d3.select(this)
                    .attr('r', d => Math.max(12, Math.min(25, Math.sqrt(d.popularity + 1) * 2)))
                    .attr('stroke-width', 3)
                    .style('filter', 'none');
                
                // Hide node tooltip with slight delay to prevent flickering
                setTimeout(() => {
                    nodeTooltip.style('opacity', '0');
                }, 150);
            })
            .on('click', (event, d) => {
                // Find the corresponding server and scroll to it
                const server = servers.find(s => s.id === d.id);
                if (server) {
                    this.scrollToServer(d.id);
                }
            })
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));

        // Add node labels
        const label = svg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('class', 'graph-node-label')
            .text(d => d.name.length > 15 ? d.name.substring(0, 15) + '...' : d.name)
            .attr('dy', '.35em')
            .style('font-size', '10px')
            .style('font-weight', '500')
            .style('fill', '#333')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'none');

        // Add edge labels for relationships only for simple graphs
        let edgeLabel;
        if (shouldShowLegend) {
            edgeLabel = svg.append('g')
                .selectAll('text')
                .data(links)
                .enter().append('text')
                .attr('class', 'graph-edge-label')
                .text(d => {
                    switch(d.type) {
                        case 'same_author': return '👤';
                        case 'same_category': return '📂';
                        case 'similar_popularity': return '⭐';
                        default: return '🔗';
                    }
                })
                .attr('dy', '.35em')
                .style('font-size', '12px')
                .style('font-weight', 'bold')
                .style('fill', d => {
                    switch(d.type) {
                        case 'same_author': return 'rgba(255, 99, 132, 0.9)';
                        case 'same_category': return 'rgba(54, 162, 235, 0.9)';
                        case 'similar_popularity': return 'rgba(255, 205, 86, 0.9)';
                        default: return 'rgba(102, 126, 234, 0.9)';
                    }
                })
                .style('text-anchor', 'middle')
                .style('pointer-events', 'none')
                .style('text-shadow', '1px 1px 2px rgba(255,255,255,0.8)');
        }

        // Add relationship legend only for simple graphs
        if (shouldShowLegend) {
            const legend = svg.append('g')
                .attr('class', 'graph-legend')
                .attr('transform', `translate(10, 10)`);

            const legendData = [
                { type: 'same_author', label: 'Same Author', icon: '👤', color: 'rgba(255, 99, 132, 0.8)' },
                { type: 'same_category', label: 'Same Category', icon: '📂', color: 'rgba(54, 162, 235, 0.8)' },
                { type: 'similar_popularity', label: 'Similar Popularity', icon: '⭐', color: 'rgba(255, 205, 86, 0.8)' }
            ];

            const legendItems = legend.selectAll('.legend-item')
                .data(legendData)
                .enter().append('g')
                .attr('class', 'legend-item')
                .attr('transform', (d, i) => `translate(0, ${i * 20})`);

            legendItems.append('line')
                .attr('x1', 0)
                .attr('y1', 0)
                .attr('x2', 20)
                .attr('y2', 0)
                .attr('stroke', d => d.color)
                .attr('stroke-width', 2);

            legendItems.append('text')
                .attr('x', 25)
                .attr('y', 0)
                .attr('dy', '.35em')
                .style('font-size', '10px')
                .style('fill', '#333')
                .text(d => `${d.icon} ${d.label}`);
        }

        // Add enhanced tooltips
        node.append('title')
            .text(d => `${d.name}\nAuthor: ${d.author}\nCategory: ${d.category}\nPopularity: ${d.popularity}\n${d.description ? d.description.substring(0, 100) + '...' : ''}`);

        // Set up simulation
        simulation
            .nodes(nodes)
            .on('tick', ticked);

        simulation.force('link')
            .links(links);

        console.log('Graph visualization created successfully');

        function ticked() {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            // Update hover areas to match visible links
            svg.selectAll('.graph-link-hover')
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);

            // Update edge labels only if they exist (for simple graphs)
            if (edgeLabel) {
                edgeLabel
                    .attr('x', d => (d.source.x + d.target.x) / 2)
                    .attr('y', d => (d.source.y + d.target.y) / 2);
            }
        }

        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        // Handle window resize
        const resizeObserver = new ResizeObserver(() => {
            const newWidth = graphContainer.clientWidth;
            const newHeight = graphContainer.clientHeight;
            svg.attr('width', newWidth).attr('height', newHeight);
            simulation.force('center', d3.forceCenter(newWidth / 2, newHeight / 2));
            simulation.alpha(0.3).restart();
        });
        resizeObserver.observe(graphContainer);
        
        console.log('✅ D3.js graph visualization completed successfully!');
        console.log('=== D3.js GRAPH VISUALIZATION DEBUG END ===');
    }

    loadD3AndRetry(servers, graphContainer) {
        console.log('🔄 Attempting to load D3.js dynamically...');
        graphContainer.innerHTML = '<p style="text-align: center; color: #667eea; padding: 2rem;">Loading D3.js visualization...</p>';
        
        // Check if script already exists
        const existingScript = document.querySelector('script[src*="d3js.org"]');
        if (existingScript) {
            console.log('D3.js script already exists, waiting for it to load...');
            
            // Try multiple times with increasing delays
            let attempts = 0;
            const maxAttempts = 10;
            const checkD3 = () => {
                attempts++;
                console.log(`Checking D3.js availability (attempt ${attempts}/${maxAttempts})...`);
                
                if (typeof d3 !== 'undefined' && d3.select && d3.forceSimulation) {
                    console.log('✅ D3.js now available, retrying visualization...');
                    this.createGraphVisualization(servers);
                    return;
                }
                
                if (attempts >= maxAttempts) {
                    console.error('❌ D3.js still not available after multiple attempts');
                    this.createFallbackVisualization(servers, graphContainer);
                    return;
                }
                
                // Wait longer between attempts
                setTimeout(checkD3, 200 * attempts);
            };
            
            checkD3();
            return;
        }
        
        // If no script exists, load it
        console.log('No D3.js script found, loading local file...');
        const script = document.createElement('script');
        script.src = 'd3.v7.min.js';
        script.onload = () => {
            console.log('✅ D3.js loaded successfully, retrying visualization...');
            setTimeout(() => {
                this.createGraphVisualization(servers);
            }, 100);
        };
        script.onerror = () => {
            console.error('❌ Failed to load local D3.js file');
            this.createFallbackVisualization(servers, graphContainer);
        };
        document.head.appendChild(script);
    }

    createFallbackVisualization(servers, graphContainer) {
        console.log('Creating fallback visualization for', servers.length, 'servers');
        
        // Determine if legend should be shown based on graph complexity
        const shouldShowLegend = servers.length <= 10;
        console.log('Fallback graph complexity - Servers:', servers.length);
        console.log('Fallback legend will be shown:', shouldShowLegend);
        
        // Clear the container first
        graphContainer.innerHTML = '';
        
        // Create a simple network visualization using HTML/CSS
        const container = document.createElement('div');
        container.style.cssText = `
            width: 100%;
            height: 100%;
            position: relative;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
            border-radius: 8px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        `;
        
        // Create a network-style visualization
        const networkContainer = document.createElement('div');
        networkContainer.style.cssText = `
            width: 100%;
            height: 100%;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        `;

        // Create tooltip for fallback visualization
        const fallbackTooltip = document.createElement('div');
        fallbackTooltip.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.95);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 400;
            pointer-events: none;
            z-index: 1001;
            opacity: 0;
            transition: opacity 0.15s ease;
            box-shadow: 0 6px 16px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.15);
            max-width: 280px;
            line-height: 1.4;
        `;
        container.appendChild(fallbackTooltip);
        
        // Create a central hub
        const hub = document.createElement('div');
        hub.style.cssText = `
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-weight: bold;
            font-size: 0.8rem;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            z-index: 10;
        `;
        hub.textContent = 'ASKG';
        
        networkContainer.appendChild(hub);
        
        // Create SVG for connecting lines
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        `;
        networkContainer.appendChild(svg);
        
        // Position servers around the hub in a circle
        // Use the graphContainer dimensions for positioning
        const containerRect = graphContainer.getBoundingClientRect();
        console.log('Graph container dimensions:', containerRect.width, 'x', containerRect.height);
        
        // Use a much larger radius to spread nodes out and use the entire available space
        const width = containerRect.width > 0 ? containerRect.width : 400;
        const height = containerRect.height > 0 ? containerRect.height : 200;
        // Use 40% of the smaller dimension to prevent overshooting while still using most of the space
        const radius = Math.min(width, height) * 0.4;
        const centerX = width / 2;
        const centerY = height / 2;
        
        console.log('Center position:', centerX, centerY, 'Radius:', radius);
        
        servers.forEach((server, index) => {
            const angle = (index / servers.length) * 2 * Math.PI;
            
            // Adjust positioning to better use horizontal space
            // Use different radii for x and y to create an elliptical distribution
            const radiusX = width * 0.4; // Use more horizontal space
            const radiusY = height * 0.35; // Use less vertical space to prevent overshooting
            
            const x = centerX + radiusX * Math.cos(angle);
            const y = centerY + radiusY * Math.sin(angle);
            
            console.log(`Server ${server.name}: angle=${angle}, x=${x}, y=${y}, radiusX=${radiusX}, radiusY=${radiusY}`);
            
            // Create connecting line from center to server
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', centerX);
            line.setAttribute('y1', centerY);
            line.setAttribute('x2', x);
            line.setAttribute('y2', y);
            line.setAttribute('stroke', 'rgba(102, 126, 234, 0.4)');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('stroke-dasharray', '5,5');
            svg.appendChild(line);
            
            const serverNode = document.createElement('div');
            serverNode.style.cssText = `
                position: absolute;
                left: ${x}px;
                top: ${y}px;
                transform: translate(-50%, -50%);
                background: white;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 8px;
                padding: 0.5rem;
                font-size: 0.7rem;
                font-weight: 500;
                color: #333;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                cursor: pointer;
                transition: all 0.2s ease;
                max-width: 80px;
                text-align: center;
                word-wrap: break-word;
                z-index: 5;
            `;
            serverNode.textContent = server.name || 'Unknown';
            serverNode.title = server.description || server.name || 'Unknown server';
            
            // Add hover effect with tooltip
            serverNode.addEventListener('mouseenter', (event) => {
                serverNode.style.transform = 'translate(-50%, -50%) scale(1.1)';
                serverNode.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                serverNode.style.borderColor = 'rgba(102, 126, 234, 0.6)';
                // Highlight the connecting line on hover
                line.setAttribute('stroke', 'rgba(102, 126, 234, 0.8)');
                line.setAttribute('stroke-width', '3');
                
                // Show tooltip with server details
                const description = server.description && server.description !== '-' ? 
                    (server.description.length > 80 ? server.description.substring(0, 80) + '...' : server.description) : 
                    'No description available';
                
                const category = server.categories && server.categories.length > 0 ? server.categories[0] : 'other';
                const popularity = server.popularity_score || 0;
                
                fallbackTooltip.innerHTML = `
                    <div style="margin-bottom: 8px;">
                        <strong style="color: #667eea; font-size: 14px;">${server.name}</strong>
                    </div>
                    <div style="margin-bottom: 6px; font-size: 11px; color: #ccc;">
                        <span style="color: #ff6b6b;">👤</span> ${server.author || 'Unknown'}
                        ${popularity > 0 ? `<span style="margin-left: 8px; color: #ffd93d;">⭐</span> ${popularity.toLocaleString()}` : ''}
                    </div>
                    <div style="margin-bottom: 6px; font-size: 11px; color: #ccc;">
                        <span style="color: #4ecdc4;">📂</span> ${category}
                    </div>
                    <div style="font-size: 11px; color: #ddd; line-height: 1.3;">
                        ${description}
                    </div>
                `;
                
                // Position tooltip
                const rect = event.target.getBoundingClientRect();
                const tooltipRect = fallbackTooltip.getBoundingClientRect();
                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight;
                
                let left = rect.left + rect.width / 2 + 15;
                let top = rect.top - 15;
                
                // Adjust if tooltip would go off right edge
                if (left + tooltipRect.width > viewportWidth - 20) {
                    left = rect.left - tooltipRect.width - 15;
                }
                
                // Adjust if tooltip would go off bottom edge
                if (top + tooltipRect.height > viewportHeight - 20) {
                    top = rect.bottom + 15;
                }
                
                // Ensure tooltip doesn't go off left or top edges
                left = Math.max(10, left);
                top = Math.max(10, top);
                
                fallbackTooltip.style.left = left + 'px';
                fallbackTooltip.style.top = top + 'px';
                fallbackTooltip.style.opacity = '1';
            });
            serverNode.addEventListener('mouseleave', () => {
                serverNode.style.transform = 'translate(-50%, -50%) scale(1)';
                serverNode.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                serverNode.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                // Reset the connecting line
                line.setAttribute('stroke', 'rgba(102, 126, 234, 0.4)');
                line.setAttribute('stroke-width', '2');
                
                // Hide tooltip with slight delay to prevent flickering
                setTimeout(() => {
                    fallbackTooltip.style.opacity = '0';
                }, 150);
            });

            // Add click functionality to scroll to server
            serverNode.addEventListener('click', () => {
                this.scrollToServer(server.id);
            });
            
            networkContainer.appendChild(serverNode);
        });
        
        // Add relationship legend to fallback visualization only for simple graphs
        if (shouldShowLegend) {
            const legend = document.createElement('div');
            legend.style.cssText = `
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 6px;
                padding: 8px;
                font-size: 10px;
                color: #333;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            `;
            legend.innerHTML = `
                <div style="margin-bottom: 4px;"><strong>Relationships:</strong></div>
                <div style="display: flex; align-items: center; margin-bottom: 2px;">
                    <div style="width: 20px; height: 2px; background: rgba(255, 99, 132, 0.8); margin-right: 5px;"></div>
                    <span>👤 Same Author</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 2px;">
                    <div style="width: 20px; height: 2px; background: rgba(54, 162, 235, 0.8); margin-right: 5px;"></div>
                    <span>📂 Same Category</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 2px; background: rgba(255, 205, 86, 0.8); margin-right: 5px;"></div>
                    <span>⭐ Similar Popularity</span>
                </div>
            `;
            container.appendChild(legend);
        }
        
        container.appendChild(networkContainer);
        graphContainer.appendChild(container);
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

    expandServerList() {
        console.log('expandServerList called');
        console.log('currentMCPResult:', this.currentMCPResult);
        
        if (!this.currentMCPResult || !this.currentMCPResult.servers) {
            console.log('No MCP result available for expansion');
            return;
        }

        // Find the last AI message and update it with the full server list
        const messages = this.chatMessages.querySelectorAll('.message.ai');
        if (messages.length === 0) return;

        const lastAIMessage = messages[messages.length - 1];
        const messageContent = lastAIMessage.querySelector('.message-content');
        
        if (!messageContent) return;

        // Generate the full server list content
        let fullContent = `I found ${this.currentMCPResult.servers.length} MCP servers related to your query.\n\n`;
        fullContent += `**All MCP Servers:**\n\n`;
        
        this.currentMCPResult.servers.forEach((server, index) => {
            fullContent += `${index + 1}. **${server.name}**`;
            if (server.repository) {
                fullContent += ` - [Repository](${server.repository})`;
            }
            fullContent += `\n`;
            
            if (server.description) {
                fullContent += `   ${server.description}\n`;
            }
            
            if (server.categories && server.categories.length > 0) {
                const categories = server.categories.map(cat => cat.value).join(', ');
                fullContent += `   **Categories:** ${categories}\n`;
            }
            
            if (server.author) {
                fullContent += `   **Author:** ${server.author}\n`;
            }
            
            fullContent += `\n`;
        });
        
        fullContent += `Check the knowledge graph pane for detailed information and interactive exploration.`;
        
        // Update the message content
        messageContent.innerHTML = `
            ${this.formatMessageContent(fullContent)}
            <div class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        `;
        
        // Show notification that the list was expanded
        this.showNotification(`Expanded to show all ${this.currentMCPResult.servers.length} servers`, 'success');
    }

    initializeResizeDivider() {
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;
        let wheelResizeTimeout = null;

        const startResize = (e) => {
            // Don't allow resizing if knowledge graph is collapsed
            if (this.knowledgeGraphSidebar.classList.contains('collapsed')) {
                return;
            }
            
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
            
            // Redraw the graph visualization after resize
            this.redrawGraphVisualization();
        };

        // Mouse wheel resize functionality
        const handleWheelResize = (e) => {
            // Only allow wheel resize when hovering over the resize divider or knowledge graph
            const target = e.target;
            const isOverResizeDivider = target === this.resizeDivider || this.resizeDivider.contains(target);
            const isOverKnowledgeGraph = this.knowledgeGraphSidebar.contains(target);
            
            if (!isOverResizeDivider && !isOverKnowledgeGraph) return;
            
            // Don't allow wheel resize if knowledge graph is collapsed
            if (this.knowledgeGraphSidebar.classList.contains('collapsed')) {
                return;
            }
            
            e.preventDefault();
            
            // Add visual feedback
            this.resizeDivider.classList.add('wheel-resize');
            setTimeout(() => {
                this.resizeDivider.classList.remove('wheel-resize');
            }, 500);
            
            const currentWidth = this.knowledgeGraphSidebar.offsetWidth;
            const delta = e.deltaY > 0 ? -20 : 20; // Scroll down = smaller, scroll up = larger
            const newWidth = Math.max(250, Math.min(600, currentWidth + delta));
            
            // Smooth resize animation
            this.knowledgeGraphSidebar.style.transition = 'width 0.2s ease';
            this.knowledgeGraphSidebar.style.width = newWidth + 'px';
            
            // Remove transition after animation
            setTimeout(() => {
                this.knowledgeGraphSidebar.style.transition = '';
            }, 200);
            
            // Debounced redraw
            clearTimeout(wheelResizeTimeout);
            wheelResizeTimeout = setTimeout(() => {
                this.redrawGraphVisualization();
            }, 250);
        };

        // Mouse events
        this.resizeDivider.addEventListener('mousedown', startResize);
        document.addEventListener('mousemove', doResize);
        document.addEventListener('mouseup', stopResize);

        // Touch events for mobile with improved gesture support
        this.resizeDivider.addEventListener('touchstart', (e) => {
            e.preventDefault();
            startResize(e.touches[0]);
        });
        
        document.addEventListener('touchmove', (e) => {
            if (isResizing) {
                e.preventDefault();
                doResize(e.touches[0]);
            }
        });
        
        document.addEventListener('touchend', stopResize);



        // Prevent text selection during resize
        this.resizeDivider.addEventListener('selectstart', (e) => {
            e.preventDefault();
        });
        
        // Add resize observer to knowledge graph container
        this.initializeGraphResizeObserver();
    }

    redrawGraphVisualization() {
        if (this.currentServers && this.currentServers.length > 0) {
            console.log('Redrawing graph visualization after resize');
            setTimeout(() => {
                this.createGraphVisualization(this.currentServers);
            }, 100); // Small delay to ensure resize is complete
        }
    }

    initializeGraphResizeObserver() {
        // Create a resize observer to watch for changes in the knowledge graph container
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                console.log('Knowledge graph container resized:', entry.contentRect);
                // Debounce the redraw to avoid too many redraws
                clearTimeout(this.resizeTimeout);
                this.resizeTimeout = setTimeout(() => {
                    this.redrawGraphVisualization();
                }, 150);
            }
        });
        
        // Start observing the knowledge graph content container
        if (this.knowledgeGraphContent) {
            resizeObserver.observe(this.knowledgeGraphContent);
        }
    }

    // Removed initializeSampleData() method - no longer needed for clean startup
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
    
    .chat-history-item .chat-id {
        font-size: 0.7rem;
        color: #888;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .no-chats {
        text-align: center;
        padding: 2rem 1rem;
        color: #666;
    }
    
    .no-chats i {
        font-size: 2rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    .no-chats p {
        margin: 0.5rem 0;
        font-weight: 500;
    }
    
    .no-chats small {
        opacity: 0.7;
    }
    
    .modal-overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 10000;
        justify-content: center;
        align-items: center;
    }
    
    .modal-content {
        background: white;
        border-radius: 12px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem 1.5rem 1rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .modal-header h3 {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .modal-close {
        background: none;
        border: none;
        font-size: 1.25rem;
        cursor: pointer;
        color: #6b7280;
        padding: 0.25rem;
        border-radius: 4px;
        transition: color 0.2s;
    }
    
    .modal-close:hover {
        color: #374151;
    }
    
    .modal-body {
        padding: 1.5rem;
    }
    
    .setting-item {
        margin-bottom: 1.5rem;
    }
    
    .setting-item label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #374151;
    }
    
    .setting-item input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 1rem;
        transition: border-color 0.2s;
    }
    
    .setting-item input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .setting-item small {
        display: block;
        margin-top: 0.5rem;
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    .modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 0.75rem;
        padding: 1rem 1.5rem 1.5rem;
        border-top: 1px solid #e5e7eb;
    }
    
    .btn {
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .btn-primary {
        background-color: #3b82f6;
        color: white;
    }
    
    .btn-primary:hover {
        background-color: #2563eb;
    }
    
    .btn-secondary {
        background-color: #f3f4f6;
        color: #374151;
    }
    
    .btn-secondary:hover {
        background-color: #e5e7eb;
    }
`;
document.head.appendChild(style);

// Initialize the app when DOM is loaded and D3.js is available
document.addEventListener('DOMContentLoaded', () => {
    // Check if D3.js is already loaded
    if (typeof d3 !== 'undefined' && d3) {
        console.log('D3.js already loaded, initializing app...');
        window.askgApp = new AskGChatApp();
    } else {
        console.log('D3.js not loaded yet, waiting...');
        // Wait a bit for D3.js to load, then initialize
        setTimeout(() => {
            if (typeof d3 !== 'undefined' && d3) {
                console.log('D3.js loaded after delay, initializing app...');
                window.askgApp = new AskGChatApp();
            } else {
                console.log('D3.js still not available, initializing app anyway...');
                window.askgApp = new AskGChatApp();
            }
        }, 1000);
    }
}); 