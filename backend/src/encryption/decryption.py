import os
import json
import cv2
import tempfile
from datetime import datetime
from Crypto.Cipher import AES


ENC_FOLDER = os.environ.get("EV_ENC_FOLDER") or os.path.join(os.path.dirname(__file__), "data", "encrypted")
OUTPUT_FOLDER = os.environ.get("EV_DEC_OUT") or os.path.join(os.path.dirname(__file__), "data", "decrypted")
KEY_PATH = os.environ.get("EV_KEY_PATH") or os.path.join(os.path.dirname(__file__), "configs", "secret.key")


def load_key():
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(f"Key not found: {KEY_PATH}")
    with open(KEY_PATH, "rb") as f:
        return f.read()


def read_safe(f, size):
    data = f.read(size)
    if len(data) != size:
        return None
    return data


def decrypt_chunk(f, key):

    header_len_bytes = read_safe(f, 4)
    if not header_len_bytes:
        return None

    chunk_header_len = int.from_bytes(
        header_len_bytes,
        "big"
    )

    header_bytes = read_safe(f, chunk_header_len)
    if not header_bytes:
        return None

    chunk_header = json.loads(
        header_bytes.decode()
    )

    nonce = read_safe(f, 16)
    tag = read_safe(f, 16)

    if not nonce or not tag:
        return None

    file_size = chunk_header["file_size"]

    ciphertext = read_safe(f, file_size)
    if not ciphertext:
        return None

    try:
        cipher = AES.new(
            key,
            AES.MODE_EAX,
            nonce=nonce
        )

        plaintext = cipher.decrypt_and_verify(
            ciphertext,
            tag
        )

        return plaintext

    except:
        return None


def extract_video_props(video_bytes):

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    ) as tmp:
        tmp.write(video_bytes)
        temp_path = tmp.name

    cap = cv2.VideoCapture(temp_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    valid = fps > 0 and width > 0 and height > 0

    cap.release()
    os.remove(temp_path)

    return valid, fps, width, height


def append_video(writer, video_bytes):

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    ) as tmp:
        tmp.write(video_bytes)
        temp_path = tmp.name

    cap = cv2.VideoCapture(temp_path)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        writer.write(frame)

    cap.release()
    os.remove(temp_path)


def decrypt_container(path, key):

    name = os.path.basename(path)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_path = os.path.join(
        OUTPUT_FOLDER,
        name.replace(".WattLagGyi", ".mp4")
    )

    writer = None

    with open(path, "rb") as f:

        header_len_bytes = read_safe(f, 4)
        if not header_len_bytes:
            return

        header_len = int.from_bytes(
            header_len_bytes,
            "big"
        )

        if not read_safe(f, header_len):
            return

        while True:

            chunk_bytes = decrypt_chunk(f, key)

            if not chunk_bytes:
                break

            if writer is None:

                valid, fps, w, h = extract_video_props(
                    chunk_bytes
                )

                if not valid:
                    continue

                fourcc = cv2.VideoWriter_fourcc(*"mp4v")

                writer = cv2.VideoWriter(
                    output_path,
                    fourcc,
                    fps,
                    (w, h)
                )

            append_video(writer, chunk_bytes)

    if writer:
        writer.release()
        print(f"Decrypted → {name}")
    else:
        print(f"No valid video → {name}")


def process_all():

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    key = load_key()

    containers = sorted([
        f for f in os.listdir(ENC_FOLDER)
        if f.lower().endswith("wattlaggyi")
    ])

    for file in containers:
        decrypt_container(
            os.path.join(ENC_FOLDER, file),
            key
        )


def decrypt_blob_to_path(blob_bytes, key):
    """Attempt to decrypt a blob that may be either:
    - a simple AES-EAX blob (nonce[16] + tag[16] + ciphertext)
    - or a container format produced by the original encrypt script
    Returns path to temporary .mp4 file or None on failure.
    """
    from io import BytesIO

    b = BytesIO(blob_bytes)

    # Try simple format first
    try:
        b.seek(0)
        # read first 16 + 16
        nonce = b.read(16)
        tag = b.read(16)
        ciphertext = b.read()
        if len(nonce) == 16 and len(tag) == 16 and len(ciphertext) > 0:
            cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)

            # Write plaintext to temp mp4 and return path
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp.write(plaintext)
            tmp.flush()
            tmp.close()
            return tmp.name
    except Exception:
        pass

    # Fallback: try container parsing using existing logic
    try:
        # write temp container with the expected container suffix so decrypt_container
        # will generate an output filename with .mp4
        tmp_container = tempfile.NamedTemporaryFile(delete=False, suffix='.WattLagGyi')
        tmp_container.write(blob_bytes)
        tmp_container.flush()
        tmp_container.close()

        # ensure output dir exists
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        # reuse decrypt_container logic by writing container to a temp file and running decrypt_container
        decrypt_container(tmp_container.name, key)

        # The decrypt_container writes to OUTPUT_FOLDER; find produced mp4
        base = os.path.basename(tmp_container.name)
        expected = base.replace('.WattLagGyi', '.mp4')
        out_path = os.path.join(OUTPUT_FOLDER, expected)
        if os.path.exists(out_path):
            return out_path
    except Exception:
        pass

    return None


if __name__ == "__main__":
    process_all()
