from flask import Flask, request, jsonify, render_template
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import yt_dlp
import os
import re
app = Flask(__name__)

# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = './myprojects-443514-7601ad8db15e.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

def make_file_public(file_id):
    """Make a Google Drive file publicly accessible."""
    try:
        drive_service.permissions().create(
            fileId=file_id,
            body={
                'type': 'anyone',  # Allow anyone to access the file
                'role': 'reader',  # Give read-only access
            },
        ).execute()
        print(f"File {file_id} is now public.")
    except Exception as e:
        print(f"Failed to make file public: {e}")
        raise e

def upload_to_google_drive(file_path, file_name):
    """Upload file to Google Drive and make it public."""
    mime_type = 'video/mp4'  # Default MIME type for MP4 files.
    
    if file_name.endswith('.webm'):
        mime_type = 'video/webm'  # Adjust MIME type for .webm files
    elif file_name.endswith('.mp3'):
        mime_type = 'audio/mp3'  # Adjust MIME type for .mp3 files
    
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, mimetype=mime_type)

    # Upload the file to Google Drive
    uploaded_file = drive_service.files().create(
        body=file_metadata, media_body=media, fields='id').execute()
    file_id = uploaded_file.get('id')
    print(f"Uploading file {file_name} with MIME type {mime_type}")

    # Make the file public
    make_file_public(file_id)
    
    return file_id



def sanitize_filename(name):
    """Sanitize a string to make it safe for use as a file name."""
    return re.sub(r'[\\/*?:"<>|]', '_', name)


def download_youtube_video(url, format_type="mp4"):
    """Download YouTube video or audio using yt_dlp and save it on filesystem."""
    output_dir = "audios" if format_type.lower() == "mp3" else "videos"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, '%(title)s.%(ext)s')

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if format_type.lower() == 'mp4' else 'bestaudio/best',
        'outtmpl': file_path,
        'merge_output_format': format_type,
    }

    if format_type.lower() == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        ydl_opts['postprocessor_args'] = ['-vn']
        ydl_opts['prefer_ffmpeg'] = True

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)

        # Ensure correct extension for MP3
        if format_type.lower() == 'mp3' and not downloaded_file.endswith('.mp3'):
            downloaded_file = downloaded_file.rsplit('.', 1)[0] + '.mp3'

        print(f"Downloaded File: {downloaded_file}")

        if not os.path.exists(downloaded_file):
            return None, "File not found after download."

        return downloaded_file, None
    except Exception as e:
        return None, str(e)



@app.route('/')
def home():
    """Render the HTML front-end."""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_youtube_video():
    try:
        # Get YouTube URL and desired format
        data = request.json
        youtube_url = data.get('url')
        format_type = data.get('format', 'mp4')  # Default to mp4
        print(format_type)
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400

        # Download YouTube video or audio
        file_path, error = download_youtube_video(youtube_url, format_type)
        if error:
            return jsonify({'error': error}), 500

        # Extract the file name from the path
        file_name = os.path.basename(file_path)

        # Upload the file to Google Drive
        file_id = upload_to_google_drive(file_path, file_name)
        
        # Clean up the local file after upload
        os.remove(file_path)

        # Generate the download link
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        return jsonify({'download_url': download_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
