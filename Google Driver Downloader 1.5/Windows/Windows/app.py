import gradio as gr
import requests
from tkinter import filedialog, messagebox
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow


import os
import pickle
import re
import sys
import webbrowser
from tkinter import Tk
import time
import shutil



# Function to browse for download directory
download_folder_path = ""  # Global variable to store the path
status_messages = []
exclude_str = ""
drive_service = None

def initialize_uploader():
    global drive_service
    download_instance = DownloadFromDrive()
    drive_service = download_instance.get_user_credential()
    
    if drive_service is None:
        raise ValueError("Dịch vụ Google Drive không khả dụng. Vui lòng kiểm tra lại file ggdownload.json/ggupload.json hoặc các file *_token.pickle.")

def check_json_files():
    
    download_file = "ggdownload.json"
    upload_file = "ggupload.json"
    missing_files = []
    
    # Kiểm tra sự tồn tại của `ggdownload.json`
    if not os.path.exists(download_file):
        if os.path.exists(upload_file):
            # Sao chép `ggupload.json` thành `ggdownload.json`
            shutil.copy(upload_file, download_file)
            print(f"Tự động sao chép {upload_file} thành {download_file}.")
        else:
            missing_files.append(download_file)
    
    # Kiểm tra sự tồn tại của `ggupload.json`
    if not os.path.exists(upload_file):
        if os.path.exists(download_file):
            
            shutil.copy(download_file, upload_file)
            print(f"Tự động sao chép {download_file} thành {upload_file}. Bạn sẽ download và upload cùng 1 tài khoản Google Drive !")
        else:
            missing_files.append(upload_file)
    
    # Nếu cả hai tệp đều thiếu, đưa ra thông báo lỗi
    if missing_files:
        missing_files_str = "\n- ".join(missing_files)
        raise FileNotFoundError(
            "\n============================\n"
            "THÔNG BÁO LỖI\n"
            "============================\n"
            "Không tìm thấy các tệp cấu hình cần thiết:\n"
            f"- {missing_files_str}\n\n"
            "Vui lòng sao chép các tệp vào thư mục hiện tại và thử lại.\n"
            "============================"
        )



def delete_api_keys():
    
    files_to_delete = ["upload_token.pickle", "download_token.pickle"]
    deleted_files = []
    for file_name in files_to_delete:
        if os.path.exists(file_name):
            os.remove(file_name)
            deleted_files.append(file_name)

    if deleted_files:
        gr.Info("Đã xóa thành công các tệp API Key !!!", visible=True, duration=2)
        return f"Đã xóa thành công các tệp API Key !!!"
    else:
        gr.Info("Không tìm thấy các tệp API Key để xóa.", visible=True, duration=2)
        return "Không tìm thấy các tệp API Key để xóa."
    
def validate_folder_link(drive_service, folder_link):
    if not isinstance(folder_link, str) or not folder_link.strip():
        return False, "Liên kết thư mục không hợp lệ hoặc để trống. Vui lòng nhập lại liên kết."

    folder_id = extract_folder_id_from_url(folder_link)
    if folder_id is None:
        return False, "Liên kết không hợp lệ. Vui lòng kiểm tra lại."

    try:
        # Kiểm tra thư mục bằng cách lấy metadata của nó
        folder = drive_service.files().get(fileId=folder_id, fields="id, name", supportsAllDrives=True).execute()
        return True, f"Thư mục đích '{folder.get('name')}' đã được xác minh."
    except HttpError as e:
        # Xử lý nếu thư mục không tồn tại hoặc không có quyền truy cập
        if e.resp.status == 404:
            return False, "Thư mục không tồn tại. Vui lòng kiểm tra lại liên kết."
        elif e.resp.status == 403:
            return False, "Bạn không có quyền truy cập vào thư mục này. Vui lòng yêu cầu quyền truy cập."
        else:
            return False, f"Lỗi không xác định: {e}"



def validate_inputs(shared_drive_links, folder_path):
    
    if not shared_drive_links.strip():
        gr.Info("Vui lòng nhập link Google Drive!", visible=True, duration=2)
        return False, "Vui lòng nhập link Google Drive ở trên !"

    
    if not folder_path or folder_path == "No folder selected.":
        gr.Info("Vui lòng chọn thư mục tải về!", visible=True, duration=2)
        return False, "Vui lòng chọn thư mục tải về ở trên !"
    
    return True, ""

