"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const http_1 = require("http");
const socket_io_1 = require("socket.io");
const cors_1 = __importDefault(require("cors"));
const helmet_1 = __importDefault(require("helmet"));
const compression_1 = __importDefault(require("compression"));
const path_1 = __importDefault(require("path"));
const app = (0, express_1.default)();
const server = (0, http_1.createServer)(app);
const io = new socket_io_1.Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});
app.use((0, helmet_1.default)());
app.use((0, compression_1.default)());
app.use((0, cors_1.default)());
app.use(express_1.default.json());
app.use(express_1.default.static(path_1.default.join(__dirname, '../public')));
app.get('/', (req, res) => {
    res.sendFile(path_1.default.join(__dirname, '../public/index.html'));
});
io.on('connection', (socket) => {
    console.log('User connected:', socket.id);
    socket.on('chat_message', (data) => {
        console.log('Received message:', data);
        const response = {
            id: Date.now().toString(),
            type: 'ai',
            content: `I received your message: "${data.content}". This is a placeholder response from the askg AI agent.`,
            timestamp: new Date().toISOString()
        };
        socket.emit('chat_response', response);
    });
    socket.on('new_chat', () => {
        console.log('New chat requested');
        socket.emit('chat_cleared');
    });
    socket.on('save_chat', (chatData) => {
        console.log('Chat save requested:', chatData);
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
//# sourceMappingURL=index.js.map