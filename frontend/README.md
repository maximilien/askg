# askg Chat Frontend

A modern TypeScript NodeJS-based chat interface for the askg AI agent.

## Features

- **Real-time Chat**: WebSocket-based real-time messaging with the askg AI agent
- **Responsive Design**: Modern UI with glassmorphism effects and smooth animations
- **Chat History**: Collapsible sidebar showing chat history (20% width)
- **Knowledge Graph**: Dedicated space for knowledge graph visualization (25% width)
- **Hamburger Menu**: Three-option menu with New Chat, Save Chat, and Settings
- **Auto-resizing Input**: Smart textarea that grows with content
- **Typing Indicators**: Visual feedback when the AI is responding
- **Message Formatting**: Basic markdown support (bold, italic, code)

## Layout

- **Header**: Contains hamburger menu and "askg AI Agent" title
- **Chat History Sidebar**: 20% width, collapsible, shows previous chats
- **Main Chat Area**: Middle section with conversation and input box
- **Knowledge Graph Sidebar**: 25% width, placeholder for graph visualization

## Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Build the Project**:
   ```bash
   npm run build
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```

4. **Start Production Server**:
   ```bash
   npm start
   ```

## Development

- **TypeScript**: Full TypeScript support with strict configuration
- **Hot Reload**: Use `npm run dev` for development with auto-restart
- **Linting**: Run `npm run lint` to check code quality
- **Formatting**: Run `npm run format` to format code with Prettier

## API Endpoints

The server provides the following WebSocket events:

### Client to Server
- `chat_message`: Send a message to the AI agent
- `new_chat`: Start a new chat session
- `save_chat`: Save the current chat

### Server to Client
- `chat_response`: Receive AI agent response
- `chat_cleared`: Notification that chat was cleared
- `chat_saved`: Confirmation of chat save operation

## File Structure

```
frontend/
├── src/
│   └── index.ts          # Main server file
├── public/
│   ├── index.html        # Main HTML file
│   ├── styles.css        # CSS styles
│   └── app.js           # Frontend JavaScript
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript configuration
└── README.md           # This file
```

## Customization

### Styling
- Modify `public/styles.css` to change the appearance
- The design uses CSS custom properties for easy theming
- Glassmorphism effects can be adjusted in the CSS

### Functionality
- Edit `public/app.js` to modify frontend behavior
- Modify `src/index.ts` to change server-side logic
- Add new WebSocket events as needed

## Browser Support

- Modern browsers with ES2020 support
- WebSocket support required
- CSS Grid and Flexbox support required

## Production Deployment

1. Build the project: `npm run build`
2. Start the server: `npm start`
3. The server will run on port 3200 by default
4. Set the `PORT` environment variable to change the port

## Integration with askg Backend

This frontend is designed to integrate with the askg Python backend. The WebSocket server currently provides placeholder responses, but can be extended to:

- Connect to the actual askg AI agent
- Query the Neo4j knowledge graph
- Display real-time knowledge graph visualizations
- Handle MCP server interactions

## License

MIT License - see the main project LICENSE file for details. 