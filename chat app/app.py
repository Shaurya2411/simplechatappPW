from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from datetime import datetime
import uuid
import os
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Initialize SocketIO with CORS support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', max_http_buffer_size=10 * 1024 * 1024)

# In-memory storage for rooms and users
active_rooms = {}  # {room_id: {'users': {sid: username}, 'messages': [], 'video_call': {'active': bool, 'participants': []}}}

# ==================== HELPER FUNCTIONS ====================

def generate_room_id():
    """Generate a unique 6-character room ID"""
    return str(uuid.uuid4())[:6].upper()

def get_timestamp():
    """Get current timestamp in readable format"""
    return datetime.now().strftime('%H:%M')

def add_system_message(room_id, message):
    """Add a system message to the room's message history"""
    if room_id in active_rooms:
        active_rooms[room_id]['messages'].append({
            'username': 'System',
            'message': message,
            'timestamp': get_timestamp(),
            'type': 'system'
        })

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    """Serve the home page"""
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Serve the chat page"""
    return render_template('chat.html')

# ==================== SOCKETIO EVENT HANDLERS ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection and cleanup"""
    user_rooms = [room for room in rooms() if room != request.sid]
    
    for room_id in user_rooms:
        if room_id in active_rooms:
            username = active_rooms[room_id]['users'].get(request.sid, 'Unknown User')
            
            # Remove user from video call if active
            if 'video_call' in active_rooms[room_id]:
                if request.sid in active_rooms[room_id]['video_call']['participants']:
                    active_rooms[room_id]['video_call']['participants'].remove(request.sid)
                    emit('user_left_call', {
                        'peer_id': request.sid,
                        'username': username
                    }, room=room_id)
            
            # Remove user from room
            if request.sid in active_rooms[room_id]['users']:
                del active_rooms[room_id]['users'][request.sid]
            
            # Add system message and notify other users
            add_system_message(room_id, f'{username} has left the room')
            emit('user_left', {
                'username': username,
                'timestamp': get_timestamp(),
                'users': list(active_rooms[room_id]['users'].values())
            }, room=room_id)
            
            # Clean up empty rooms
            if len(active_rooms[room_id]['users']) == 0:
                del active_rooms[room_id]
                print(f'Room {room_id} deleted (empty)')
    
    print(f'Client disconnected: {request.sid}')

@socketio.on('create_room')
def handle_create_room(data):
    """Create a new chat room with unique ID"""
    try:
        username = data.get('username', 'Anonymous')
        room_id = generate_room_id()
        
        # Ensure room ID is unique
        while room_id in active_rooms:
            room_id = generate_room_id()
        
        # Initialize room
        active_rooms[room_id] = {
            'users': {},
            'messages': [],
            'video_call': {
                'active': False,
                'participants': []
            }
        }
        
        emit('room_created', {'room_id': room_id})
        print(f'Room created: {room_id} by {username}')
        
    except Exception as e:
        emit('error', {'message': f'Failed to create room: {str(e)}'})
        print(f'Error creating room: {e}')

