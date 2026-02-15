from flask import Blueprint, request, jsonify, current_app
from src.server.user import find_by_email, find_by_username, create_user
from src.server.auth import verify_password, make_token_for_user

bp = Blueprint('users', __name__)


@bp.route('/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    identifier = data.get('email') or data.get('username')
    password = data.get('password')
    if not identifier or not password:
        return jsonify({'error': 'email/username and password required'}), 400

    user = find_by_email(identifier) or find_by_username(identifier)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not verify_password(user.get('password'), password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = make_token_for_user(user)
    resp = jsonify({'username': user['username'], 'role': user.get('role', 'viewer')})
    secure_flag = current_app.config.get('SECURE_COOKIES', False)
    resp.set_cookie('ev_token', token, httponly=True, secure=secure_flag, samesite='Lax', max_age=7200)
    return resp, 200


@bp.route('/me')
def me():
    token = request.cookies.get('ev_token')
    if not token:
        return jsonify({"authenticated": False}), 200
    try:
        import jwt
        payload = jwt.decode(token, current_app.config.get('SECRET_KEY'), algorithms=["HS256"])
        return jsonify({"authenticated": True, "user": payload}), 200
    except Exception:
        return jsonify({"authenticated": False}), 200


@bp.route('/auth/logout', methods=['POST'])
def auth_logout():
    # Clear the ev_token cookie
    resp = jsonify({'ok': True})
    secure_flag = current_app.config.get('SECURE_COOKIES', False)
    resp.set_cookie('ev_token', '', httponly=True, secure=secure_flag, samesite='Lax', max_age=0)
    return resp, 200


def admin_create_user():
    # simple admin endpoint to create users if needed (protect externally)
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'viewer')
    cameras = data.get('cameras', [])
    if not username or not email or not password:
        return jsonify({'error': 'username,email,password required'}), 400
    try:
        uid = create_user(username, email, password, role=role, cameras=cameras)
        return jsonify({'user_id': uid}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


