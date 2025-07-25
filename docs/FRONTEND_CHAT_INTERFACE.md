# Frontend Chat Interface Documentation

## Overview

The ASKG frontend provides a modern, interactive chat interface for discovering and exploring MCP servers. Built with vanilla JavaScript, Socket.IO, and D3.js, it offers a seamless user experience with real-time search, persistent chat history, and an interactive knowledge graph visualization.

## 🚀 Core Features

### Real-time Search Results
- **Instant Query Processing**: Real-time search with immediate results
- **Intelligent Fallback**: Automatic fallback to keyword-based search when LLM queries fail
- **Text-First Relevance**: Prioritizes actual text matches over popularity scores
- **Comprehensive Metadata**: Server details, tools, categories, and popularity information
- **Smart Filtering**: Intelligent relevance scoring and result ranking

### Interactive Chat Interface
- **Persistent Chat History**: Automatic saving and loading of conversations using localStorage
- **Dynamic Chat Titles**: Auto-generated titles based on the first user interaction
- **Chat Management**: Rename, delete, and organize chat sessions
- **Real-time Updates**: Live search results with typing indicators
- **Responsive Design**: Works seamlessly on desktop and mobile devices

### Server Details Modal
- **Comprehensive Information**: Complete server details including tools, metadata, and installation instructions
- **Tools Display**: Scrollable list of exposed tools with detailed descriptions and input parameters
- **Enhanced Layout**: Wider modal (1000px) with better spacing and responsive design
- **Multiple Close Options**: X button, Close button, and clicking outside modal
- **Smooth Animations**: Professional transitions and hover effects

### Interactive Knowledge Graph Visualization
- **D3.js-Powered**: Dynamic, interactive graph with force-directed layout
- **Clickable Nodes**: Click nodes to scroll to corresponding servers in the list
- **Smart Node Interaction**: Hover for detailed server summaries without auto-opening details
- **Flexible Graph Resizing**: Drag and mouse wheel controls for graph height (20%-50% of pane height)
- **Touch Support**: Mobile-friendly gesture controls
- **Auto-Redraw**: Responsive layout adjustments
- **Visual Feedback**: Smooth animations and hover effects
- **Fallback Support**: HTML-based visualization when D3.js unavailable
- **Duplicate Edge Prevention**: Smart link creation prevents duplicate edges between the same node pairs
- **Conditional Legend Display**: Legend automatically hidden for complex graphs (more than 10 nodes or more than 5×nodes edges) to reduce visual clutter

### Enhanced Graph Interactions
- **Node Tooltips**: Detailed server information on hover including:
  - Server name (prominently displayed)
  - Author with person icon
  - Popularity score with star icon (if available)
  - Category with folder icon
  - Description (truncated to 80 characters for readability)
- **Edge Information**: Relationship details with hover tooltips:
  - Same author relationships (red edges)
  - Same category relationships (blue edges)
  - Similar popularity relationships (yellow edges)
- **Improved Hover Sensitivity**: Larger invisible hover areas (12px width) for better edge detection
- **Smart Tooltip Positioning**: Automatic positioning to avoid screen edges
- **Relationship Visualization**: Color-coded edges with icons and legends

### Advanced UI/UX Features
- **Resizable Layout**: Adjustable knowledge graph pane width with drag controls
- **Collapsible Sections**: Toggle chat history and knowledge graph visibility
- **Dark Theme**: Modern, eye-friendly interface with consistent styling
- **Smooth Animations**: Professional transitions and hover effects throughout
- **Mobile Responsive**: Optimized for touch devices and smaller screens

## 🏗️ Technical Architecture

### Frontend Stack
- **Vanilla JavaScript**: No framework dependencies for maximum performance
- **Socket.IO**: Real-time communication with backend MCP server
- **D3.js**: Interactive graph visualization with force-directed layout
- **Local Storage**: Chat persistence and session management
- **CSS3**: Modern styling with animations and responsive design

### Key Components

#### Chat Interface (`app.js`)
- **Message Handling**: Send/receive messages with real-time updates
- **Chat History**: Persistent storage and management
- **UI Updates**: Dynamic rendering of search results and chat messages
- **Event Handling**: User interactions and form submissions

#### Graph Visualization (`app.js`)
- **D3.js Integration**: Force-directed graph layout and interactions
- **Node Management**: Server representation with hover and click events
- **Edge Visualization**: Relationship display with tooltips and styling
- **Responsive Design**: Auto-adjustment to container size changes

#### Server Details Modal (`app.js`)
- **Modal Management**: Show/hide with smooth animations
- **Content Rendering**: Dynamic HTML generation for server information
- **Tool Display**: Formatted tool lists with input parameter details
- **Responsive Layout**: Adaptive design for different screen sizes

