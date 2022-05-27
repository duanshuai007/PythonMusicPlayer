import os
import threading
import time
import tkinter.messagebox
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from ttkthemes import themed_tk as tk
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
import pygame
import random

from logger import LoggingProducer, LoggingConsumer
from m4a_2_mp3 import *

LoggingConsumer()



def resource_path(relative_path):
    if getattr(sys, 'frozen', False):   #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

'''
MODE:1/2/3
VOLUME:0-100
THEME:xxxxxx
'''
class Config():
    __save_par = {
        "VOLUME" : "",
        "MODE" : "",
        "THEME" : ""
    }
    CONFIG_FILE = ".config"
    def __init__(self):
        self.CONFIG_FILE = resource_path(self.CONFIG_FILE)
        if not os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "w") as f:
                message = "MODE:1\nVOLUME:70\nTHEME:ubuntu\n"
                f.write(message)
            self.__save_par["VOLUME"] = "70"
            self.__save_par["MODE"] = "1"
            self.__save_par["THEME"] = "ubuntu"
        else:
            with open(self.CONFIG_FILE, "r") as f:
                m = f.readlines()
                #print(m)
                for l in m:
                    if len(l) > 0 and l.endswith('\n'):
                        l = l.replace('\n', '')
                        key,value = l.split(":")
                        self.__save_par[key] = value
                    
    def get(self, key:str):
        if key in self.__save_par.keys():
            return self.__save_par[key]
        else:
            return None
        
    def set(self, key:str, value:str):
        if key in self.__save_par.keys():
            self.__save_par[key] = value
            #print(self.__save_par)
            sm = ""
            for k in self.__save_par.keys():
                m = "{}:{}\n".format(k, self.__save_par[k])
                sm = "{}{}".format(sm, m)
            with open(self.CONFIG_FILE, "w") as f:
                f.write(sm)
        else:
            print("set key not exists:{}".format(key))


