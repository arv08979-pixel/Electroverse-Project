from flask import Blueprint, request, jsonify, current_app, Response
from bson.objectid import ObjectId
from src.server.auth import token_required
from src.encryption import decryption as decryption_mod
import os

bp = Blueprint('videos', __name__)


def get_fs():
    return current_app.config['FS']


@bp.route('/video/<video_id>')
@token_required
def stream_video(video_id):
    try:
        fs = get_fs()
        video_file = fs.get(ObjectId(video_id))
        metadata = getattr(video_file, 'metadata', {}) or {}
        cam_id = metadata.get('camera_id')
        user_payload = request.user
        if user_payload.get('role') != 'admin' and cam_id not in user_payload.get('assigned_cameras', []):
            return jsonify({"error": "Not authorized to view this camera's video"}), 403

        def generate():
            for chunk in video_file:
                yield chunk

        return Response(generate(), mimetype='application/octet-stream')
    except Exception:
        return jsonify({"error": "Video not found"}), 404


@bp.route('/video/decrypted/<video_id>')
@token_required
def stream_decrypted(video_id):
    try:
        fs = get_fs()
        video_file = fs.get(ObjectId(video_id))
        metadata = getattr(video_file, 'metadata', {}) or {}
        cam_id = metadata.get('camera_id')
        user_payload = request.user
        if user_payload.get('role') != 'admin' and cam_id not in user_payload.get('assigned_cameras', []):
            return jsonify({"error": "Not authorized to view this camera's video"}), 403

        blob = video_file.read()
        key = decryption_mod.load_key()
        tmp_mp4 = decryption_mod.decrypt_blob_to_path(blob, key)
        if not tmp_mp4 or not os.path.exists(tmp_mp4):
            return jsonify({"error": "Decryption failed"}), 500

        def generate_file():
            try:
                with open(tmp_mp4, 'rb') as f:
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        yield chunk
            finally:
                try:
                    os.remove(tmp_mp4)
                except Exception:
                    pass

        return Response(generate_file(), mimetype='video/mp4')
    except Exception:
        return jsonify({"error": "Video not found"}), 404


@bp.route('/search')
@token_required
def search_videos():
    plate = request.args.get('plate')
    date_str = request.args.get('date') # YYYY-MM-DD
    camera_id = request.args.get('camera_id')
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')

    query = {}
    if plate:
        query['metadata.plate_numbers'] = plate
    if camera_id:
        query['metadata.camera_id'] = camera_id

    if date_str:
        try:
            from datetime import datetime, timedelta
            base_date = datetime.strptime(date_str, '%Y-%m-%d')
            if start_time_str and end_time_str:
                t_start = datetime.strptime(start_time_str, '%H:%M:%S').time()
                t_end = datetime.strptime(end_time_str, '%H:%M:%S').time()
                ist_start = datetime.combine(base_date, t_start)
                ist_end = datetime.combine(base_date, t_end)
            else:
                ist_start = base_date
                ist_end = ist_start + timedelta(days=1)
            utc_start = ist_start - timedelta(hours=5, minutes=30)
            utc_end = ist_end - timedelta(hours=5, minutes=30)
            query['uploadDate'] = {'$gte': utc_start, '$lt': utc_end}
        except ValueError:
            return jsonify({'error': 'Invalid format. Use Date: YYYY-MM-DD, Time: HH:MM:SS'}), 400

    db = current_app.config['DB']
    cursor = db.fs.files.find(query)
    results = []
    from datetime import timedelta
    for video in cursor:
        utc_time = video['uploadDate']
        ist_time = utc_time + timedelta(hours=5, minutes=30)
        results.append({
            'video_id': str(video['_id']),
            'filename': video['filename'],
            'camera_id': video.get('metadata', {}).get('camera_id'),
            'upload_date_ist': ist_time.strftime('%Y-%m-%d %H:%M:%S'),
            'plates_found': video.get('metadata', {}).get('plate_numbers', [])
        })
    if not results:
        return jsonify({'message': 'No results found'}), 404
    return jsonify(results), 200


@token_required
def update_plate(video_id):
    token = request.cookies.get('ev_token')
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    try:
        payload = request.user
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401
    user = current_app.config['DB'].users.find_one({'username': payload.get('username')})
    if not user or user.get('role') not in ['uploader', 'admin']:
        return jsonify({'error': 'No permission to update metadata'}), 403
    data = request.get_json() or {}
    plate_numbers = data.get('plate_numbers')
    if not plate_numbers:
        return jsonify({'error': 'No plate number provided'}), 400
    result = current_app.config['DB'].fs.files.update_one({'_id': ObjectId(video_id)}, {'$push': {'metadata.plate_numbers': plate_numbers}})
    if result.matched_count == 0:
        return jsonify({'error': 'Video not found'}), 404
    return jsonify({'message': 'Plate added to metadata'}), 200
