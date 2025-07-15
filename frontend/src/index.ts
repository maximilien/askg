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

// WebSocket connection handling
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  // Handle chat messages
  socket.on('chat_message', (data) => {
    console.log('Received message:', data);
    
    // Echo back the message for now (in a real app, this would go to the AI agent)
    const response = {
      id: Date.now().toString(),
      type: 'ai',
      content: `I received your message: "${data.content}". This is a placeholder response from the askg AI agent.`,
      timestamp: new Date().toISOString()
    };
    
    socket.emit('chat_response', response);
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