@socketio.on('join_room')
def handle_join_room(data):
    """Handle user joining a room"""
    try:
        room_id = data.get('room_id', '').strip().upper()
        username = data.get('username', 'Anonymous').strip()
        
        if not room_id:
            emit('error', {'message': 'Room ID is required'})
            return
        
        if not username:
            emit('error', {'message': 'Username is required'})
            return
        
        # Create room if it doesn't exist
        if room_id not in active_rooms:
            active_rooms[room_id] = {
                'users': {},
                'messages': [],
                'video_call': {
                    'active': False,
                    'participants': []
                }
            }
        
        # Check if username is already taken in this room
        existing_usernames = [u.lower() for u in active_rooms[room_id]['users'].values()]
        if username.lower() in existing_usernames:
            emit('error', {'message': 'Username already taken in this room'})
            return
        
        # Join the room
        join_room(room_id)
        active_rooms[room_id]['users'][request.sid] = username
        
        # Send room history to the new user
        emit('room_joined', {
            'room_id': room_id,
            'username': username,
            'messages': active_rooms[room_id]['messages'],
            'users': list(active_rooms[room_id]['users'].values()),
            'video_call_active': active_rooms[room_id]['video_call']['active']
        })
        
        # Notify other users
        add_system_message(room_id, f'{username} has joined the room')
        emit('user_joined', {
            'username': username,
            'timestamp': get_timestamp(),
            'users': list(active_rooms[room_id]['users'].values())
        }, room=room_id, skip_sid=request.sid)
        
        print(f'{username} joined room {room_id}')
        
    except Exception as e:
        emit('error', {'message': f'Failed to join room: {str(e)}'})
        print(f'Error joining room: {e}')

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle user leaving a room"""
    try:
        room_id = data.get('room_id', '').strip().upper()
        
        if room_id in active_rooms and request.sid in active_rooms[room_id]['users']:
            username = active_rooms[room_id]['users'][request.sid]
            
            # Remove from video call if active
            if request.sid in active_rooms[room_id]['video_call']['participants']:
                active_rooms[room_id]['video_call']['participants'].remove(request.sid)
                emit('user_left_call', {
                    'peer_id': request.sid,
                    'username': username
                }, room=room_id)
            
            # Remove user from room
            del active_rooms[room_id]['users'][request.sid]
            leave_room(room_id)
            
            # Notify other users
            add_system_message(room_id, f'{username} has left the room')
            emit('user_left', {
                'username': username,
                'timestamp': get_timestamp(),
                'users': list(active_rooms[room_id]['users'].values())
            }, room=room_id)
            
            # Clean up empty rooms
            if len(active_rooms[room_id]['users']) == 0:
                del active_rooms[room_id]
                print(f'Room {room_id} deleted (empty)')
            
            emit('left_room', {'room_id': room_id})
            print(f'{username} left room {room_id}')
        
    except Exception as e:
        emit('error', {'message': f'Failed to leave room: {str(e)}'})
        print(f'Error leaving room: {e}')

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a text message to a room"""
    try:
        room_id = data.get('room_id', '').strip().upper()
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return
        
        if room_id not in active_rooms or request.sid not in active_rooms[room_id]['users']:
            emit('error', {'message': 'You are not in this room'})
            return
        
        username = active_rooms[room_id]['users'][request.sid]
        timestamp = get_timestamp()
        
        # Create message object
        message_obj = {
            'username': username,
            'message': message_text,
            'timestamp': timestamp,
            'type': 'text',
            'sender_id': request.sid
        }
        
        # Store message in room history
        active_rooms[room_id]['messages'].append(message_obj)
        
        # Broadcast message to all users in the room
        emit('new_message', message_obj, room=room_id)
        print(f'Message from {username} in room {room_id}: {message_text}')
        
    except Exception as e:
        emit('error', {'message': f'Failed to send message: {str(e)}'})
        print(f'Error sending message: {e}')

@socketio.on('send_voice_note')
def handle_send_voice_note(data):
    """Handle sending a voice note to a room"""
    try:
        room_id = data.get('room_id', '').strip().upper()
        audio_data = data.get('audio_data')
        duration = data.get('duration', 0)
        
        if not audio_data:
            emit('error', {'message': 'No audio data received'})
            return
        
        if room_id not in active_rooms or request.sid not in active_rooms[room_id]['users']:
            emit('error', {'message': 'You are not in this room'})
            return
        
        # Validate audio data size (max 5MB for voice notes)
        audio_size = len(audio_data)
        if audio_size > 5 * 1024 * 1024:
            emit('error', {'message': 'Voice note too large (max 5MB)'})
            return
        
        username = active_rooms[room_id]['users'][request.sid]
        timestamp = get_timestamp()
        
        # Create voice note message object
        message_obj = {
            'username': username,
            'audio_data': audio_data,
            'duration': duration,
            'timestamp': timestamp,
            'type': 'voice',
            'sender_id': request.sid
        }
        
        # Store message in room history
        active_rooms[room_id]['messages'].append(message_obj)
        
        # Broadcast voice note to all users in the room
        emit('new_message', message_obj, room=room_id)
        print(f'Voice note from {username} in room {room_id} ({duration}s, {audio_size} bytes)')
        
    except Exception as e:
        emit('error', {'message': f'Failed to send voice note: {str(e)}'})
        print(f'Error sending voice note: {e}')

# ==================== VIDEO CALL HANDLERS ====================

@socketio.on('start_video_call')
def handle_start_video_call(data):
    """Handle starting a video call in the room"""
    try:
        room_id = data.get('room_id', '').strip().upper()
        
        if room_id not in active_rooms or request.sid not in active_rooms[room_id]['users']:
            emit('error', {'message': 'You are not in this room'})
            return
        
        username = active_rooms[room_id]['users'][request.sid]
        
        # Mark video call as active
        active_rooms[room_id]['video_call']['active'] = True
        active_rooms[room_id]['video_call']['participants'].append(request.sid)
        
        # Notify all users in the room
        add_system_message(room_id, f'{username} started a video call')
        emit('video_call_started', {
            'username': username,
            'peer_id': request.sid,
            'timestamp': get_timestamp()
        }, room=room_id)
        
        print(f'{username} started video call in room {room_id}')
        
    except Exception as e:
        emit('error', {'message': f'Failed to start video call: {str(e)}'})
        print(f'Error starting video call: {e}')

