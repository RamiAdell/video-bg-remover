from datetime import datetime, timedelta
import secrets
from flask import Flask, request, jsonify, send_file, send_from_directory
import os
import subprocess
import threading
import time
import math
from pydub.utils import mediainfo
from utils.video_utils import remove_background_from_video
from config import Config

app = Flask(__name__)

progress = 0
progress_lock = threading.Lock()


app.config['SIGNED_URL_EXPIRY'] = 3600  # 1 hour expiry for signed URLs
app.config['SIGNED_URL_EXPIRY'] = 3600  # 1 hour expiry for signed URLs
app.secret_key = secrets.token_hex(16)  # Secret key for signing URLs

def generate_signed_url(type,filename, expiry=None):
    """
    Generate a signed URL for a file.
    """
    if expiry is None:
        expiry = app.config['SIGNED_URL_EXPIRY']
    expiration_time = datetime.utcnow() + timedelta(seconds=expiry)
    token = secrets.token_urlsafe(32)  # Generate a secure token
    signed_url = f"/download_video?type={type}&filename={filename}&token={token}&expires={expiration_time.timestamp()}"
    return signed_url

@app.route('/get_token')
def hi():
    return "test"

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' in request.files:
        file = request.files['audio']
    elif 'file' in request.files:
        file = request.files['file']
    else:
        return jsonify({'error': 'No file provided'}), 400

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    user_id = request.form.get('user_id', 'unknown')
    original_filename = file.filename
    filename = f"{user_id}_{original_filename}"
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)

    try:
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(file_path)
        
        print(f"File uploaded: {filename}")
        return jsonify({'filename': filename}), 200

    except Exception as e:
        return jsonify({'error': f"File upload failed: {str(e)}"}), 500


@app.route('/process', methods=['POST'])
def process():
    global progress
    progress = 0

    user_id = request.form.get('user_id', 'unknown')
    filename = request.form.get('filename')
    if not filename:
        return jsonify({'error': 'Filename not provided'}), 400

    print(f"Processing file: {filename}")

    input_video_path = os.path.join(Config.UPLOAD_FOLDER, filename).replace("\\", "/")
    intermediate_output_path = os.path.join(Config.UPLOAD_FOLDER, f"intermediate_{filename}").replace("\\", "/")
    final_output_path = os.path.join(Config.PROCESSED_FOLDER, f"final_{filename}").replace("\\", "/")
    info = mediainfo(input_video_path)  # Get metadata
    duration = float(info.get("duration", 0))  # Extract duration safely
    dur = math.ceil(duration)

    def progress_callback(p):
        global progress
        with progress_lock:
            progress = p
        print(f"Progress: {progress}%")

    # Run background removal
    
    remove_background_from_video(input_video_path, intermediate_output_path, progress_callback)

    try:
        if os.path.exists(final_output_path):
            os.remove(final_output_path)
        subprocess.run([
            "ffmpeg", "-i", intermediate_output_path,
            "-vcodec", "libx264",
            "-acodec", "aac",
            final_output_path
        ], check=True)
        print(f"Final video saved: {final_output_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error processing video: {e}")
        return jsonify({'error': 'Video processing failed'}), 500

    p = os.path.join(Config.UPLOAD_FOLDER, filename)
    print(p)
    signed_url = generate_signed_url("intermediate",f"intermediate_{filename}")
    v_signed_url=generate_signed_url("final",f"final_{filename}")
    return jsonify({
        'view-video':'https://www.nexmediaai.com/video-bg-processing'+v_signed_url,
        'signed_url':'https://www.nexmediaai.com/video-bg-processing'+signed_url,
        'duration': dur,
        'processed_file_url': 'https://www.nexmediaai.com/video-bg-processing'+v_signed_url,
        'processed_filename': filename,
        'sucess':True,
    }), 200


@app.route('/download_video', methods=['GET'])
def download_video():
    try:
        filename = request.args.get('filename')
        token = request.args.get('token')
        expires = request.args.get('expires')
        type = request.args.get('type')

        if not filename or not token or not expires:
            return jsonify({'error': 'Invalid URL'}), 400

        # Check if the URL has expired
        expiration_time = datetime.fromtimestamp(float(expires))
        if datetime.utcnow() > expiration_time:
            return jsonify({'error': 'URL has expired'}), 403

        # Construct the path to the processed video
        if type == "final":
            p = Config.PROCESSED_FOLDER
         
        else :
            
            p = Config.UPLOAD_FOLDER
        # Check if the video exists
        if not os.path.exists(os.path.join(p, filename)):
            return jsonify({'error': 'Video not found'}), 404

        # Send the video file as an attachment
       
        return send_from_directory(p, filename, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=1565, host="0.0.0.0")