class BFMusicPlayer():
    pause_flag = False
    load_flag = False
    root = None
    conf = None
    playBtn = None
    music_name_label = None
    music_time_label = None
    musci_end_event  = pygame.USEREVENT + 1
    music_next_event = pygame.USEREVENT + 2
    music_pret_event = pygame.USEREVENT + 3
    music_total_time = 0
    music_time_mins = 0
    music_time_secs = 0
    music_file_list = []
    PLAYLIST_FILE = "./.__play_list.txt"
    SHUNXU_MODE     = 1
    RANDOM_MODE     = 2
    SINGLE_MODE     = 3
    __playmode = SHUNXU_MODE
    __curr_play_item_number = -1
    __curr_musicplay_ts = 0
    __is_play_m4a_file = False
    cm4a_list = []
    __button_img_prex = "./image/prex.png"
    __button_img_next = "./image/next.png"
    __button_img_play = "./image/play.png"
    __button_img_pause = "./image/pause.png"
    __button_img_random = "./image/random_play.png"
    __button_img_single = "./image/single_play.png"
    __button_img_shunxu = "./image/shunxu_play.png"
    #Scale控件在使用set函数时也会调用command指定的函数，没有找到好的解决方式，
    #使用该变量作为过滤条件，否则会造成音乐循环播放同一秒无法前进
    __is_setpos_inuse = False
    
    def __init__(self):
        self.logger = LoggingProducer().getlogger()
        self.__button_img_prex = resource_path(self.__button_img_prex)
        self.__button_img_next = resource_path(self.__button_img_next)
        self.__button_img_play = resource_path(self.__button_img_play)
        self.__button_img_pause = resource_path(self.__button_img_pause)
        self.__button_img_random = resource_path(self.__button_img_random)
        self.__button_img_single = resource_path(self.__button_img_single)
        self.__button_img_shunxu = resource_path(self.__button_img_shunxu)
        self.PLAYLIST_FILE = resource_path(self.PLAYLIST_FILE)
        
        self.conf = Config()
        self.__playmode = int(self.conf.get("MODE"), 10)
        self.__volume = int(self.conf.get("VOLUME"), 10)
        pygame.init()       #for pygame.event.get() 
        pygame.mixer.init()
        self.__create_window()
        #初始化组件状态，根据配置文件中保存的信息就行初始化
        self.set_vol(self.__volume)
        self.scale.set(self.__volume)
        if self.__playmode == self.SHUNXU_MODE:
            self.__playmode = self.RANDOM_MODE
            self.playmodeBtn['image'] = self.__random_play_img
        elif self.__playmode == self.RANDOM_MODE:
            self.__playmode = self.SINGLE_MODE
            self.playmodeBtn['image'] = self.__single_play_img
        elif self.__playmode == self.SINGLE_MODE:
            self.__playmode = self.SHUNXU_MODE
            self.playmodeBtn['image'] = self.__shunxu_play_img
        self.cm4a = ChangeM4AToMP3()
        t = threading.Thread(target = self.show_animation, args=[])
        t.setDaemon(True)
        t.start()
        
    def load_music_file(self, music_file_name:str):
        try:
            if music_file_name.endswith(".mp3"):
                a = MP3(music_file_name)
                self.music_total_time = int(a.info.length)
            elif music_file_name.endswith(".wav"):
                a = pygame.mixer.Sound(music_file_name)
                self.music_total_time = a.get_length()
            elif music_file_name.endswith(".m4a"):
                a = MP4(music_file_name)
                self.music_total_time = int(a.info.length)
            self.logger.info("filename:{} times:{}".format(music_file_name, self.music_total_time))
            #pygame.mixer.music.unload()
            self.music_time_mins, self.music_time_secs = divmod(self.music_total_time, 60)
            self.music_time_mins = round(self.music_time_mins)
            self.music_time_secs = round(self.music_time_secs)
            self.music_time_label['text'] = "00:00 / {:02d}:{:02d}".format(self.music_time_mins, self.music_time_secs)
            self.musciplay_time_scale['to'] = self.music_total_time
            self.music_name_label['text'] = os.path.basename(music_file_name)
            self.musciplay_time_scale.set(0)
            if music_file_name.endswith(".mp3") or music_file_name.endswith(".wav"):
                pygame.mixer.music.load(music_file_name)
                self.__is_play_m4a_file = False
                pygame.mixer.music.set_endevent(self.musci_end_event)
            elif music_file_name.endswith(".m4a"):
                self.cm4a.change_m4a_to_mp3(music_file_name)
                self.cm4a_list = self.cm4a.get_curr_m4a_list()
                self.cm4a_playno = 0
                pygame.mixer.music.load(self.cm4a_list[self.cm4a_playno])
                self.__is_play_m4a_file = True
                if len(self.cm4a_list) >= 2:
                    pygame.mixer.music.queue(self.cm4a_list[self.cm4a_playno+1])
                pygame.mixer.music.set_endevent(self.musci_end_event)
                pass
            self.load_flag = True
        except Exception as e:
            self.logger.info("load_music_file:{} err:{}".format(music_file_name, e))

    def play_music(self):
        if pygame.mixer.music.get_busy() is True:
            pygame.mixer.music.pause()
            self.pause_flag = True
            self.playBtn['image'] = self.play_img
        else:
            if self.pause_flag is True:
                pygame.mixer.music.unpause()
                self.pause_flag = False
                self.playBtn['image'] = self.pause_img
            else:
                if self.load_flag is False:
                    self.__curr_play_item_number = 0
                    self.load_music_file(self.music_file_list[self.__curr_play_item_number])
                self.playlistbox.selection_set(self.__curr_play_item_number)
                pygame.mixer.music.play()
                self.playBtn['image'] = self.pause_img

    def set_vol(self, val):
        #val是字符串类型的浮点数，不能通过int函数直接转换
        if type(val) is str:
            intstr,littlestr = val.split('.')
            self.conf.set("VOLUME", intstr)
        else:
            self.conf.set("VOLUME", "{}".format(val))
        volume = float(val) / 100
        pygame.mixer.music.set_volume(volume)

    def set_musci_play_time(self, val):
        #self.logger.info("set_musci_play_time:{} type={}".format(val, type(val)))
        if self.__is_setpos_inuse is False:
            try:
                s = int(val.split('.')[0])
                self.__curr_musicplay_ts = s
            except Exception as e:
                self.logger.error("set_musci_play_time val:{} err:{}".format(val, e))
            if pygame.mixer.music.get_busy():
                if self.__is_play_m4a_file is True:
                    if s < self.cm4a.first_section_times:
                        self.cm4a_playno = 0
                        ss = s
                    else:
                        nn = int((s - self.cm4a.first_section_times) / self.cm4a.section_times) + 1
                        ss = int((s - self.cm4a.first_section_times) % self.cm4a.section_times)
                        self.cm4a_playno = nn
                    #self.logger.info("set_musci_play_time m4a:playno={} ss={}".format(self.cm4a_playno, ss))
                    pygame.mixer.music.load(self.cm4a_list[self.cm4a_playno])
                    if self.cm4a_playno < len(self.cm4a_list) - 2:
                        pygame.mixer.music.queue(self.cm4a_list[self.cm4a_playno+1])
                    pygame.mixer.music.play()
                    pygame.mixer.music.set_pos(ss)
                else:
                    pygame.mixer.music.play()
                    pygame.mixer.music.set_pos(s)
    
    def __music_next(self):
        e = pygame.event.Event(self.music_next_event, attr=None)
        pygame.event.post(e)
        
    def __music_pret(self):
        e = pygame.event.Event(self.music_pret_event, attr=None)
        pygame.event.post(e)
        
    def __add_music_dir(self):
        try:
            filename_path = filedialog.askdirectory()
            if len(filename_path) > 0:
                self.logger.info("__add_music_dir:{}".format(filename_path))
                s = os.listdir(filename_path)
                self.logger.info(s)
                for i in s:
                    if i.endswith(".mp3") or i.endswith(".wav") or i.endswith(".m4a"):
                        if i not in self.music_file_list:
                            fullpath_music_name = "{}/{}".format(filename_path, i)
                            self.music_file_list.append(fullpath_music_name)
                            with open(self.PLAYLIST_FILE, "a") as f:
                                f.write("{}\n".format(fullpath_music_name))
                            name = os.path.basename(i)
                            self.playlistbox.insert("end", name)
        except Exception as e:
            self.logger.info("browse_file err:{}".format(e))
            
    def __add_music_file(self):
        try:
            #askopenfilenames可以添加多个文件 askopenfilename添加单个文件
            filename_path = filedialog.askopenfilenames(title = "音乐播放器", filetypes =[("mp3文件","*.mp3"),("WMA文件","*.wma"),("WAV文件","*.wav"),("M4A文件", "*.m4a")])   
            #if filename_path.endswith(".mp3") or filename_path.endswith(".wav"):
            for i in filename_path:
                if i not in self.music_file_list:
                    self.music_file_list.append(i)
                    with open(self.PLAYLIST_FILE, "a") as f:
                        f.write("{}\n".format(i))
                    name = os.path.basename(i)
                    self.playlistbox.insert("end", name)
            #print("__add_music_file:{}".format(self.music_file_list))
        except Exception as e:
            self.logger.info("browse_file err:{}".format(e))
    
    def __double_click_playlist_item(self, v):
        self.logger.info(self.playlistbox.curselection())
        #s = self.playlistbox.get(self.playlistbox.curselection())
        #print("double click:{}".format(v))
        try:
            #if self.__curr_play_item_number >= 0:
            #    self.playlistbox.selection_clear(self.__curr_play_item_number)
            self.__curr_play_item_number = self.playlistbox.curselection()[0]
            self.load_music_file(self.music_file_list[self.__curr_play_item_number])
            self.play_music()
        except Exception as e:
            self.logger.error("__double_click_playlist_item err:{}".format(e))

    def __right_click_playlist_item(self, v):
        #print("__rightclick_playlist_item:{}".format(v))
        self.playlistbox.selection_clear(self.__curr_play_item_number)
        self.__curr_play_item_number = self.playlistbox.nearest(v.y)
        self.playlistbox.selection_set(self.__curr_play_item_number)
        #s = self.playlistbox.get(self.__curr_play_item_number)
        #print(s)
        try:
            #第三个参数设置为0 则弹出菜单可以无限制创建
            #设置为1，则弹出菜单只能存在一个
            self.popmenu.tk_popup(v.x_root, v.y_root, 1)
        finally:
            self.popmenu.grab_release()
    def __playlist_item_settop(self):
        pass
    def __playlist_item_delete(self):
        s = self.playlistbox.get(self.__curr_play_item_number)
        self.logger.info("__playlist_item_delete:{}".format(s))
        #需要在3个地方进行删除
        #1.playlistbox中进行删除,根据索引进行删除
        self.playlistbox.delete(self.__curr_play_item_number)
        #2.music_file_list中删除
        for n in self.music_file_list:
            if s in n:
                self.music_file_list.remove(n)
                break
        #print(self.music_file_list)
        #3.PLAYLIST_FILE中进行删除
        wh = open("./.temp", "w");
        with open(self.PLAYLIST_FILE, "r") as f:
            m = f.readlines()
            for i in m:
                if s not in i:
                    wh.write(i)
        wh.close()
        os.remove(self.PLAYLIST_FILE)
        os.rename("./.temp", self.PLAYLIST_FILE)
        pass
        
    def __set_theme_1(self):
        s = self.userChoice.get()
        self.logger.info("__set_theme_1:{}".format(s))
        self.root.set_theme(s)
        self.conf.set("THEME", s)
        
    def __set_music_playmode(self):
        if self.__playmode == self.SHUNXU_MODE:
            self.__playmode = self.RANDOM_MODE
            #self.playmodeBtn['text'] = "随"
            self.playmodeBtn['image'] = self.__random_play_img
        elif self.__playmode == self.RANDOM_MODE:
            self.__playmode = self.SINGLE_MODE
            self.playmodeBtn['image'] = self.__single_play_img
        elif self.__playmode == self.SINGLE_MODE:
            self.__playmode = self.SHUNXU_MODE
            self.playmodeBtn['image'] = self.__shunxu_play_img
        self.conf.set("MODE", "{}".format(self.__playmode))
    
    def __about_info(self):
        msg = "QQ:334862088 注明来意\r\n邮箱:duanbixing@163.com\r\nTEMPDIR:{}".format(TEMPDIR)
        tkinter.messagebox.showinfo('About Me', msg)
        
    def __create_window(self):
        #self.root = Tk()
        self.root =  tk.ThemedTk()
        #设置窗口大小不可调整
        self.root.title("BFMPlayer")
        
        window_size_w = 200
        window_size_h = 380
        object_h_seq = 20
        
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        self.root.geometry("{}x{}+{}+{}".format(window_size_w, window_size_h, w - int(1.5*window_size_w), 40))
        self.root.resizable(width=False, height=False)
        
        #theme_config = "scidgreen"
        #if os.path.exists(self.THEME_CONF_FILE):
        #    with open(self.THEME_CONF_FILE, 'r') as f:
        #        theme_config = f.readline()
        #        theme_config = theme_config.replace('\r', '')
        #        theme_config = theme_config.replace('\n', '')
        theme_config = self.conf.get("THEME")
        #t = self.root.get_themes()                 # Returns a list of all themes that can be set
        #['classic', 'radiance', 'scidgrey', 'smog', 'aquativo', 'scidsand', 'winxpblue', 'clearlooks', 'scidpink', 'scidpurple', 'xpnative', 'scidmint', 'keramik', 'clam', 'default', 'elegance', 'vista', 'black', 'scidblue', 'winnative', 'equilux', 'blue', 'alt', 'kroc', 'plastik', 'yaru', 'scidgreen', 'breeze', 'arc', 'adapta', 'itft1', 'ubuntu']
        self.root.set_theme(theme_config)
        
        self.menubar = Menu(self.root)
        #tearoff=0则菜单没有顶部分割线
        #tearoff默认，则菜单顶部有可点击的分割线
        self.subMenu = Menu(self.menubar, tearoff=0)
        self.themeMenu = Menu(self.menubar, tearoff=0)
        self.aboutMenu = Menu(self.menubar, tearoff=0)
        self.root.config(menu = self.menubar)

        self.menubar.add_cascade(label="添加", menu = self.subMenu)
        self.subMenu.add_command(label="添加路径", command = self.__add_music_dir)
        self.subMenu.add_separator()
        self.subMenu.add_command(label="添加文件", command = self.__add_music_file)
        #self.subMenu.add_separator()
        #self.subMenu.add_command(label="退出", command = self.root.destroy)
        
        self.menubar.add_cascade(label="主题", menu = self.themeMenu)
        t = self.root.get_themes()
        t.sort()
        self.menubar.add_cascade(label="关于", menu = self.aboutMenu)
        self.aboutMenu.add_command(label="关于", command = self.__about_info)
        '''
        两种实现菜单radiobutton参数传递的方式
        for i in t:
            self.themeMenu.add_radiobutton(label=i, variable=selected, value=index, command = lambda theme=i:self.__set_theme(theme))
        '''
        self.userChoice=StringVar()
        self.userChoice.set('')
        for i in t:
            if i == theme_config:
                self.userChoice.set(i)
            self.themeMenu.add_radiobutton(label=i, variable=self.userChoice, value=i, command = self.__set_theme_1)
        #创建弹出式菜单
        self.popmenu = Menu(self.root, tearoff=0)
        self.popmenu.add_command(label = "置        顶", command = self.__playlist_item_settop)
        self.popmenu.add_command(label = "从列表中删除", command = self.__playlist_item_delete)
        
        #place布局方式
        listbox_h = 240
        self.music_name_label = ttk.Label(self.root, text='')
        self.music_name_label.place(x=0, y=listbox_h + 10, width=window_size_w - 40, height=22)
        self.music_time_label = ttk.Label(self.root, text='')
        self.music_time_label.place(x=int(window_size_w/2) - 20, y=listbox_h + 30, width=window_size_w - 40, height=22)
        
        self.music_count_label = ttk.Label(self.root, text='')
        self.music_count_label.place(x=4, y=listbox_h + 30, width=60, height=22)
        
        self.__random_play_img = PhotoImage(file=self.__button_img_random)
        self.__single_play_img = PhotoImage(file=self.__button_img_single)
        self.__shunxu_play_img = PhotoImage(file=self.__button_img_shunxu)
        #self.playmodeBtn = ttk.Button(self.root, text="顺", command = self.__set_music_playmode)
        self.playmodeBtn = Button(self.root, image=self.__shunxu_play_img, command = self.__set_music_playmode)
        self.playmodeBtn.place(x=window_size_w-40, y=listbox_h+15, width=30, height=30)
        
        #volume set
        self.scale = ttk.Scale(self.root, from_=0, to=100, orient=HORIZONTAL, command = self.set_vol)
        self.scale.set(70)  # implement the default value of scale when music player starts
        pygame.mixer.music.set_volume(0.7)
        self.scale.place(x=10, y=listbox_h  + 22 + 30, width=window_size_w - 20, height=22)
        #时间进度条
        self.musciplay_time_scale = ttk.Scale(self.root, from_=0, to=100, orient=HORIZONTAL, command = self.set_musci_play_time)
        #self.musciplay_time_scale = ttk.Scale(self.root, from_=0, to=100, orient=HORIZONTAL, command = lambda var=0: self.set_musci_play_time(var, False))
        self.musciplay_time_scale.set(0)
        self.musciplay_time_scale.place(x=10, y=listbox_h  + 22 + 30 + 30, width=window_size_w - 20, height=22)
        
        self.prex_img = PhotoImage(file=self.__button_img_prex)
        self.logger.info("w={} h={}".format(self.prex_img.width(), self.prex_img.height()))
        self.pretBtn = Button(self.root, image=self.prex_img, command = self.__music_pret)
        #self.pretBtn.place(x=10, y=listbox_h + object_h_seq + 22 + object_h_seq + 22 + 30, width=int((window_size_w - 40)/3), height=30)
        self.pretBtn.place(x=10, y=listbox_h + object_h_seq + 22 + object_h_seq + 22 + 30, width=40, height=20)
        self.play_img = PhotoImage(file=self.__button_img_play)
        self.pause_img = PhotoImage(file=self.__button_img_pause)
        #self.playBtn = ttk.Button(self.root, text="播放", command = self.play_music)
        self.playBtn = Button(self.root, image=self.play_img, command = self.play_music)
        self.playBtn.place(x=20 + int((window_size_w - 40)/3), y=listbox_h + object_h_seq + 22 + object_h_seq + 22 + 30, width=40, height=20)
        self.next_img = PhotoImage(file=self.__button_img_next)
        self.nextBtn = Button(self.root, image=self.next_img, command = self.__music_next)
        self.nextBtn.place(x=30 + int((window_size_w - 40)/3)*2, y=listbox_h + object_h_seq + 22 + object_h_seq + 22 + 30, width=40, height=20)

        scrollbar_w = 20
        sc = Scrollbar(self.root)
        sc.place(x=window_size_w - scrollbar_w, y=0, width=scrollbar_w, height=240)
        self.playlistbox = Listbox(self.root, selectmode=SINGLE, yscrollcommand=sc.set)
        self.playlistbox.place(x=0, y=0, width=window_size_w - scrollbar_w, height=240)
        self.playlistbox.bind("<Double-Button-1>", self.__double_click_playlist_item)
        self.playlistbox.bind("<Button-3>", self.__right_click_playlist_item)
        sc.config(command=self.playlistbox.yview)
        if os.path.exists(self.PLAYLIST_FILE):
            with open(self.PLAYLIST_FILE, 'r') as f:
                while True:
                    m = f.readline()
                    if len(m) == 0:
                        break
                    m = m.replace('\n', '')
                    self.music_file_list.append(m)
                    n = os.path.basename(m)
                    self.playlistbox.insert("end", n)

    def forever(self):
        self.root.mainloop()

    def show_animation(self):
        while True:
            try:
                if pygame.mixer.music.get_busy() is True:
                    t = int(pygame.mixer.music.get_pos() / 1000)
                    t += self.__curr_musicplay_ts
                    #self.logger.info("t={}".format(t))
                    cmins, csecs = divmod(t, 60)
                    cmins = round(cmins)
                    csecs = round(csecs)
                    self.music_time_label['text'] = "{:02d}:{:02d} / {:02d}:{:02d}".format(cmins, csecs, self.music_time_mins, self.music_time_secs)
                    self.__is_setpos_inuse = True
                    self.musciplay_time_scale.set(t)
                    self.__is_setpos_inuse = False
                for event in pygame.event.get():
                    if event.type == self.musci_end_event:
                        self.music_time_label['text'] = "{:02d}:{:02d} / {:02d}:{:02d}".format(0, 0, self.music_time_mins, self.music_time_secs)
                        #self.playBtn['text'] = "播放"
                        self.playBtn['image'] = self.play_img
                        #self.logger.info("musci_end_event")
                        if self.__is_play_m4a_file is True:
                            if self.cm4a_playno < len(self.cm4a_list) - 2:
                                self.cm4a_playno += 1
                                self.__curr_musicplay_ts = self.cm4a.first_section_times + ((self.cm4a_playno - 1) * self.cm4a.section_times)
                                self.logger.info("self.__curr_musicplay_ts:{} no={}".format(self.__curr_musicplay_ts, self.cm4a_playno))
                                if pygame.mixer.music.get_busy() is False:
                                    pygame.mixer.music.load(self.cm4a_list[self.cm4a_playno])
                                    self.play_music()
                                    pygame.mixer.music.queue(self.cm4a_list[self.cm4a_playno+1])
                                else:
                                    pygame.mixer.music.queue(self.cm4a_list[self.cm4a_playno+1])
                                self.playBtn['image'] = self.pause_img
                                continue
                            elif self.cm4a_playno == len(self.cm4a_list) - 2:
                                self.cm4a_playno += 1
                                self.__curr_musicplay_ts = self.cm4a.first_section_times + ((self.cm4a_playno - 1) * self.cm4a.section_times)
                                self.logger.info("this music last section")
                                self.playBtn['image'] = self.pause_img
                                continue
                            else:
                                self.__is_play_m4a_file = False

                        if self.__playmode == self.SHUNXU_MODE:
                            self.__music_next()
                        elif self.__playmode == self.SINGLE_MODE:
                            self.load_music_file(self.music_file_list[self.__curr_play_item_number])
                            self.play_music()
                        elif self.__playmode == self.RANDOM_MODE:
                            while True:
                                s = random.randint(0, len(self.music_file_list)-1)
                                if s != self.__curr_play_item_number:
                                    self.playlistbox.selection_clear(self.__curr_play_item_number)
                                    self.__curr_play_item_number = s
                                    break
                            self.load_music_file(self.music_file_list[self.__curr_play_item_number])
                            self.play_music()
                    elif event.type == self.music_next_event:
                        self.playlistbox.selection_clear(self.__curr_play_item_number)
                        self.__curr_play_item_number += 1
                        if self.__curr_play_item_number >= len(self.music_file_list):
                            self.__curr_play_item_number = 0
                        self.load_music_file(self.music_file_list[self.__curr_play_item_number])
                        self.play_music()
                    elif event.type == self.music_pret_event:
                        self.playlistbox.selection_clear(self.__curr_play_item_number)
                        if self.__curr_play_item_number == 0:
                            self.__curr_play_item_number = len(self.music_file_list) - 1
                        else:
                            self.__curr_play_item_number -= 1
                        self.load_music_file(self.music_file_list[self.__curr_play_item_number])
                        self.play_music()
                self.music_count_label['text'] = "{}/{}".format( self.__curr_play_item_number + 1, len(self.music_file_list))
                time.sleep(0.2)
            except Exception as e:
                self.logger.info("animation err:{}".format(e))

if __name__ == "__main__":
    p = BFMusicPlayer()
    p.forever()
