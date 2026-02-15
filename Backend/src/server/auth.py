import os
import jwt
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import request, jsonify, current_app
import bcrypt


def verify_password(stored, provided):
    if not stored or not provided:
        return False
    try:
        if isinstance(stored, (bytes, bytearray)):
            return bcrypt.checkpw(provided.encode('utf-8'), stored)
        if isinstance(stored, str):
            try:
                return bcrypt.checkpw(provided.encode('utf-8'), stored.encode('utf-8'))
            except Exception:
                import hashlib
                return hashlib.sha256(provided.encode('utf-8')).hexdigest() == stored
    except Exception:
        return False
    return False


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('ev_token')
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        try:
            secret = current_app.config.get('SECRET_KEY')
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def make_token_for_user(user_dict, hours=2):
    secret = current_app.config.get('SECRET_KEY')
    payload = {
        'username': user_dict.get('username'),
        'role': user_dict.get('role', 'viewer'),
        'assigned_cameras': user_dict.get('assigned_cameras', [])
    }
    exp = datetime.now(timezone.utc) + timedelta(hours=hours)
    payload['exp'] = exp
    token = jwt.encode(payload, secret, algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token
