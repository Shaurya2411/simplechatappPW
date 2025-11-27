# Real-Time Chat Application

A production-ready real-time chat application built with Flask and Flask-SocketIO, featuring WebSocket communication for instant messaging.

## Features

✨ **Core Features:**
- Create chat rooms with unique 6-character room IDs
- Join existing rooms using room IDs
- Real-time bidirectional messaging
- User presence tracking (online users list)
- System notifications for user join/leave events
- Message history preservation during session
- Username validation and duplicate prevention
- Responsive design for mobile and desktop

🔒 **Production-Ready:**
- Comprehensive error handling
- Input validation and sanitization
- XSS prevention
- Graceful disconnect handling
- Room cleanup for empty rooms
- Loading states and user feedback

## Project Structure

```
chat-app/
├── app.py                 # Flask backend with SocketIO
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html        # Home page (create/join room)
│   └── chat.html         # Chat room page
└── README.md             # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or create the project directory:**
```bash
mkdir chat-app
cd chat-app
```

2. **Create the required files:**
   - Copy `app.py` to the root directory
   - Create a `templates` folder
   - Copy `index.html` and `chat.html` to the `templates` folder
   - Copy `requirements.txt` to the root directory

3. **Create a virtual environment (recommended):**
```bash
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Set environment variables (optional but recommended for production):**
```bash
# On Windows:
set SECRET_KEY=your-secret-key-here

# On macOS/Linux:
export SECRET_KEY=your-secret-key-here
```

## Running the Application

1. **Start the Flask server:**
```bash
python app.py
```

2. **Access the application:**
   - Open your web browser
   - Navigate to: `http://localhost:5000`

3. **Using the application:**
   - Enter a username on the home page
   - Click "Create New Room" to create a new chat room
   - Share the room ID with others
   - Others can join by entering the room ID on the home page

## Usage Guide

### Creating a Room
1. Enter your username
2. Click "Create New Room"
3. You'll be redirected to the chat page
4. Share the room ID (displayed at the top) with others

### Joining a Room
1. Enter your username
2. Enter the 6-character room ID
3. Click "Join"
4. You'll enter the chat room with other users

### Chat Features
- Type messages in the input field
- Press Enter or click "Send" to send messages
- See all active users in the sidebar
- View message history from when you joined
- Click the room ID to copy it to clipboard
- Click "Leave Room" to exit

## Technical Details

### Backend (Flask + SocketIO)

**Key Components:**
- `Flask`: Web framework for serving pages and handling routes
- `Flask-SocketIO`: WebSocket support for real-time communication
- In-memory storage for rooms and messages (session-based)

**SocketIO Events:**
- `connect`: Client connection established
- `disconnect`: Client disconnection and cleanup
- `create_room`: Generate new room with unique ID
- `join_room`: Add user to existing room
- `leave_room`: Remove user from room
- `send_message`: Broadcast message to room

**Data Structures:**
```python
active_rooms = {
    'ROOM_ID': {
        'users': {socket_id: username},
        'messages': [message_objects]
    }
}
```

### Frontend (HTML + JavaScript + CSS)

**Technologies:**
- Socket.IO client library for WebSocket connections
- Vanilla JavaScript (no framework dependencies)
- Responsive CSS with mobile-first design
- LocalStorage for username persistence

**Key Features:**
- Real-time message updates
- Auto-scroll to latest messages
- Message type indicators (own/others/system)
- User avatar generation
- Toast notifications
- Mobile-responsive sidebar

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for session management (default: 'your-secret-key-change-in-production')

### Customization Options

**Change Port:**
```python
# In app.py, line ~280
socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

**Room ID Length:**
```python
# In app.py, line ~21
return str(uuid.uuid4())[:6].upper()  # Change [:6] to desired length
```

**Message Limits:**
```javascript
// In index.html, line ~128
maxlength="20"  // Username max length

// In chat.html, add to textarea
maxlength="500"  // Message max length
```

## Production Deployment

### Security Considerations
1. **Set a strong SECRET_KEY:**
   ```bash
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   ```

2. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:5000
   ```

3. **Enable HTTPS:**
   - Use a reverse proxy (Nginx, Apache)
   - Obtain SSL certificate (Let's Encrypt)

4. **Additional security headers:**
   Add to app.py:
   ```python
   @app.after_request
   def set_security_headers(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       return response
   ```

### Scaling Considerations
- For production, consider using Redis for session storage
- Implement message persistence with a database (MongoDB, PostgreSQL)
- Use a message queue for handling high loads
- Deploy behind a load balancer for horizontal scaling

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Change the port in app.py or kill the process
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:5000 | xargs kill -9
```

**Socket connection fails:**
- Check firewall settings
- Ensure the server is running
- Verify the correct URL is being used
- Check browser console for errors

**Messages not appearing:**
- Verify WebSocket connection in browser dev tools
- Check server logs for errors
- Ensure both users are in the same room

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Opera: ✅ Full support
- IE11: ❌ Not supported (WebSocket required)

## Future Enhancements

Potential features to add:
- [ ] User authentication and accounts
- [ ] Private messaging
- [ ] File/image sharing
- [ ] Message reactions and emojis
- [ ] Typing indicators
- [ ] Read receipts
- [ ] Message search
- [ ] Room passwords
- [ ] Admin/moderator roles
- [ ] Database persistence
- [ ] Message encryption

## License

This project is open source and available for educational and commercial use.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs in the console
3. Check browser developer console for client-side errors

---

**Happy Chatting! 💬**