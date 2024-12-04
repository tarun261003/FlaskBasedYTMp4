from googleapiclient.discovery import build
from google.oauth2 import service_account

# Set up Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = './myprojects-443514-7601ad8db15e.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=credentials)

def list_and_delete_files():
    try:
        # List files in the Google Drive
        results = drive_service.files().list(
            pageSize=1000,  # You can adjust the number as needed
            fields="nextPageToken, files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print('No files found.')
        else:
            # Loop through the files and delete them
            for file in files:
                file_id = file['id']
                file_name = file['name']
                print(f"Deleting file: {file_name} (ID: {file_id})")
                drive_service.files().delete(fileId=file_id).execute()
            print("All files deleted successfully.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        print(file_name)

if __name__ == '__main__':
    list_and_delete_files()
