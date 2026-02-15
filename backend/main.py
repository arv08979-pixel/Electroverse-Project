import threading
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime
import csv
import shutil
from src.encryption.keyGeneration import load_key

load_key()  # Ensure key is generated at startup
 

ROOT = Path(__file__).resolve().parent

# Configurable via env
DATA_DIR = Path(os.environ.get('EV_DATA_DIR', ROOT / 'data'))
RAW_DIR = DATA_DIR / 'raw_buffer'
LOGS_DIR = RAW_DIR / 'logs'
CV_OUT = DATA_DIR / 'cv2.mp4'
PLATE_CSV = LOGS_DIR / 'plate_log.csv'
CAMERA_ID = os.environ.get('EV_CAMERA_ID', 'CAM_01')

def record_thread(stop_event):
    # Run the recorder (blocks) in this thread
    from src.record import record
    try:
        record()
    except Exception as e:
        print('record_thread error:', e)


def cv_thread(stop_event):
    # Watch for new motion recordings (motion_*.mp4 / .avi) and run plates_detect
    import subprocess
    RAW_GLOB = ['motion_*.mp4', 'motion_*.avi']
    while not stop_event.is_set():
        found = []
        for pat in RAW_GLOB:
            found.extend(list(ROOT.glob(pat)))
        if found:
            found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            video = found[0]
            try:
                # run plates_detect as a module; ensure working dir is backend
                subprocess.run(
                    ['python', '-m', 'src.plates_detect.plates_detect', '--video', str(video)],
                    cwd=str(ROOT), check=False
                )
                # plates_detect writes data/cv2.mp4 and CSV logs under cwd
                # move produced cv2.mp4 into DATA_DIR (it already writes to data/cv2.mp4)
                produced = ROOT / 'data' / 'cv2.mp4'
                if produced.exists():
                    shutil.move(str(produced), str(CV_OUT))
                # keep or remove original raw file
                try:
                    video.unlink()
                except Exception:
                    pass
            except Exception as e:
                print('cv_thread error:', e)

        time.sleep(int(os.environ.get('EV_CV_POLL', 5)))


def encryption_thread(stop_event):
    from src.encryption import encryption
    from pymongo import MongoClient
    from gridfs import GridFS

    client = MongoClient(os.environ.get('EV_MONGO'))
    db = client.video_storage_db
    fs = GridFS(db)
    key = encryption.load_key()

    while not stop_event.is_set():
        if CV_OUT.exists():
            try:
                # Create container and append encrypted chunk
                container_path = encryption.create_new_container()
                blob = encryption.encrypt_chunk_blob(str(CV_OUT), key)
                with open(container_path, 'ab') as f:
                    f.write(blob)

                # read plates from CSV if available
                plates = []
                if PLATE_CSV.exists():
                    try:
                        with open(PLATE_CSV, newline='') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                # try common fields
                                if 'plate' in row:
                                    plates.append(row['plate'])
                                elif 'plate_path' in row:
                                    plates.append(Path(row['plate_path']).name)
                    except Exception:
                        pass

                # store container into GridFS with metadata
                with open(container_path, 'rb') as f:
                    container_bytes = f.read()
                    fs.put(container_bytes, filename=os.path.basename(container_path), content_type='application/octet-stream', metadata={'camera_id': CAMERA_ID, 'plate_numbers': plates, 'is_encrypted': True, 'container_format': 'WattLagGyi'})

                # cleanup
                try:
                    CV_OUT.unlink()
                except Exception:
                    pass
                try:
                    if PLATE_CSV.exists():
                        PLATE_CSV.unlink()
                except Exception:
                    pass
                try:
                    if Path(container_path).exists():
                        Path(container_path).unlink()
                except Exception:
                    pass
            except Exception as e:
                print('encryption_thread error:', e)

        time.sleep(int(os.environ.get('EV_ENC_POLL', 3)))


def server_thread(stop_event):
    # Run Flask server in-process (no reloader) for RPi friendliness
    from src.server.server import create_app
    app = create_app()
    # run in this thread (blocking) but stop_event will not stop Flask; use process supervisor for production
    ssl_ctx = app.config.get('SSL_CONTEXT')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False, use_reloader=False, ssl_context=ssl_ctx)


def main():
    stop_event = threading.Event()

    threads = [
        threading.Thread(target=record_thread, args=(stop_event,), daemon=True),
        threading.Thread(target=cv_thread, args=(stop_event,), daemon=True),
        threading.Thread(target=encryption_thread, args=(stop_event,), daemon=True),
        threading.Thread(target=server_thread, args=(stop_event,), daemon=True),
    ]

    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Stopping...')
        stop_event.set()


if __name__ == '__main__':
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    main()