## 📱 User Interface Elements

### Chat Interface
```
┌─────────────────────────────────────────────────────────────┐
│ Chat History Panel (Collapsible)                           │
│ ├─ New Chat                                                │
│ ├─ Chat 1: "Find crypto servers"                          │
│ ├─ Chat 2: "AI tools for development"                     │
│ └─ [Trash Icons for Delete]                               │
├─────────────────────────────────────────────────────────────┤
│ Message Area                                               │
│ ├─ User: "Find popular crypto servers"                    │
│ ├─ Assistant: Found 5 servers...                          │
│ └─ [Server Cards with Details]                            │
├─────────────────────────────────────────────────────────────┤
│ Input Area                                                 │
│ ├─ [Text Input with Auto-resize]                          │
│ └─ [Send Button]                                          │
└─────────────────────────────────────────────────────────────┘
```

### Knowledge Graph Panel
```
┌─────────────────────────────────────────────────────────────┐
│ Knowledge Graph Header                                     │
│ ├─ [Toggle Button]                                         │
│ ├─ [Resize Handle]                                         │
│ └─ [Collapse Button]                                       │
├─────────────────────────────────────────────────────────────┤
│ Graph Visualization Area                                   │
│ ├─ [D3.js Interactive Graph]                               │
│ ├─ [Node Tooltips on Hover]                                │
│ ├─ [Edge Tooltips on Hover]                                │
│ ├─ [Resize Handle for Height]                              │
│ └─ [Legend for Relationships]                              │
└─────────────────────────────────────────────────────────────┘
```

### Server Details Modal
```
┌─────────────────────────────────────────────────────────────┐
│ Modal Overlay                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Modal Header                                            │ │
│ │ ├─ Server Name                                          │ │
│ │ ├─ [X Close Button]                                     │ │
│ │ └─ [Close Button]                                       │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Modal Body                                              │ │
│ │ ├─ Description                                          │ │
│ │ ├─ Metadata (Author, Repository, Language)              │ │
│ │ ├─ Categories                                           │ │
│ │ ├─ Tools Section (Scrollable)                           │ │
│ │ │  ├─ Tool 1: Description + Input Parameters            │ │
│ │ │  ├─ Tool 2: Description + Input Parameters            │ │
│ │ │  └─ [More Tools...]                                   │ │
│ │ └─ Installation Instructions                             │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 User Interactions

### Chat Management
1. **Start New Chat**: Click "New Chat" button to begin fresh conversation
2. **Rename Chat**: Click on chat title to edit (inline editing)
3. **Delete Chat**: Click trash icon next to chat in history panel
4. **Load Chat**: Click on any chat in history to load previous conversation

### Search and Discovery
1. **Natural Language Queries**: Type questions like "Find crypto servers" or "Show me AI tools"
2. **Real-time Results**: See results appear instantly as you type
3. **Server Details**: Click on any server card to view comprehensive information
4. **Tool Exploration**: Browse exposed tools and their parameters in the modal

### Graph Interaction
1. **Node Hover**: Hover over nodes to see detailed server information
2. **Node Click**: Click nodes to scroll to corresponding server in the list
3. **Edge Hover**: Hover over edges to see relationship details
4. **Graph Resizing**: Drag resize handle or use mouse wheel to adjust graph height
5. **Pane Resizing**: Drag divider to adjust knowledge graph pane width

### Modal Interaction
1. **Open Modal**: Click on any server card in the results list
2. **Browse Tools**: Scroll through the tools list to see available functionality
3. **Close Modal**: Use X button, Close button, or click outside modal
4. **Responsive Design**: Modal adapts to different screen sizes

## 🔧 Configuration

### Environment Variables
```bash
# Frontend configuration (if needed)
NODE_ENV=development
PORT=3000
SOCKET_URL=http://localhost:8200
```

### Local Storage Keys
```javascript
// Chat history persistence
'askg_chat_history' // Array of chat objects
'askg_current_chat' // Current chat ID
'askg_settings'     // User preferences
```

## 📊 Performance Optimization

### Rendering Optimizations
- **Virtual Scrolling**: Efficient rendering of large server lists
- **Debounced Search**: Prevents excessive API calls during typing
- **Lazy Loading**: Load graph visualization only when needed
- **Caching**: Cache search results and chat history locally

### Graph Performance
- **Force Simulation**: Optimized D3.js force-directed layout
- **Node Clustering**: Group similar nodes for better performance
- **Progressive Loading**: Load graph data incrementally
- **Memory Management**: Clean up event listeners and DOM elements

### Mobile Optimization
- **Touch Events**: Optimized touch interactions for mobile devices
- **Responsive Design**: Adaptive layout for different screen sizes
- **Gesture Support**: Swipe and pinch gestures for graph interaction
- **Performance Tuning**: Reduced animations and effects on mobile

## 🧪 Testing

### Manual Testing Scenarios
1. **Chat Functionality**: Create, rename, delete, and load chats
2. **Search Queries**: Test various natural language queries
3. **Graph Interaction**: Hover, click, and resize graph elements
4. **Modal Functionality**: Open, browse, and close server details
5. **Responsive Design**: Test on different screen sizes
6. **Performance**: Test with large datasets and many servers

### Browser Compatibility
- **Chrome**: Full support (recommended)
- **Firefox**: Full support
- **Safari**: Full support
- **Edge**: Full support
- **Mobile Browsers**: Responsive design support

## 🐛 Troubleshooting

### Common Issues

#### Chat History Not Saving
- Check browser localStorage support
- Verify localStorage quota not exceeded
- Clear browser cache and try again

#### Graph Not Loading
- Check D3.js library availability
- Verify network connectivity
- Check browser console for errors
- Try refreshing the page

#### Modal Not Opening
- Check for JavaScript errors in console
- Verify server data structure
- Clear browser cache
- Check CSS conflicts

#### Performance Issues
- Reduce number of displayed servers
- Close other browser tabs
- Check system memory usage
- Use hardware acceleration if available

### Debug Mode
Enable debug logging by setting localStorage:
```javascript
localStorage.setItem('askg_debug', 'true');
```

## 🔄 Future Enhancements

### Planned Features
- **Advanced Filtering**: Multi-criteria server filtering
- **Graph Analytics**: Server usage patterns and trends
- **Custom Layouts**: User-defined graph visualization options
- **Export Functionality**: Export visualizations and data
- **Collaborative Features**: Shared chat sessions and annotations

### Technical Improvements
- **Web Workers**: Background processing for large datasets
- **Service Workers**: Offline functionality and caching
- **Progressive Web App**: Installable web application
- **Accessibility**: Screen reader support and keyboard navigation
- **Internationalization**: Multi-language support

## 📚 API Reference

### Socket.IO Events

#### Client to Server
```javascript
// Send search query
socket.emit('message', {
    content: 'Find crypto servers',
    timestamp: '2024-01-01T12:00:00Z',
    maxResults: 5
});
```

#### Server to Client
```javascript
// Receive search results
socket.on('mcp_servers', (data) => {
    console.log('Received servers:', data.servers);
    console.log('Total found:', data.total_found);
    console.log('Search metadata:', data.search_metadata);
});
```

### Local Storage API

#### Chat History
```javascript
// Save chat
const chat = {
    id: 'chat_123',
    title: 'Find crypto servers',
    messages: [...],
    timestamp: Date.now()
};
localStorage.setItem('askg_chat_history', JSON.stringify([...chats, chat]));

