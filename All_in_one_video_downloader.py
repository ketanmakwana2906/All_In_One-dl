import sys
import requests
import yt_dlp
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5 import QtGui

class DownloadThread(QThread):
    progress_update = pyqtSignal(int)
    download_complete = pyqtSignal()

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
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
        self.progress_bar.setFixedSize(700, 25)
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
        self.download_thread.download_complete.connect(self.show_download_complete_alert)
        self.download_thread.start()

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
