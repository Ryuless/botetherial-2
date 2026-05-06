import json
import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Firestore-backed persistence with in-memory fallback
_use_firestore = False
_sessions_col = None
_world_doc = None
_fallback_sessions: Dict[str, dict] = {}
_fallback_world_state: Dict[str, dict] = {}
_app_initialized = False


def init(config_path: str = None):
    """Initialize Firebase/Firestore client. If credentials are missing or
    initialization fails, fall back to in-memory storage.
    """
    global _use_firestore, _sessions_col, _world_doc, _app_initialized
    try:
        import firebase_admin
        from firebase_admin import credentials
        from firebase_admin import firestore
    except Exception as e:
        logger.error(f"Firebase Admin SDK not available: {e}")
        _use_firestore = False
        return

    service_account_path = None
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                service_account_path = cfg.get("firebase_service_account")
        except Exception as e:
            logger.error(f"Error reading config: {e}")
            service_account_path = None

    try:
        # Initialize app with credential if provided and exists
        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            # Check if app already initialized
            if not _app_initialized:
                try:
                    firebase_admin.initialize_app(cred)
                    _app_initialized = True
                except ValueError:
                    # App already initialized
                    _app_initialized = True
            logger.info(f"Firebase initialized with credentials from {service_account_path}")
        else:
            logger.warning(f"Firebase service account not found at {service_account_path}")
            _use_firestore = False
            return

        client = firestore.client()
        _sessions_col = client.collection("sessions")
        _world_doc = client.collection("meta").document("world_state")
        _use_firestore = True
        logger.info("Firestore connected successfully")
    except Exception as e:
        logger.error(f"Firestore initialization failed: {e}")
        _use_firestore = False


def get_session(user_id: str) -> dict:
    user_id = str(user_id)
    if _use_firestore and _sessions_col is not None:
        try:
            doc = _sessions_col.document(user_id).get()
            data = doc.to_dict() if doc.exists else {}
            if not isinstance(data, dict):
                data = {}
            logger.debug(f"Loaded session for user {user_id} from Firestore (exists={doc.exists})")
            return data
        except Exception as e:
            logger.error(f"Error loading session from Firestore for user {user_id}: {e}")
            # Fall back to in-memory
            return _fallback_sessions.get(user_id, {})
    
    # Fallback to in-memory storage
    logger.debug(f"Loading session for user {user_id} from in-memory storage (Firestore disabled)")
    return _fallback_sessions.get(user_id, {})


def save_session(user_id: str, session: dict):
    user_id = str(user_id)
    if not isinstance(session, dict):
        logger.error(f"Invalid session data type for user {user_id}: {type(session)}")
        return
    
    if _use_firestore and _sessions_col is not None:
        try:
            _sessions_col.document(user_id).set(session)
            logger.debug(f"Saved session for user {user_id} to Firestore")
            return
        except Exception as e:
            logger.error(f"Error saving session to Firestore for user {user_id}: {e}")
            # Fall back to in-memory
            _fallback_sessions[user_id] = session
            return
    
    # Fallback to in-memory storage
    logger.debug(f"Saving session for user {user_id} to in-memory storage (Firestore disabled)")
    _fallback_sessions[user_id] = session


def get_world_state() -> dict:
    if _use_firestore and _world_doc is not None:
        try:
            doc = _world_doc.get()
            data = doc.to_dict() if doc.exists else {}
            if not isinstance(data, dict):
                data = {}
            logger.debug(f"Loaded world state from Firestore (exists={doc.exists})")
            return data
        except Exception as e:
            logger.error(f"Error loading world state from Firestore: {e}")
            return _fallback_world_state.get("world", {})
    
    logger.debug("Loading world state from in-memory storage (Firestore disabled)")
    return _fallback_world_state.get("world", {})


def save_world_state(state: dict):
    if not isinstance(state, dict):
        logger.error(f"Invalid world state data type: {type(state)}")
        return
    
    if _use_firestore and _world_doc is not None:
        try:
            _world_doc.set(state)
            logger.debug("Saved world state to Firestore")
            return
        except Exception as e:
            logger.error(f"Error saving world state to Firestore: {e}")
            _fallback_world_state["world"] = state
            return
    
    logger.debug("Saving world state to in-memory storage (Firestore disabled)")
    _fallback_world_state["world"] = state


def is_firestore_enabled() -> bool:
    """Check if Firestore is properly initialized and enabled."""
    return _use_firestore and _sessions_col is not None and _world_doc is not None


def get_firestore_status() -> dict:
    """Get detailed status of Firestore connection."""
    return {
        "enabled": _use_firestore,
        "sessions_collection": _sessions_col is not None,
        "world_doc": _world_doc is not None,
        "app_initialized": _app_initialized,
        "fallback_sessions_count": len(_fallback_sessions),
        "fallback_world_state": bool(_fallback_world_state)
    }
