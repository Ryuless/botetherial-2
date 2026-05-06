import json
import db

# Initialize database
db.init('config.json')

print("=== DATABASE STATUS ===")
print(f"Using Firestore: {db._use_firestore}")
print(f"Sessions collection available: {db._sessions_col is not None}")
print()

# Get all sessions from fallback (in-memory) storage
print("=== IN-MEMORY FALLBACK SESSIONS ===")
all_sessions = db._fallback_sessions
print(f"Total sessions in memory: {len(all_sessions)}")
if all_sessions:
    created_users = {}
    for user_id, session_data in all_sessions.items():
        if session_data.get('created', False):
            created_users[user_id] = {
                'username': session_data.get('title', 'Unknown'),
                'race': session_data.get('race', 'Unknown'),
                'job': session_data.get('job', 'Unknown'),
                'level': session_data.get('level', 1),
                'location': session_data.get('location', 'Unknown'),
                'created': session_data.get('created', False),
                'gold': session_data.get('gold', 0),
                'hp': f"{session_data.get('hp', 0)}/{session_data.get('max_hp', 100)}",
                'sp': f"{session_data.get('sp', 0)}/{session_data.get('max_sp', 50)}",
            }
    print(json.dumps(created_users, indent=2) if created_users else "No users with created characters")
else:
    print("No sessions in memory")

# If Firestore is enabled, try to fetch from there
if db._use_firestore and db._sessions_col is not None:
    print("\n=== FIRESTORE SESSIONS ===")
    try:
        docs = db._sessions_col.stream()
        firestore_users = {}
        for doc in docs:
            data = doc.to_dict()
            if data.get('created', False):
                firestore_users[doc.id] = {
                    'username': data.get('title', 'Unknown'),
                    'race': data.get('race', 'Unknown'),
                    'job': data.get('job', 'Unknown'),
                    'level': data.get('level', 1),
                    'location': data.get('location', 'Unknown'),
                    'created': data.get('created', False),
                    'gold': data.get('gold', 0),
                    'hp': f"{data.get('hp', 0)}/{data.get('max_hp', 100)}",
                    'sp': f"{data.get('sp', 0)}/{data.get('max_sp', 50)}",
                }
        print(f"Total created users in Firestore: {len(firestore_users)}")
        print(json.dumps(firestore_users, indent=2) if firestore_users else "No users with created characters")
    except Exception as e:
        print(f"Error fetching from Firestore: {e}")
