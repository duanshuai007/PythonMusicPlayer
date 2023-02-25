#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys
import logging
import queue
import threading
import time
import os
import json
import operator
import random
import copy
import re

from mutagen.mp4 import MP4

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMenu, QAction
from PyQt5.QtCore import Qt, QDateTime, QUrl, QSize
from PyQt5.QtMultimedia import *
#ui文件导入
from qt5player import Ui_qt5player
#自定义logger文件导入
from logger import LoggingProducer, LoggingConsumer
import config
from m4a_2_mp3 import *

LoggingConsumer()

'''
QMediaPlaylist: removeMedia(self, int)
'''

class Window(QtWidgets.QMainWindow, Ui_qt5player):

    __music_is_pause = False
    __button_pressed = False
    
    __PLAY_SHUNXU_MODE = 1
    __PLAY_RANDOM_MODE = 2
    __PLAY_SINGLE_MODE = 3
    __playmode = __PLAY_SHUNXU_MODE
    
    cm4a_list = []
    cm4a_playno = 0
    cm4a_inuse = False
    cm4a_flag = False
    cm4a_playlist_index = 0
    
    __playbtn_icon = "image/play.png"
    __prexbtn_icon = "image/prex.png"
    __nextbtn_icon = "image/next.png"
    __pausebtn_icon = "image/pause.png"
    __playmode_random_icon = "image/random_play.png"
    __playmode_single_icon = "image/single_play.png"
    __playmode_shunxu_icon = "image/shunxu_play.png"
    
    __curr_play_musicname = ""
    __curr_playlist_index = 0
    __cm4a_music_total_time = 0
    __slider_music_pressed = False
    
    def __init__(self):
        super(Window, self).__init__()
        self.setupUi(self)
        self.logger = LoggingProducer().getlogger()

        self.__playbtn_icon = config.resource_path(self.__playbtn_icon)
        self.__prexbtn_icon = config.resource_path(self.__prexbtn_icon)
        self.__nextbtn_icon = config.resource_path(self.__nextbtn_icon)
        self.__pausebtn_icon = config.resource_path(self.__pausebtn_icon)
        self.__playmode_random_icon = config.resource_path(self.__playmode_random_icon)
        self.__playmode_single_icon = config.resource_path(self.__playmode_single_icon)
        self.__playmode_shunxu_icon = config.resource_path(self.__playmode_shunxu_icon)
        
        self.player = QMediaPlayer()
        #self.player.setVideoOutput(self.videoout)
        self.player.positionChanged.connect(self.__PlayerChangeSlide)
        self.player.stateChanged.connect(self.__PlayerStateChange)
        self.playlist = QMediaPlaylist()
        #self.player.setPlaylist(self.playlist)
        self.config = config.Config()
        
        self.listWidget.itemDoubleClicked.connect(self.__PlayListItemDoubleClicked)
        self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested[QtCore.QPoint].connect(self.__PlayListItemRightClicked)
        #菜单动作:添加文件，添加目录，关于
        self.action_add_file.triggered.connect(self.__ActionAddVideoFile)
        self.action_add_dir.triggered.connect(self.__ActionAddVideoDir)
        self.action_adout.triggered.connect(self.__ActionAbout)
        #按钮:模式，上一首，播放/暂停，下一首 
        self.btn_playmode.clicked.connect(self.__ButtonPlayModeFunction)
        self.btn_prex.clicked.connect(self.__ButtonPlayPrexFunction)
        self.btn_play.clicked.connect(self.__ButtonPlayPlayFunction)
        self.btn_next.clicked.connect(self.__ButtonPlayNextFunction)
        
        #self.btn_playmode_icon = QtGui.QIcon("C:/Users/Administrator/git/PythonMusicPlayer/image/play.png")
        #self.btn_playmode.setIcon(self.btn_playmode_icon)
        #self.btn_playmode.setIconSize(QSize(30,30))
        #self.btn_play.setIcon(self.btn_playmode_icon)
        #self.btn_play.setIconSize(QSize(self.btn_play.width(), self.btn_play.height()))
        
        #显示音乐文件名称
        #self.label_musicplaytime.setStyleSheet("color:red")
        self.label_musicplaytime.setStyleSheet("background-color:red")
        self.label_musicplaytime.setAlignment(Qt.AlignCenter)
        self.label_musicplaytime.setText("MusicPlayTime")
        #self.label_musiccount
        #self.label_musiccount.setStyleSheet("color:red")
        self.label_musiccount.setStyleSheet("background-color:gray")
        self.label_musiccount.setAlignment(Qt.AlignCenter)
        self.label_musiccount.setText("MusicPlayCount")
        #self.label_musicname
        #self.label_musicname.setStyleSheet("color:red")
        self.label_musicname.setStyleSheet("background-color:green")
        self.label_musicname.setAlignment(Qt.AlignCenter)
        self.label_musicname.setText("MusicPlayName")
        #音乐播放时间条
        self.slider_music_playtime.setMinimum(0)
        self.slider_music_playtime.setMaximum(100)
        #self.slider_music_playtime.setSingleStep(1)
        self.slider_music_playtime.setValue(0)
        #self.slider_music_playtime.valueChanged.connect(self.__SlideMusicPlayTimeValueChange)
        self.slider_music_playtime.actionTriggered.connect(self.__SlideMusicPlayTimeValueTriggered)
        self.slider_music_playtime.sliderReleased.connect(self.__SlideMusicPlayTimeValueReleased)
        #音量条
        self.slider_music_volme.setMinimum(0)
        self.slider_music_volme.setMaximum(100)
        self.slider_music_volme.setSingleStep(1)
        self.slider_music_volme.setValue(int(self.config.get("VOLUME")))
        self.slider_music_volme.valueChanged.connect(self.__SlideMusicPlayVolumeValueChange)
        #self.slider_music_volme
        self.__playmode = int(self.config.get("MODE"))
        if self.__playmode == self.__PLAY_RANDOM_MODE:
            self.playlist.setPlaybackMode(QMediaPlaylist.Random)
        elif self.__playmode == self.__PLAY_SINGLE_MODE:
            self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        elif self.__playmode == self.__PLAY_SHUNXU_MODE:
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
            
        self.cm4a = ChangeM4AToMP3()
        r = config.get_file_from_config()
        for m in r:
            self.logger.info("add to playlist: {}".format(m))
            qurl = QUrl.fromLocalFile(m)
            content = QMediaContent(qurl)
            self.playlist.addMedia(content)
            n = os.path.basename(m)
            self.listWidget.addItem(n)
        
    #设置播放模式
    def __ButtonPlayModeFunction(self):
        #self.logger.info("__ButtonPlayModeFunction")
        _translate = QtCore.QCoreApplication.translate
        if self.__playmode == self.__PLAY_RANDOM_MODE:
            self.__playmode = self.__PLAY_SINGLE_MODE
            self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        elif self.__playmode == self.__PLAY_SINGLE_MODE:
            self.__playmode = self.__PLAY_SHUNXU_MODE
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        elif self.__playmode == self.__PLAY_SHUNXU_MODE:
            self.__playmode = self.__PLAY_RANDOM_MODE
            self.playlist.setPlaybackMode(QMediaPlaylist.Random)
        self.config.set("MODE", self.__playmode)
    #上一首
    def __ButtonPlayPrexFunction(self):
        self.logger.info("__ButtonPlayPrexFunction")
        self.__button_pressed = True
        if self.cm4a_flag is True:
            num = self.cm4a_playlist_index
        else:
            self.playlist.previous()
            num = self.playlist.currentIndex()
            if num == -1:
                num = self.playlist.mediaCount() - 1
        self.logger.info("prex:num={}".format(num))
        self.__player_play(num)
    #播放/暂停
    def __ButtonPlayPlayFunction(self):
        self.logger.info("__ButtonPlayPlayFunction")
        if self.playlist.currentIndex() == -1:
            if self.cm4a_inuse == False:
                self.__player_play(0)
                return
        if self.__music_is_pause is True:
            self.player.play()
            self.__music_is_pause = False
        else:
            self.player.pause()
            self.__music_is_pause = True
    #下一首
    def __ButtonPlayNextFunction(self):
        self.logger.info("__ButtonPlayNextFunction")
        self.__button_pressed = True
        if self.cm4a_flag is True:
            num = self.cm4a_playlist_index
        else:
            self.playlist.next()
            num = self.playlist.currentIndex()
            if num == -1:
                num = 0
        self.logger.info("next:num={}".format(num))
        self.__player_play(num)
        
    def __SlideMusicPlayTimeValueTriggered(self, v):
        self.logger.info("__SlideMusicPlayTimeValueTriggered:{} {}".format(v, self.slider_music_playtime.value()))
        self.__slider_music_pressed = True
        if self.cm4a_inuse is False:
            self.player.setPosition(self.slider_music_playtime.value()*1000)
    
    def __SlideMusicPlayTimeValueReleased(self):
        self.logger.info("__SlideMusicPlayTimeValueReleased:{}".format(self.slider_music_playtime.value()))
        if self.cm4a_inuse is True:
            self.__button_pressed = True
            s = self.slider_music_playtime.value()
            self.logger.info("------> s = {}".format(s))
            if s < self.cm4a.first_section_times:
                self.cm4a_playno = 0
                ss = s
            else:
                self.cm4a_playno = int((s - self.cm4a.first_section_times) / self.cm4a.section_times) + 1
                ss = (s - self.cm4a.first_section_times) % self.cm4a.section_times
                #ss = self.cm4a.first_section_times + ((self.cm4a_playno - 1) * self.cm4a.section_times)
            qurl = QUrl.fromLocalFile(self.cm4a_list[self.cm4a_playno])
            content = QMediaContent(qurl)
            self.player.stop()
            self.player.setMedia(content)
            self.player.play()
            self.player.setPosition(ss * 1000)
            self.logger.info("__SlideMusicPlayTimeValueReleased m4a:playno={} ss={}".format(self.cm4a_playno, ss))
        self.__slider_music_pressed = False
        
    def __SlideMusicPlayVolumeValueChange(self, v):
        #self.logger.info("__SlideMusicPlayVolumeValueChange:{}".format(self.slider_music_volme.value()))
        self.player.setVolume(v)
        self.config.set("VOLUME", str(v))
        
    def __ActionAddVideoFile(self):
        try:
            #urls = QFileDialog.getOpenFileUrl()[0]     #添加单个文件
            urls = QFileDialog.getOpenFileUrls(caption='添加音乐文件', filter='Playlist(*.mp3 *.wav *.m4a)')[0] #添加单个或多个文件  
            #urls = QFileDialog.getOpenFileName()[0]
            #urls = QFileDialog.getOpenFileNames(caption='添加音乐文件', filter='Playlist(*.mp3 *.wav *.m4a)')[0]
            #self.logger.info("__ActionAddVideoFile:{}".format(urls))
            if len(urls) >= 1:
                for url in urls:
                    s = url.toString()
                    if config.check_file_is_exists(s) is False:
                        config.save_file_to_config(s)
                        name = s.split('/')[-1]
                        self.logger.info("music name:{} url:{}".format(name, url))
                        content = QMediaContent(url)
                        self.playlist.addMedia(content)
                        self.listWidget.addItem(name)
        except Exception as e:
            self.logger.info("__ActionAddVideoFile err:{}".format(e))
    
    def __ActionAddVideoDir(self):
        try:
            dir = QFileDialog.getExistingDirectory(caption='添加目录')
            files = os.listdir(dir)
            for file in files:
                if file.endswith(".mp3") or file.endswith(".wav") or file.endswith(".m4a"):
                    file = "{}/{}".format(dir, file)
                    if config.check_file_is_exists(file) is False:
                        config.save_file_to_config(file)
                        name = file.split('/')[-1]
                        self.logger.info("add dir=>name:{} file:{}".format(name, file))
                        qurl = QUrl.fromLocalFile(file)
                        content = QMediaContent(qurl)
                        self.playlist.addMedia(content)
                        n = os.path.basename(file)
                        self.listWidget.addItem(n)
            #self.logger.info("dir:{} files:{}".format(dir, files))
        except Exception as e:
            self.logger.info("__ActionAddVideoDir err:{}".format(e))

    def __ActionAbout(self):
        self.logger.info("__ActionAbout")
    
    def __PlayerChangeSlide(self, v):
        try:
            self.logger.info("__PlayerChangeSlide: v={}".format(int(v/1000)))
            v = int(v / 1000)
            if self.cm4a_inuse is False:
                a = int(self.player.duration() / 1000)
            else:
                a = self.__cm4a_music_total_time
                if self.cm4a_playno >= 1:
                    v += self.cm4a.first_section_times + (self.cm4a.section_times * (self.cm4a_playno - 1))
            d = QDateTime.fromSecsSinceEpoch(v).toString("mm:ss")
            t = QDateTime.fromSecsSinceEpoch(a).toString("mm:ss")
            self.logger.info("__PlayerChangeSlide: v={} a={}".format(v, a))
            self.slider_music_playtime.setMaximum(a)
            if self.__slider_music_pressed is False:
                self.slider_music_playtime.setValue(v)
            self.label_musicplaytime.setText(d + '/' + t)
            #index = self.playlist.currentIndex()
            total = self.playlist.mediaCount()
            self.label_musiccount.setText("{} / {}".format(self.__curr_playlist_index + 1, total))
            #currentItem = self.listWidget.currentItem()
            #if currentItem:
            #    self.label_musicname.setText(currentItem.text())
            self.label_musicname.setText(self.__curr_play_musicname)
        except Exception as e:
            self.logger.info("__PlayerChangeSlide err:{}".format(e))
            
    def __PlayerStateChange(self, v):
        self.logger.info("__PlayerStateChange:{}".format(v))
        if v == QMediaPlayer.PlayingState:  #start play
            self.__button_pressed = False
            pass
        elif v == QMediaPlayer.PausedState:
            pass
        elif v == QMediaPlayer.StoppedState:  #stop play
            #如果不用__button_pressed就会出现正常播放情况下按下上一首/下一首会出现
            #连续跳过好几首的情况。需要用该变量进行一下区分。
            if self.__button_pressed is True:
                self.__button_pressed = False
                self.logger.info("__PlayerStateChange: __button_pressed is True")
            else:
                if self.cm4a_inuse is True:
                    self.cm4a_flag = True
                    self.cm4a_playno += 1       #播放结束切换到下一个片段
                self.__ButtonPlayNextFunction()
            
    def __PlayListItemDoubleClicked(self):
        self.logger.info("__PlayListDoubleItemClicked")
        self.__button_pressed = True
        index = self.listWidget.currentRow()
        self.__player_play(index)
        self.__music_is_pause = False
        
    def __PlayListItemRightClicked(self, point):
        self.logger.info("__PlayListItemRightClicked:{}".format(point))
        menu = QMenu()
        ac1 = menu.addAction("添加")
        ac2 = menu.addAction("删除")
        ac3 = menu.addAction("打开所在目录")
        hitIndex = self.listWidget.row(self.listWidget.itemAt(point))
        self.logger.info("hitIndex = {}".format(hitIndex))
        if hitIndex > -1:
            #name = self.listWidget.item(hitIndex).text()
            action = menu.exec_(self.listWidget.mapToGlobal(point))
            if action == ac1:
                self.logger.info("action=add")
            elif action == ac3:
                pathname = config.get_file_by_index_from_config(hitIndex)
                path = os.path.dirname(pathname)
                name = os.path.basename(pathname)
                path = path.replace('/', '\\')
                #self.logger.info("in dir:{} {} {}".format(name, path, fdir))
                os.system("explorer.exe {}".format(path))
            elif action == ac2:
                #self.logger.info("action=delete {}".format(name))
                config.del_file_from_config(hitIndex)
                curr = self.playlist.currentIndex()
                self.listWidget.removeItemWidget(self.listWidget.takeItem(hitIndex))
                self.playlist.removeMedia(hitIndex)
                if hitIndex > curr:
                    self.playlist.setCurrentIndex(curr)
                    self.listWidget.setCurrentRow(curr)
                elif hitIndex < curr:
                    self.playlist.setCurrentIndex(curr-1)
                    self.listWidget.setCurrentRow(curr-1)
                else:
                    self.__player_play(curr)
    
    def __player_play(self, index:int):
        self.listWidget.setCurrentRow(index)
        currentItem = self.listWidget.currentItem()
        if currentItem:
            songname = currentItem.text()
            self.logger.info("__player_play:songname={} index={}".format(songname, index))
            if songname.endswith(".m4a"):
                if self.cm4a_inuse == False:
                    name = config.get_file_by_index_from_config(index)
                    a = MP4(name)
                    self.__cm4a_music_total_time = int(a.info.length)
                    self.cm4a.change_m4a_to_mp3(name)
                    self.cm4a_list = self.cm4a.get_curr_m4a_list()
                    self.cm4a_playno = 0
                    self.cm4a_inuse = True
                    self.cm4a_playlist_index = index
                    self.logger.info("__player_play m4a name:{}, {} {}".format(name, self.cm4a_list, self.__cm4a_music_total_time))
                else:
                    pass
                    
                if self.cm4a_playno >= len(self.cm4a_list):
                    self.cm4a_inuse = False
                    self.cm4a_flag = False
                    self.__ButtonPlayNextFunction()
                    return
                else:
                    qurl = QUrl.fromLocalFile(self.cm4a_list[self.cm4a_playno])
                    content = QMediaContent(qurl)
                    self.player.setMedia(content)
                self.logger.info("__player_play:cm4a_playno={}".format(self.cm4a_playno))
            else:
                self.cm4a_inuse = False
                self.playlist.setCurrentIndex(index)
                self.player.setMedia(self.playlist.currentMedia())
            
            self.player.play()
            self.__curr_play_musicname = songname
            self.__curr_playlist_index = index



if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s:%(filename)s[line:%(lineno)d]: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())