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
const MCP_SERVER_URL = 'http://localhost:8080';
app.use((0, helmet_1.default)());
app.use((0, compression_1.default)());
app.use((0, cors_1.default)());
app.use(express_1.default.json());
app.use(express_1.default.static(path_1.default.join(__dirname, '../public')));
app.get('/', (req, res) => {
    res.sendFile(path_1.default.join(__dirname, '../public/index.html'));
});
async function callMCPServer(prompt) {
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
                    limit: 10,
                    min_confidence: 0.5
                }
            })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data.result || data;
    }
    catch (error) {
        console.error('Error calling MCP server:', error);
        return null;
    }
}
io.on('connection', (socket) => {
    console.log('User connected:', socket.id);
    socket.on('chat_message', async (data) => {
        console.log('Received message:', data);
        const mcpResult = await callMCPServer(data.content);
        console.log('MCP server result:', mcpResult);
        const response = {
            id: Date.now().toString(),
            type: 'ai',
            content: `I found ${mcpResult?.servers?.length || 0} MCP servers related to your query: "${data.content}". Check the knowledge graph pane for details.`,
            timestamp: new Date().toISOString()
        };
        socket.emit('chat_response', response);
        if (mcpResult && mcpResult.servers) {
            console.log('Sending MCP servers to client:', mcpResult.servers.length, 'servers');
            socket.emit('mcp_servers_result', {
                servers: mcpResult.servers,
                total_found: mcpResult.total_found,
                search_metadata: mcpResult.search_metadata
            });
        }
        else {
            console.log('No MCP servers to send to client');
        }
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