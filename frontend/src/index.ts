import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import path from 'path';

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// MCP Server configuration
const MCP_SERVER_URL = 'http://localhost:8080';

// Middleware
app.use(helmet());
app.use(compression());
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// Serve the main HTML file
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Function to call MCP server
async function callMCPServer(prompt: string, maxResults: number = 20) {
  try {
    const response = await fetch(`${MCP_SERVER_URL}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now().toString(),
        method: 'search_servers',
        params: {
          prompt: prompt,
          limit: maxResults,
          min_confidence: 0.5
        }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json() as any;
    return data.result || data;
  } catch (error) {
    console.error('Error calling MCP server:', error);
    return null;
  }
}

// WebSocket connection handling
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  // Handle chat messages
  socket.on('chat_message', async (data) => {
    console.log('Received message:', data);
    
    // Call MCP server to search for relevant servers
    const maxResults = data.maxResults || 20;
    const mcpResult = await callMCPServer(data.content, maxResults);
    console.log('MCP server result:', mcpResult);
    
    // Send response back to client
    const response = {
      id: Date.now().toString(),
      type: 'ai',
      content: `I found ${mcpResult?.servers?.length || 0} MCP servers related to your query: "${data.content}". Check the knowledge graph pane for details.`,
      timestamp: new Date().toISOString()
    };
    
    socket.emit('chat_response', response);
    
    // Send MCP server results to update knowledge graph
    if (mcpResult && mcpResult.servers) {
      console.log('Sending MCP servers to client:', mcpResult.servers.length, 'servers');
      socket.emit('mcp_servers_result', {
        servers: mcpResult.servers,
        total_found: mcpResult.total_found,
        search_metadata: mcpResult.search_metadata
      });
    } else {
      console.log('No MCP servers to send to client');
    }
  });

  // Handle new chat creation
  socket.on('new_chat', () => {
    console.log('New chat requested');
    socket.emit('chat_cleared');
  });

  // Handle chat save
  socket.on('save_chat', (chatData) => {
    console.log('Chat save requested:', chatData);
    // In a real app, this would save to a database
    socket.emit('chat_saved', { success: true, message: 'Chat saved successfully' });
  });

  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
  });
});

const PORT = process.env.PORT || 3000;

server.listen(PORT, () => {
  console.log(`askg Chat Server running on port ${PORT}`);
  console.log(`Open http://localhost:${PORT} in your browser`);
}); 