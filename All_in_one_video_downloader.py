import sys
import requests
import yt_dlp
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5 import QtGui
import os
import zipfile

class DownloadThread(QThread):
    progress_update = pyqtSignal(int)
    download_complete = pyqtSignal()
    operation_changed = pyqtSignal(str)

    def __init__(self, video_url, download_path, quality):
        super().__init__()
        self.video_url = video_url
        self.download_path = download_path
        self.quality = quality
        self.height = self.quality.strip('p');


    def run(self):
        ydl_opts = {
            'format': f'bestvideo[height={self.height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height={self.height}]+bestaudio',
            'outtmpl': f'{self.download_path}/%(title)s={self.height}p.mp4',
            'progress_hooks': [self.progress_hook],
            'ffmpeg_location': self.ffmpeg_path,
         }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            self.progress_update.emit(0)
            self.operation_changed.emit("Downloading Progress")
            ydl.download([self.video_url])
            self.download_complete.emit()
            self.progress_update.emit(0)


    def progress_hook(self, d):
        if d['status'] == 'finished':
         self.progress_update.emit(100)
        elif d['status'] == 'downloading':
            progress_str = d['_percent_str']
            progress_percent = int(float(progress_str[7:12]))
            self.progress_update.emit(progress_percent)

class RequirementDownloadThread(QThread):
    def run(self):
        user_home = os.path.expanduser('~')
        ffmpeg_exe_path = os.path.join(user_home, "ffmpeg", 'ffmpeg.exe')
        zip_location = os.path.join(user_home,'ffmpeg.zip')
        if not os.path.exists(ffmpeg_exe_path):
         ffmpeg_zip_url = 'https://github.com/ketanmakwana2906/ffmpeg/raw/main/ffmpeg.zip'
         response = requests.get(ffmpeg_zip_url, stream=True)
         total_size = int(response.headers.get('content-length', 0))
         bytes_so_far = 0
         if response.status_code == 200:
          with open(zip_location, 'wb') as f:
           for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    bytes_so_far += len(chunk)
                    progress_percent = int((bytes_so_far / total_size) * 100)
                    # self.progress_update.emit(progress_percent)
         with zipfile.ZipFile(zip_location, 'r') as zip_ref:
           exefolder_location = os.path.join(user_home,"ffmpeg")
           if not os.path.exists(exefolder_location):
             os.mkdir(exefolder_location)
           zip_ref.extractall(exefolder_location)
        self.ffmpeg_path = ffmpeg_exe_path
        if os.path.exists(zip_location):
             os.remove(zip_location)

class VideoDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('All in ONE video downloader')
        self.setFixedSize(900, 250)
        self.setStyleSheet("background-color: #defff4;")
        icon_url = "https://raw.githubusercontent.com/ketanmakwana2906/Project_Images_Storage/main/all_in_one/video-831.png"
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(requests.get(icon_url).content)
        self.setWindowIcon(QtGui.QIcon(pixmap))
        self.setup_ui()
    def setup_ui(self):
        user_home = os.path.expanduser('~')
        ffmpeg_exe_path = os.path.join(user_home, "ffmpeg", 'ffmpeg.exe')
        if os.path.exists(ffmpeg_exe_path):
            self.create_video_downloader_layout()
        else:
            self.create_requirement_download_layout()

    def create_video_downloader_layout(self):
         self.video_url_label = QLabel('Video URL:')
         self.video_url_input = QLineEdit()
         self.video_url_input.setFixedSize(700, self.video_url_input.sizeHint().height())
         self.video_url_input.textChanged.connect(self.update_quality_options)

         self.quality_label = QLabel('Select Quality:')
         self.quality_combo = QComboBox()
         self.quality_combo.setFixedSize(700, self.quality_combo.sizeHint().height())

         self.path_label = QLabel('Select Download Path:')
         self.path_display = QLineEdit()
         self.path_display.setFixedSize(515, self.path_display.sizeHint().height())
         self.browse_button = QPushButton('Browse')
         self.browse_button.setFixedSize(180, self.browse_button.sizeHint().height())
         self.browse_button.clicked.connect(self.select_download_path)

         self.download_button = QPushButton('Download')
         self.download_button.clicked.connect(self.download_video)

         self.progress_label = QLabel('Download Progress:')
         self.progress_bar = QProgressBar()
         self.progress_bar.setValue(0)
         self.progress_bar.setAlignment(Qt.AlignCenter)
         self.progress_label.hide()
         self.progress_bar.hide()

         url_layout = QHBoxLayout()
         url_layout.addWidget(self.video_url_label)
         url_layout.addWidget(self.video_url_input)

         quality_layout = QHBoxLayout()
         quality_layout.addWidget(self.quality_label)
         quality_layout.addWidget(self.quality_combo)

         path_layout = QHBoxLayout()
         path_layout.addWidget(self.path_label)
         path_layout.addWidget(self.path_display)
         path_layout.addWidget(self.browse_button)

         button_layout = QHBoxLayout()
         button_layout.addWidget(self.download_button)

         progress_layout = QHBoxLayout()
         progress_layout.addWidget(self.progress_label)
         progress_layout.addWidget(self.progress_bar)

         main_layout = QVBoxLayout()
         main_layout.addLayout(url_layout)
         main_layout.addLayout(quality_layout)
         main_layout.addLayout(path_layout)
         main_layout.addLayout(button_layout)
         main_layout.addLayout(progress_layout)
         self.setLayout(main_layout)

    def create_requirement_download_layout(self):
        self.welcome_label = QLabel('Welcome to the application')
        self.requirement_download_button = QPushButton('Download')
        self.requirement_download_button.clicked.connect(self.download_requirement)
        layout = QVBoxLayout()
        layout.addWidget(self.welcome_label)
        layout.addWidget(self.requirement_download_button)
        self.setLayout(layout)

    def refresh_layout(self):
        current_layout = self.layout()
        current_layout.setParent(None)
        self.create_video_downloader_layout()
        
    def download_requirement(self):
        self.requirement_download_thread = RequirementDownloadThread()
        self.requirement_download_thread.finished.connect(self.refresh_layout)
        self.requirement_download_thread.start()

    def select_download_path(self):
        download_path = QFileDialog.getExistingDirectory(self, 'Select Download Path')
        if download_path:
            self.path_display.setText(download_path)

    def update_quality_options(self):
        video_url = self.video_url_input.text()
        self.quality_combo.clear()
        self.quality_combo.addItem('Loading Available Qualities...')
        self.quality_combo.repaint()

        try:
            ydlp = yt_dlp.YoutubeDL({})
            info_dict = ydlp.extract_info(video_url, download=False)
            formats = info_dict.get('formats', [])

            quality_set = set()
            for format in formats:
                if format.get('height') and format.get('ext') == 'mp4':
                    quality_set.add(f"{format['height']}p")

            if not quality_set:
                raise ValueError("No quality options found.")
            
            quality_options = sorted(list(quality_set), key=lambda x: int(x.replace('p', '')))
            self.quality_combo.clear()
            self.quality_combo.addItems(quality_options)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            QMessageBox.warning(self, "Error", "Enter valid url, cannot load qualities")

    def download_video(self):
        video_url = self.video_url_input.text()
        download_path = self.path_display.text()
        quality = self.quality_combo.currentText()

        if not video_url or not download_path:
            QMessageBox.warning(self, 'Error', 'Enter Video Url')
            return
        
        self.progress_label.show()
        self.progress_bar.show()

        self.download_thread = DownloadThread(video_url, download_path, quality)
        self.download_thread.progress_update.connect(self.update_progress)
        self.download_thread.operation_changed.connect(self.update_progress_label)
        self.download_thread.download_complete.connect(self.show_download_complete_alert)
        self.download_thread.start()

     
    def update_progress_label(self, text):
        self.progress_label.setText(text)

    def update_progress(self, progress_percent):
        self.progress_bar.setValue(progress_percent)

    def show_download_complete_alert(self):
     QMessageBox.information(self, 'Download Complete', 'Video downloaded successfully!')
     self.progress_label.hide()
     self.progress_bar.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    downloader = VideoDownloader()
    downloader.show()
    sys.exit(app.exec_())
