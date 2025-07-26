# ASKG - AI Server Knowledge Graph

A powerful chat interface for discovering and exploring MCP (Model Context Protocol) servers with an interactive knowledge graph visualization.

## 🚀 Features

### AI-Powered Query Conversion
- **LLM-Enhanced Search**: Converts natural language queries to Cypher using GPT-4o-mini
- **Intelligent Fallback**: Robust fallback mechanism for complex queries
- **Text-First Relevance**: Prioritizes text matches over popularity for better results
- **Multi-Strategy Search**: Combines semantic search with keyword matching

### Real-time Search Results
- **Live Server Discovery**: Instant results from Neo4j database
- **Comprehensive Metadata**: Server details, tools, categories, and popularity
- **Smart Filtering**: Intelligent relevance scoring and result ranking
- **Query Processing**: Advanced text-to-Cypher conversion with fallback

### Interactive Chat Interface
- **Persistent Chat History**: Automatic saving and loading of conversations
- **Dynamic Chat Titles**: Auto-generated titles based on first interaction
- **Chat Management**: Rename, delete, and organize chat sessions
- **Server Details Modal**: Comprehensive server information with tools display
- **Enhanced Modal Design**: Wider modal with better layout and scrolling

### Interactive Knowledge Graph
- **D3.js-Powered Visualization**: Dynamic, interactive graph with force-directed layout
- **Clickable Nodes**: Click nodes to scroll to corresponding servers in the list
- **Smart Node Interaction**: Hover for detailed server summaries
- **Flexible Graph Resizing**: Drag and mouse wheel controls for graph height (20%-50%)
- **Touch Support**: Mobile-friendly gesture controls
- **Auto-Redraw**: Responsive layout adjustments
- **Visual Feedback**: Smooth animations and hover effects
- **Fallback Support**: HTML-based visualization when D3.js unavailable

### Enhanced Graph Interactions
- **Node Tooltips**: Detailed server information on hover (name, author, popularity, category, description)
- **Edge Information**: Relationship details with hover tooltips (same author, same category, similar popularity)
- **Improved Hover Sensitivity**: Larger invisible hover areas for better edge detection
- **Smart Tooltip Positioning**: Automatic positioning to avoid screen edges
- **Relationship Visualization**: Color-coded edges with icons and legends

### Advanced UI/UX
- **Resizable Layout**: Adjustable knowledge graph pane width
- **Collapsible Sections**: Toggle chat history and knowledge graph visibility
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Theme**: Modern, eye-friendly interface
- **Smooth Animations**: Professional transitions and effects

## 🛠️ Installation

### Prerequisites
- Node.js (v16 or higher)
- Python 3.8+
- Neo4j Desktop or Neo4j Community Edition
- OpenAI API key (for advanced query conversion)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd askg
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Add your OpenAI API key to .env
   ```

5. **Start Neo4j**
   - Open Neo4j Desktop
   - Start your database instance

6. **Run the application**
   ```bash
   # Terminal 1: Start backend
   python mcp/server.py
   
   # Terminal 2: Start frontend
   cd frontend
   npm start
   ```

7. **Open in browser**
   - Navigate to `http://localhost:3000`

## 📖 Usage

### Basic Search
- Type queries like "crypto servers", "AI tools", or "popular blockchain servers"
- Results appear instantly with server details and tools

### Advanced Queries
- **Complex Queries**: "Find servers for cryptocurrency trading with high popularity"
- **Category-Based**: "Show me all AI assistant servers"
- **Author-Specific**: "Servers by OpenAI or Anthropic"

### Graph Interaction
- **Hover over nodes**: See detailed server information
- **Hover over edges**: View relationship details
- **Click nodes**: Scroll to server in the list
- **Resize graph**: Drag or use mouse wheel to adjust height
- **Explore relationships**: Understand connections between servers

### Chat Management
- **Start new chat**: Click "New Chat" button
- **Rename chats**: Click on chat title to edit
- **Delete chats**: Use trash icon in chat history
- **Persistent storage**: All chats saved automatically

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Neo4j Setup
1. Create a new database in Neo4j Desktop
2. Import MCP server data using the provided scripts
3. Configure connection settings in `.config.yaml`

## 🏗️ Architecture

### Frontend
- **Vanilla JavaScript**: No framework dependencies
- **Socket.IO**: Real-time communication
- **D3.js**: Interactive graph visualization
- **Local Storage**: Chat persistence

### Backend
- **Python**: FastAPI-based MCP server
- **Neo4j**: Graph database for server relationships
- **OpenAI API**: LLM-powered query conversion
- **Text2Cypher**: Intelligent query processing

### Data Flow
1. User query → Frontend
2. Frontend → Backend (Socket.IO)
3. Backend → Text2Cypher conversion
4. Text2Cypher → Neo4j (Cypher query)
5. Neo4j → Backend (results)
6. Backend → Frontend (formatted data)
7. Frontend → Graph visualization + Server list

## 🧪 Testing

### Run Tests
```bash
# Python tests
uv run pytest

# Frontend tests (if available)
cd frontend
npm test
```

### Test Queries
- "crypto" - Should return cryptocurrency-related servers
- "AI servers" - Should return AI/ML servers
- "popular servers" - Should return high-popularity servers
- "enterprise" - Should return enterprise-focused servers

## 📊 Performance

### Query Processing
- **LLM Conversion**: ~2-3 seconds for complex queries
- **Fallback Detection**: Immediate for failed conversions
- **Neo4j Response**: <500ms for most queries
- **Frontend Rendering**: <1 second for graph updates

### Scalability
- **Database**: Supports 10,000+ servers
- **Graph Visualization**: Optimized for 100+ nodes
- **Real-time Updates**: WebSocket-based communication
- **Memory Usage**: Efficient data structures and caching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines
- Follow existing code style
- Add documentation for new features
- Test thoroughly before submitting
- Update README for significant changes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Neo4j**: Graph database technology
- **D3.js**: Data visualization library
- **OpenAI**: LLM-powered query conversion
- **MCP Community**: Model Context Protocol specification

## 📞 Support

For issues and questions:
1. Check the [documentation](docs/)
2. Search existing issues
3. Create a new issue with detailed information

## 🔄 Recent Updates

### Latest Features (v2.0)
- **Enhanced Node Tooltips**: Detailed server information on hover
- **Improved Edge Hover**: Better sensitivity and relationship information
- **Smart Tooltip Positioning**: Automatic edge detection and positioning
- **Graph Resizing Controls**: Flexible height adjustment (20%-50%)
- **Touch Support**: Mobile-friendly gesture controls
- **Performance Optimizations**: Faster rendering and smoother interactions

### Previous Updates
- **AI-Powered Query Conversion**: LLM-enhanced search with intelligent fallback
- **Server Details Modal**: Comprehensive server information display
- **Interactive Knowledge Graph**: D3.js-powered visualization with clickable nodes
- **Chat History Management**: Persistent storage with rename/delete functionality
- **Responsive Design**: Mobile-friendly interface with collapsible sections