@socketio.on('join_video_call')
def handle_join_video_call(data):
    """Handle user joining the video call"""
    try:
        room_id = data.get('room_id', '').strip().upper()
        
        if room_id not in active_rooms or request.sid not in active_rooms[room_id]['users']:
            emit('error', {'message': 'You are not in this room'})
            return
        
        username = active_rooms[room_id]['users'][request.sid]
        
        # Add user to video call participants
        if request.sid not in active_rooms[room_id]['video_call']['participants']:
            active_rooms[room_id]['video_call']['participants'].append(request.sid)
        
        # Get all other participants
        other_participants = [
            {'peer_id': pid, 'username': active_rooms[room_id]['users'][pid]}
            for pid in active_rooms[room_id]['video_call']['participants']
            if pid != request.sid and pid in active_rooms[room_id]['users']
        ]
        
        # Send existing participants to the new user
        emit('existing_participants', {
            'participants': other_participants
        })
        
        # Notify others about the new participant
        emit('user_joined_call', {
            'peer_id': request.sid,
            'username': username
        }, room=room_id, skip_sid=request.sid)
        
        add_system_message(room_id, f'{username} joined the video call')
        emit('new_message', {
            'username': 'System',
            'message': f'{username} joined the video call',
            'timestamp': get_timestamp(),
            'type': 'system'
        }, room=room_id)
        
        print(f'{username} joined video call in room {room_id}')
        
    except Exception as e:
        emit('error', {'message': f'Failed to join video call: {str(e)}'})
        print(f'Error joining video call: {e}')

@socketio.on('leave_video_call')
def handle_leave_video_call(data):
    """Handle user leaving the video call"""
    try:
        room_id = data.get('room_id', '').strip().upper()
        
        if room_id not in active_rooms or request.sid not in active_rooms[room_id]['users']:
            return
        
        username = active_rooms[room_id]['users'][request.sid]
        
        # Remove from participants
        if request.sid in active_rooms[room_id]['video_call']['participants']:
            active_rooms[room_id]['video_call']['participants'].remove(request.sid)
        
        # If no participants left, deactivate call
        if len(active_rooms[room_id]['video_call']['participants']) == 0:
            active_rooms[room_id]['video_call']['active'] = False
            add_system_message(room_id, 'Video call ended')
            emit('video_call_ended', {}, room=room_id)
        
        # Notify others
        emit('user_left_call', {
            'peer_id': request.sid,
            'username': username
        }, room=room_id)
        
        add_system_message(room_id, f'{username} left the video call')
        emit('new_message', {
            'username': 'System',
            'message': f'{username} left the video call',
            'timestamp': get_timestamp(),
            'type': 'system'
        }, room=room_id)
        
        print(f'{username} left video call in room {room_id}')
        
    except Exception as e:
        emit('error', {'message': f'Failed to leave video call: {str(e)}'})
        print(f'Error leaving video call: {e}')

# WebRTC signaling handlers
@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Forward WebRTC offer to specific peer"""
    try:
        target_peer = data.get('target_peer')
        offer = data.get('offer')
        
        emit('webrtc_offer', {
            'offer': offer,
            'peer_id': request.sid
        }, room=target_peer)
        
    except Exception as e:
        print(f'Error forwarding offer: {e}')

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    """Forward WebRTC answer to specific peer"""
    try:
        target_peer = data.get('target_peer')
        answer = data.get('answer')
        
        emit('webrtc_answer', {
            'answer': answer,
            'peer_id': request.sid
        }, room=target_peer)
        
    except Exception as e:
        print(f'Error forwarding answer: {e}')

@socketio.on('webrtc_ice_candidate')
def handle_ice_candidate(data):
    """Forward ICE candidate to specific peer"""
    try:
        target_peer = data.get('target_peer')
        candidate = data.get('candidate')
        
        emit('webrtc_ice_candidate', {
            'candidate': candidate,
            'peer_id': request.sid
        }, room=target_peer)
        
    except Exception as e:
        print(f'Error forwarding ICE candidate: {e}')

# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    print('Starting Flask-SocketIO Chat Server...')
    print('Features: Text messages, Voice notes, Video calls')
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)