def browse_files():
    #global selected_file_path
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()  
    selected_file_paths = filedialog.askopenfilenames()  
    root.destroy()
    
    if selected_file_paths:
        return [os.path.normpath(path) for path in selected_file_paths]  
    else:
        gr.Info("Vui lòng chọn các tệp để tải lên!", visible=True, duration=2)
        return None  



def browse_directory():
    global download_folder_path
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()  
    download_folder_path = filedialog.askdirectory()  
    root.destroy()
    if download_folder_path:
        return f"{download_folder_path}"
    gr.Info("Vui lòng chọn thư mục tải về!", visible=True, duration=2)
    return "No folder selected."

def open_output_folder():
    global download_folder_path
    if download_folder_path and os.path.exists(download_folder_path):
        webbrowser.open(download_folder_path)
    else:
        gr.Info("Chưa chọn thư mục tải về. Vui lòng chọn lại!", visible=True, duration=2)
        messagebox.showerror("Lỗi", "Chưa chọn thư mục tải về. Vui lòng chọn lại !!!")

# Function to validate and check Google Drive URLs
def validate_url(url):
    drive_url_pattern = r"(https?://drive\.google\.com/.*)"
    print(f"Check URL : {url} !")

    # Kiểm tra URL có đúng định dạng Google Drive không
    if not re.match(drive_url_pattern, url):
        
        return False, f"link {url} ---> không phải Google Drive, vui lòng kiểm tra lại!"
    
    # Kiểm tra URL có bị khóa (private) hoặc lỗi 404 không
    try:
        response = requests.get(url)
        if 'ServiceLogin' in response.url:
            
            return False, f"link {url} ---> đã bị khóa, vui lòng liên hệ người chia sẻ để cấp quyền truy cập cho bạn!"
        elif response.status_code == 404:
            
            return False, f"link {url} ---> sai định dạng của Google Drive, vui lòng kiểm tra lại!"
    except requests.RequestException as e:
        return False, f"Không thể kiểm tra URL {url}, lỗi: {str(e)}"
    
    return True, " ---> đã tải thành công !!!"




def load_client_info(json_path='credentials.json'):
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        client_id = data["installed"]["client_id"]
        client_secret = data["installed"]["client_secret"]
    return client_id, client_secret

class UploadToDrive:
    def __init__(self, client_id=None, client_secret=None):
        """Khởi tạo và xác thực với Google Drive API, lưu token vào `upload_token.pickle`."""
        self.service = None
        check_json_files()

        
        if client_id and client_secret:
            self.authenticate_manually(client_id, client_secret)
        else:
            self.service = self.get_user_credential()

          

    def get_user_credential(self):
        """Lấy token từ `upload_token.pickle` nếu tồn tại, hoặc xác thực lại."""
        creds = None
        if os.path.exists('upload_token.pickle'):
            with open('upload_token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'ggupload.json', ['https://www.googleapis.com/auth/drive']
                )
                creds = flow.run_local_server(port=0)

            # Lưu token vào upload_token.pickle
            with open('upload_token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        # Trả về dịch vụ Google Drive
        return build('drive', 'v3', credentials=creds)

    def authenticate_manually(self, client_id, client_secret):
        
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=['https://www.googleapis.com/auth/drive']
        )

        creds = flow.run_local_server(port=0)

        # Lưu token mới vào upload_token.pickle
        with open('upload_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)
        

    def extract_folder_id_from_url(self, url):
        """Trích xuất ID thư mục từ URL và kiểm tra quyền truy cập."""
        pattern = r'[-\w]{25,}'
        match = re.search(pattern, url)
        if match:
            folder_id = match.group(0)
            try:
                # Kiểm tra quyền truy cập vào thư mục
                self.service.files().get(fileId=folder_id, supportsAllDrives=True).execute()
                return folder_id
            except HttpError:
                print(f"Lỗi: Không thể truy cập thư mục với ID {folder_id}. Kiểm tra quyền và URL.")
                return None
        else:
            print("Lỗi: Định dạng URL không hợp lệ.")
            return None

    def upload_file(self, file_path, parent_folder_id=None):
        
        file_name = os.path.basename(file_path)
        file_metadata = {'name': file_name}
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        uploaded_file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = uploaded_file.get('id')
        link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        message = f"File '{file_name}' đã được tải lên thành công!\nVui lòng xem kết quả tại đây: {link}"
        print(message)
        return message

    def upload_folder(self, folder_path, parent_folder_id=None):
        
        folder_name = os.path.basename(folder_path)
        folder_id = self.create_folder(folder_name, parent_folder_id)
        
        # Duyệt qua cấu trúc thư mục và tải lên mà không trả về thông báo cho từng tệp
        for root, _, files in os.walk(folder_path):
            relative_path = os.path.relpath(root, folder_path)
            current_folder_id = folder_id

            # Tạo các thư mục con trên Google Drive
            if relative_path != '.':
                current_folder_id = self.create_folder(relative_path, folder_id)

            # Tải lên các tệp trong thư mục hiện tại mà không in thông báo từng tệp
            for file_name in files:
                file_path = os.path.join(root, file_name)
                self.upload_file(file_path, current_folder_id)

        # Trả về thông báo thành công cho thư mục chính
        folder_link = f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"
        message = f"Thư mục '{folder_name}' đã được tải lên thành công!\nVui lòng xem kết quả tại đây: {folder_link}"
        print(message)
        return message



    def create_folder(self, folder_name, parent_folder_id=None):
        """Tạo một thư mục trên Google Drive."""
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]

        folder = self.service.files().create(body=file_metadata, fields='id').execute()
        print(f"Thư mục '{folder_name}' đã được tạo với ID: {folder.get('id')}")
        return folder.get('id')
    
