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
        this.initializeSampleData();
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
        this.knowledgeGraphContent = document.getElementById('knowledgeGraphContent');
        this.resizeDivider = document.getElementById('resizeDivider');
        this.knowledgeGraphSidebar = document.getElementById('knowledgeGraphSidebar');
        
        // Settings modal elements
        this.settingsModal = document.getElementById('settingsModal');
        this.closeSettingsBtn = document.getElementById('closeSettings');
        this.cancelSettingsBtn = document.getElementById('cancelSettings');
        this.saveSettingsBtn = document.getElementById('saveSettings');
        this.maxResultsInput = document.getElementById('maxResults');
        
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
                <div class="loading-indicator">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Searching for MCP servers...</p>
                </div>
            </div>
            <div class="server-list-container" id="serverListContainer">
            </div>
        `;
        
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
        this.currentChatId = this.nextChatId.toString();
        this.nextChatId++;
        this.addChatToHistory('New Chat', this.currentChatId);
        
        // Clear knowledge graph pane
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

    addChatToHistory(title, id) {
        const chatItem = {
            id: id,
            title: title,
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
                <div class="chat-title">${chat.title}</div>
                <div class="chat-time">${timeString}</div>
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
        this.settingsModal.style.display = 'flex';
        this.maxResultsInput.value = this.maxResults;
    }

    closeSettings() {
        this.settingsModal.style.display = 'none';
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
        
        // Store the servers data for potential redrawing
        this.currentServers = result.servers || [];
        
        if (!result || !result.servers || result.servers.length === 0) {
            console.log('No servers found, showing empty state');
            this.currentServers = [];
            this.knowledgeGraphContent.innerHTML = `
                <div class="graph-visualization" id="graphVisualization">
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <p>No MCP servers found for your query.</p>
                    </div>
                </div>
                <div class="server-list-container" id="serverListContainer">
                </div>
            `;
            return;
        }

        console.log('Creating visualization for', result.servers.length, 'servers');

        // Create server list HTML first
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

        // Update the content structure
        this.knowledgeGraphContent.innerHTML = `
            <div class="graph-visualization" id="graphVisualization">
                <!-- Graph will be rendered here -->
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

        console.log('DOM updated, creating graph visualization');
        console.log('Graph container after DOM update:', document.getElementById('graphVisualization'));
        
        // Create graph visualization after DOM is updated
        setTimeout(() => {
            console.log('Timeout fired, calling createGraphVisualization...');
            this.createGraphVisualization(result.servers);
        }, 100);
    }

    createGraphVisualization(servers) {
        console.log('createGraphVisualization called with:', servers);
        console.log('Servers data:', servers);
        
        const graphContainer = document.getElementById('graphVisualization');
        console.log('Looking for graphVisualization element:', graphContainer);
        
        if (!graphContainer) {
            console.error('Graph container not found!');
            console.log('Available elements with graph in name:');
            document.querySelectorAll('[id*="graph"]').forEach(el => {
                console.log('Found element:', el.id, el);
            });
            return;
        }

        console.log('Graph container found:', graphContainer);
        console.log('Container dimensions:', graphContainer.clientWidth, 'x', graphContainer.clientHeight);
        console.log('Container computed styles:', window.getComputedStyle(graphContainer));

        // Clear existing content
        graphContainer.innerHTML = '';

        // Add a test message to see if the container is working
        graphContainer.innerHTML = '<p style="color: blue; text-align: center; padding: 1rem;">Creating visualization...</p>';

        // For now, let's use the fallback visualization to ensure something shows up
        console.log('Using fallback visualization for now');
        this.createFallbackVisualization(servers, graphContainer);
        return;

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

        // Create force simulation
        const simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));

        // Create nodes from servers
        const nodes = servers.map((server, index) => ({
            id: server.id || `server-${index}`,
            name: server.name || 'Unknown',
            category: server.categories && server.categories.length > 0 ? server.categories[0] : 'other',
            popularity: server.popularity_score || 0,
            author: server.author || 'Unknown'
        }));

        console.log('Created nodes:', nodes);

        // Create links between nodes (simplified - connect to nearest nodes)
        const links = [];
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < Math.min(i + 3, nodes.length); j++) {
                links.push({
                    source: nodes[i].id,
                    target: nodes[j].id,
                    value: 1
                });
            }
        }

        console.log('Created links:', links);

        // Color scale for categories
        const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

        // Create links
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'graph-link');

        // Create nodes
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('class', 'graph-node')
            .attr('r', d => Math.max(8, Math.min(20, Math.sqrt(d.popularity) / 10)))
            .attr('fill', d => colorScale(d.category))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
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
            .text(d => d.name.length > 10 ? d.name.substring(0, 10) + '...' : d.name)
            .attr('dy', '.35em');

        // Add tooltips
        node.append('title')
            .text(d => `${d.name}\nAuthor: ${d.author}\nCategory: ${d.category}\nPopularity: ${d.popularity}`);

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

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
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
    }

    loadD3AndRetry(servers, graphContainer) {
        console.log('Attempting to load D3.js dynamically...');
        graphContainer.innerHTML = '<p>Loading D3.js...</p>';
        
        const script = document.createElement('script');
        script.src = 'https://d3js.org/d3.v7.min.js';
        script.onload = () => {
            console.log('D3.js loaded successfully, retrying visualization...');
            setTimeout(() => {
                this.createGraphVisualization(servers);
            }, 100);
        };
        script.onerror = () => {
            console.error('Failed to load D3.js');
            this.createFallbackVisualization(servers, graphContainer);
        };
        document.head.appendChild(script);
    }

    createFallbackVisualization(servers, graphContainer) {
        console.log('Creating fallback visualization for', servers.length, 'servers');
        
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
            
            // Add hover effect
            serverNode.addEventListener('mouseenter', () => {
                serverNode.style.transform = 'translate(-50%, -50%) scale(1.1)';
                serverNode.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                serverNode.style.borderColor = 'rgba(102, 126, 234, 0.6)';
                // Highlight the connecting line on hover
                line.setAttribute('stroke', 'rgba(102, 126, 234, 0.8)');
                line.setAttribute('stroke-width', '3');
            });
            serverNode.addEventListener('mouseleave', () => {
                serverNode.style.transform = 'translate(-50%, -50%) scale(1)';
                serverNode.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                serverNode.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                // Reset the connecting line
                line.setAttribute('stroke', 'rgba(102, 126, 234, 0.4)');
                line.setAttribute('stroke-width', '2');
            });
            
            networkContainer.appendChild(serverNode);
        });
        
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
            
            // Redraw the graph visualization after resize
            this.redrawGraphVisualization();
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

    initializeSampleData() {
        // Add sample chat history if none exists
        if (this.chatHistory.length === 0) {
            const sampleChats = [
                {
                    id: '1',
                    title: 'Database servers',
                    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() // 1 day ago
                },
                {
                    id: '2', 
                    title: 'File system tools',
                    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() // 2 hours ago
                },
                {
                    id: '3',
                    title: 'API integration services',
                    timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString() // 30 minutes ago
                }
            ];
            
            this.chatHistory = sampleChats;
            this.nextChatId = 4; // Start from 4 since we have 3 sample chats
            this.saveChatHistory();
            this.renderChatHistory();
        }
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
        new AskGChatApp();
    } else {
        console.log('D3.js not loaded yet, waiting...');
        // Wait a bit for D3.js to load, then initialize
        setTimeout(() => {
            if (typeof d3 !== 'undefined' && d3) {
                console.log('D3.js loaded after delay, initializing app...');
                new AskGChatApp();
            } else {
                console.log('D3.js still not available, initializing app anyway...');
                new AskGChatApp();
            }
        }, 1000);
    }
}); 