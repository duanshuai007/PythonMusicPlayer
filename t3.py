from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QDateTime, QUrl#, QSize

def a():
    app = QApplication([])
    player = QMediaPlayer()
    wgt_video = QVideoWidget()
    wgt_video.show()
    player.setVideoOutput(wgt_video)
    #file = QFileDialog.getOpenFileUrl()[0]
    #print(file)
    #content = QMediaContent(file)
    content = QMediaContent(QUrl.fromLocalFile("I:/迅雷下载/极品收藏/2048论坛@fun2048.com -JUL-225.mp4"))
    player.setMedia(content)
    player.play()
    app.exec_()
    
a()