class DownloadFromDrive:
    def __init__(self, client_id=None, client_secret=None):
        check_json_files()
        self._total_size = 0
        self._limit_size = 0
        self.excluded_strings = [ext.strip() for ext in exclude_str.split(",") if ext.strip()]
        self.service = None
        
        if client_id and client_secret:
            self.authenticate_manually(client_id, client_secret)
        else:
            self.service = self.get_user_credential()

        
        

    def get_user_credential(self):
        """Lấy token từ `download_token.pickle` nếu tồn tại, hoặc xác thực lại."""
        creds = None
        if os.path.exists('download_token.pickle'):
            with open('download_token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'ggdownload.json', ['https://www.googleapis.com/auth/drive']
                )
                creds = flow.run_local_server(port=0)

            # Lưu token vào upload_token.pickle
            with open('download_token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        # Trả về dịch vụ Google Drive
        return build('drive', 'v3', credentials=creds)

    def authenticate_manually(self, client_id, client_secret):
        
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=['https://www.googleapis.com/auth/drive']
        )

        creds = flow.run_local_server(port=0)

        # Lưu token mới vào upload_token.pickle
        with open('download_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)
        

    
     
    def get_childs_from_folder(self, drive_service, folder_id, dest_folder):
        query = f"'{folder_id}' in parents and trashed = false"
        if self.excluded_strings:
            query += " and " + " and ".join([f"not name contains '{ext}'" for ext in self.excluded_strings])

        page_token = None
        while True:
            response = drive_service.files().list(q=query, orderBy='name, createdTime',
                                                fields='files(id, name, mimeType, size), nextPageToken',
                                                pageToken=page_token, supportsAllDrives=True,
                                                includeItemsFromAllDrives=True).execute()
            for file in response.get('files', []):
                # Kiểm tra nếu file là thư mục, thì tạo thư mục tương ứng và đệ quy vào bên trong
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    # Tạo thư mục con tương ứng
                    subfolder_path = os.path.join(dest_folder, file['name'])
                    os.makedirs(subfolder_path, exist_ok=True)
                    # Đệ quy để tải các file bên trong thư mục con
                    self.get_childs_from_folder(drive_service, file['id'], subfolder_path)
                else:
                    # Tải file vào thư mục hiện tại
                    self.copy_file(drive_service, dest_folder, file)

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break



    def copy_file(self, drive_service, dest_folder, source_file):
        if source_file['mimeType'] != 'application/vnd.google-apps.folder':
            file_name = source_file['name']
            download_path = os.path.join(dest_folder, file_name)
            
            if not os.path.exists(download_path):
                try:
                    request = drive_service.files().get_media(fileId=source_file['id'])
                    with open(download_path, 'wb') as f:
                        downloader = MediaIoBaseDownload(f, request)
                        done = False
                        self._total_size = 0  
                        start_time = time.time()  

                        while not done:
                            status, done = downloader.next_chunk()
                            self._total_size += status.resumable_progress  
                            print(f"Tải {file_name}: {int(status.progress() * 100)}%")
                        
                        end_time = time.time()  
                        
                        # Tính toán tốc độ tải
                        size_mb = self._total_size / (1024 * 1024)  # Kích thước tính theo MB
                        speed_mb = size_mb / (end_time - start_time)  # Tốc độ tính theo MB/s
                        print(f"Xong {file_name}. Kích thước {size_mb:0.2f} MB. Thời gian {int(end_time - start_time)} giây. Tốc độ {speed_mb:0.2f} MB/s")

                except HttpError as e:
                    print(f"An error occurred: {e}")
            else:
                print(f"{file_name} đã tồn tại trong {dest_folder}. Bỏ qua.")

    def extract_folder_id_from_url(self, url):
        pattern = r'[-\w]{25,}'
        match = re.search(pattern, url)
        if match:
            return match.group(0)
        return None

    def download_from_drive(self, shared_drive_urls, dest_folder):
        service = self.get_user_credential()  # Lấy quyền truy cập vào Google Drive API
        status_messages = []  
        
        
        for drive_url in shared_drive_urls:
            source_folder_id = self.extract_folder_id_from_url(drive_url)
            if source_folder_id:
                try:
                    
                    source_folder = service.files().get(fileId=source_folder_id, supportsAllDrives=True).execute()

                    if source_folder['mimeType'] == 'application/vnd.google-apps.folder':
                        
                        root_folder_path = os.path.join(dest_folder, source_folder['name'])
                        os.makedirs(root_folder_path, exist_ok=True)

                        
                        self.get_childs_from_folder(service, source_folder_id, root_folder_path)

                        
                        status_messages.append(f"link {drive_url} ---> đã tải thành công!")
                    else:
                        
                        self.copy_file(service, dest_folder, source_folder)
                        
                        status_messages.append(f"link {drive_url} ---> đã tải thành công!")

                except HttpError as e:
                    # Xử lý lỗi khi không tìm thấy file hoặc folder, hoặc bị khóa quyền truy cập
                    if "notFound" in str(e):
                        status_messages.append(f"link {drive_url} ---> bị lỗi khi truy cập, vui lòng kiểm tra lại.")
                    elif "permission" in str(e):
                        status_messages.append(f"link {drive_url} ---> bị khóa bởi người dùng, bạn nên yêu cầu người ta cấp quyền truy cập cho bạn.")
                    else:
                        status_messages.append(f"Đã xảy ra lỗi với link {drive_url}: {str(e)}")
            else:
                # Nếu không phải là link Google Drive hợp lệ
                status_messages.append(f"link {drive_url}---> không phải link google drive, vui lòng kiểm tra lại!")

        # Trả về các thông báo đã thu thập
        return "\n".join(status_messages) if status_messages else gr.Info("Đã tải xong ! Vui lòng bấm nút [ Output folder ] để xem kết quả.", visible=True, duration=2)



def start_download(shared_drive_links, max_size):
    global download_folder_path
    global status_messages
    status_messages = []  

    
    shared_drive_links = [link.strip() for link in shared_drive_links.replace("\n", ",").split(",") if link.strip()]
    
    
    seen_links = set()
    
    
    downloader = DownloadFromDrive()
    downloader._limit_size = float(max_size)
    
    
    for link in shared_drive_links:
        
        if link in seen_links:
            status_messages.append(f"link {link} ---> đã được xử lý trước đó!")
            continue

        seen_links.add(link)  
        
        
        valid, message = validate_url(link)
        if not valid:
            status_messages.append(message)  # Nếu không hợp lệ, thêm thông báo lỗi
        else:
            
            download_result = downloader.download_from_drive([link], download_folder_path)
            status_messages.append(download_result)  
    
    
    return "\n".join(status_messages)



def start_download_with_validation(shared_drive_links, max_size, folder_path):
        # Kiểm tra đầu vào
        is_valid, validation_message = validate_inputs(shared_drive_links, folder_path)
        if not is_valid:
            return validation_message  
        
        # Nếu hợp lệ, tiếp tục tải xuống
        return start_download(shared_drive_links, max_size)

def open_output_folder_with_validation(folder_path):
        # Kiểm tra xem người dùng đã chọn thư mục tải về chưa
        if not folder_path or folder_path == "No folder selected.":
            return "Vui lòng chọn thư mục tải về!"
        
        # Nếu hợp lệ, mở thư mục đã chọn
        open_output_folder()
        return "Thư mục tải về đã được mở!"


def check_and_extract_folder_id(destination_folder_link):
    uploader = UploadToDrive()  # Khởi tạo dịch vụ
    folder_id = uploader.extract_folder_id_from_url(destination_folder_link)
    if folder_id:
        return f"Thư mục hợp lệ, ID: {folder_id}"
    return "Liên kết thư mục không hợp lệ hoặc không có quyền truy cập."

def upload_files_to_drive(destination_folder_link):
    
    uploader = UploadToDrive()
    folder_id = uploader.extract_folder_id_from_url(destination_folder_link)
    
    if not folder_id:
        return "Liên kết thư mục không hợp lệ hoặc không có quyền truy cập. Vui lòng kiểm tra lại URL."
    
    file_paths = browse_files()  
    if not file_paths:
        return "Không có tệp nào được chọn."

    if len(file_paths) > 99:
        return "Vui lòng chọn tối đa 99 tệp để tải lên."

    
    

    
    for file_path in file_paths:
        uploader.upload_file(file_path, folder_id)

    
    folder_link = f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"
    return f"Tất cả các tệp đã được tải lên thành công vào thư mục đích!\nVui lòng xem kết quả tại đây: {folder_link}"

def upload_folder_to_drive(destination_folder_link):
    uploader = UploadToDrive()
    folder_id = uploader.extract_folder_id_from_url(destination_folder_link)

    # Kiểm tra nếu URL không hợp lệ hoặc không có quyền truy cập
    if not folder_id:
        return "Liên kết thư mục không hợp lệ hoặc không có quyền truy cập. Vui lòng kiểm tra lại URL."

    # Nếu URL hợp lệ, mở hộp thoại để chọn thư mục
    folder_path = browse_directory()  
    if folder_path == "No folder selected.":
        return "Không có thư mục nào được chọn."

    # Tiến hành upload thư mục
    return uploader.upload_folder(folder_path, folder_id)



    


initialize_uploader()

# Gradio Interface
with gr.Blocks(title="Google Drive Upload/Download - Andy 0908231181") as demo:
    gr.HTML("<h1><center>🦟 Donation Momo/zalo pay/VNpay: 0908231181 🦟 </center></h1>")
    gr.HTML("<h1><center>1. Tải file/folder từ Google Drive bất kì về máy tính (Windows/Mac OS) </center></h1>") 
    
    shared_drive_links = gr.Textbox(label="Nhập các dòng link Google Drive: ", placeholder="Tối đa 10 link thôi nha !", lines=2)
    
    
    with gr.Row():
        with gr.Column(scale=8):
            folder_path = gr.Textbox(label="Chọn thư mục tải về", interactive=False, visible=True)
        with gr.Column(scale=1):
            browse_button = gr.Button("Duyệt thư mục")
            output_folder_button = gr.Button("Mở thư mục tải về")

    with gr.Row():
        with gr.Column(scale=8): download_button = gr.Button("Tải xuống", variant="primary")  
        with gr.Column(scale=2): max_size = gr.Textbox(label="Dung lượng tải tối đa (GB)", value="700", placeholder="Nhập tổng dung lượng tối đa (Gb) tải về") 
        with gr.Column(scale=2): delete_button = gr.Button("Xóa API Key")
          
    
    output_message = gr.Textbox(label="Trạng thái Tải về", lines=3)

    gr.HTML("<h1><center>2. Tải file/folder lên Google Drive của bạn </center></h1>") 

    destination_folder_link = gr.Textbox(label="Link thư mục Google Drive đích:", placeholder="Nhập link thư mục Google Drive đích")

    with gr.Row():
        with gr.Column(scale=5): upload_file_button = gr.Button("Tải tệp lên")
        with gr.Column(scale=5):upload_folder_button = gr.Button("Tải thư mục lên")
    
    output_upload_message = gr.Textbox(label="Trạng thái Tải lên", lines=2)

    
    upload_file_button.click(fn=upload_files_to_drive, inputs=destination_folder_link, outputs=output_upload_message)
    upload_folder_button.click(fn=upload_folder_to_drive, inputs=destination_folder_link, outputs=output_upload_message)
    delete_button.click(fn=delete_api_keys, outputs=output_message, show_progress=False)
    
    
    
    
    

    # Browse folder when button is clicked
    browse_button.click(fn=browse_directory, inputs=[], outputs=folder_path, show_progress=False)
    
    # Start download
    download_button.click(start_download_with_validation, [shared_drive_links, max_size, folder_path], output_message)
    
    # Open output folder
    output_folder_button.click(open_output_folder_with_validation, [folder_path], output_message, show_progress=False)

demo.launch(inbrowser=True, show_error=True)