// Load chats
const chats = JSON.parse(localStorage.getItem('askg_chat_history') || '[]');
```

### D3.js Graph API

#### Node Creation
```javascript
const node = svg.append('g')
    .selectAll('circle')
    .data(nodes)
    .enter().append('circle')
    .attr('class', 'graph-node')
    .on('mouseover', handleNodeHover)
    .on('click', handleNodeClick);
```

#### Edge Creation
```javascript
const link = svg.append('g')
    .selectAll('line')
    .data(links)
    .enter().append('line')
    .attr('class', 'graph-link')
    .on('mouseover', handleEdgeHover);
```

## 📖 Example Queries

### Basic Queries
- "crypto" - Find cryptocurrency-related servers
- "AI servers" - Find AI/ML servers
- "popular servers" - Find high-popularity servers
- "enterprise" - Find enterprise-focused servers

### Complex Queries
- "Find servers for cryptocurrency trading with high popularity"
- "Show me all AI assistant servers by popular authors"
- "What are the best blockchain servers for enterprise use?"
- "Find servers that can read and write files"

### Category-Based Queries
- "database servers"
- "file system tools"
- "monitoring servers"
- "development tools"

## 🎨 Styling and Theming

### CSS Variables
```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --background-color: #1a1a1a;
    --text-color: #ffffff;
    --border-color: #333333;
    --hover-color: #4a5568;
}
```

### Responsive Breakpoints
```css
/* Mobile */
@media (max-width: 768px) { ... }

/* Tablet */
@media (min-width: 769px) and (max-width: 1024px) { ... }

/* Desktop */
@media (min-width: 1025px) { ... }
```

This documentation provides comprehensive coverage of the frontend chat interface, including all recent enhancements and technical details for developers and users alike. 