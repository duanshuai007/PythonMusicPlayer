import os
import threading
import time
import tkinter.messagebox
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from ttkthemes import themed_tk as tk
from mutagen.mp3 import MP3
import pygame
import random


'''
MODE:1/2/3
VOLUME:0-100
THEME:xxxxxx
'''
class Config():
    
    CONFIG_FILE = "./.config"
    __save_par = {
        "VOLUME" : "",
        "MODE" : "",
        "THEME" : ""
    }
    def __init__(self):
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

    
class BigFishMusicPlayer():
    
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
    __curr_play_item_number = 0
    
    def __init__(self):
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
            self.playmodeBtn['text'] = "随"
        elif self.__playmode == self.RANDOM_MODE:
            self.__playmode = self.SINGLE_MODE
            self.playmodeBtn['text'] = "单"
        elif self.__playmode == self.SINGLE_MODE:
            self.__playmode = self.SHUNXU_MODE
            self.playmodeBtn['text'] = "顺"
            
        t = threading.Thread(target = self.show_animation, args=[])
        t.setDaemon(True)
        t.start()
        
    def load_music_file(self, music_file_name:str):
        try:
            if music_file_name.endswith(".mp3"):
                a = MP3(music_file_name)
                self.music_total_time = int(a.info.length)
            else:
                a = pygame.mixer.Sound(music_file_name)
                self.music_total_time = a.get_length()
            print("total length:{}".format(self.music_total_time))
            pygame.mixer.music.load(music_file_name)
            pygame.mixer.music.set_endevent(self.musci_end_event)
            #file_data = os.path.splitext(music_file_name)
            #name = music_file_name.split('/')[-1]
            name = os.path.basename(music_file_name)
            self.music_name_label['text'] = name
            
            self.music_time_mins, self.music_time_secs = divmod(self.music_total_time, 60)
            self.music_time_mins = round(self.music_time_mins)
            self.music_time_secs = round(self.music_time_secs)
            self.music_time_label['text'] = "00:00 / {:02d}:{:02d}".format(self.music_time_mins, self.music_time_secs)
            #print(self.music_time_label['text'])
            self.load_flag = True
        except Exception as e:
            print("load_music_file:{} err:{}".format(music_file_name, e))

    def play_music(self):
        if pygame.mixer.music.get_busy() is True:
            print("pause")
            pygame.mixer.music.pause()
            self.playBtn['text'] = "播放"
            self.pause_flag = True
        else:
            if self.pause_flag is True:
                print("unpause")
                pygame.mixer.music.unpause()
                self.playBtn['text'] = "暂停"
                self.pause_flag = False
            else:
                print("play")
                if self.load_flag is False:
                    self.__curr_play_item_number = 0
                    self.load_music_file(self.music_file_list[self.__curr_play_item_number])
                print("activate:{}".format(self.__curr_play_item_number))
                self.playlistbox.selection_set(self.__curr_play_item_number)
                pygame.mixer.music.play()
                self.playBtn['text'] = "暂停"

    def set_vol(self, val):
        #val是字符串类型的浮点数，不能通过int函数直接转换
        if type(val) is str:
            intstr,littlestr = val.split('.')
            #print("setvol:val={} type={}".format(val, type(val)))
            self.conf.set("VOLUME", intstr)
        else:
            self.conf.set("VOLUME", "{}".format(val))
        volume = float(val) / 100
        pygame.mixer.music.set_volume(volume)

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
                print("__add_music_dir:{}".format(filename_path))
                s = os.listdir(filename_path)
                print(s)
                for i in s:
                    if i.endswith(".mp3") or i.endswith(".wav"):
                        fullpath_music_name = "{}/{}".format(filename_path, i)
                        self.music_file_list.append(fullpath_music_name)
                        with open(self.PLAYLIST_FILE, "a") as f:
                            f.write("{}\n".format(fullpath_music_name))
                        name = os.path.basename(i)
                        self.playlistbox.insert("end", name)
        except Exception as e:
            print("browse_file err:{}".format(e))
            
    def __add_music_file(self):
        try:
            filename_path = filedialog.askopenfilename()
            if filename_path.endswith(".mp3") or filename_path.endswith(".wav"):
                self.music_file_list.append(filename_path)
                with open(self.PLAYLIST_FILE, "a") as f:
                    f.write("{}\n".format(filename_path))
                name = os.path.basename(filename_path)
                self.playlistbox.insert("end", name)
            #print("__add_music_file:{}".format(self.music_file_list))
        except Exception as e:
            print("browse_file err:{}".format(e))
    
    def __double_click_playlist_item(self, v):
        #print(self.playlistbox.curselection())
        #s = self.playlistbox.get(self.playlistbox.curselection())
        #print("double click:{}".format(v))
        self.playlistbox.selection_clear(self.__curr_play_item_number)
        self.__curr_play_item_number = self.playlistbox.curselection()[0]
        self.load_music_file(self.music_file_list[self.__curr_play_item_number])
        self.play_music()
        
    def __rightclick_playlist_item(self, v):
        #print("__rightclick_playlist_item:{}".format(v))
        self.playlistbox.selection_clear(self.__curr_play_item_number)
        self.__curr_play_item_number = self.playlistbox.nearest(v.y)
        self.playlistbox.selection_set(self.__curr_play_item_number)
        s = self.playlistbox.get(self.__curr_play_item_number)
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
        print("__playlist_item_delete:{}".format(s))
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
            #print("+====================")
            #print(m)
            for i in m:
                if s in i:
                    pass
                else:
                    wh.write(i)
        wh.close()
        os.remove(self.PLAYLIST_FILE)
        os.rename("./.temp", self.PLAYLIST_FILE)
        pass
        
    def __set_theme_1(self):
        s = self.userChoice.get()
        print("__set_theme_1:{}".format(s))
        self.root.set_theme(s)
        #with open(self.THEME_CONF_FILE, "w") as f:
        #    f.write(s)
        self.conf.set("THEME", s)
        
    def __set_music_playmode(self):
        if self.__playmode == self.SHUNXU_MODE:
            self.__playmode = self.RANDOM_MODE
            self.playmodeBtn['text'] = "随"
        elif self.__playmode == self.RANDOM_MODE:
            self.__playmode = self.SINGLE_MODE
            self.playmodeBtn['text'] = "单"
        elif self.__playmode == self.SINGLE_MODE:
            self.__playmode = self.SHUNXU_MODE
            self.playmodeBtn['text'] = "顺"
        self.conf.set("MODE", "{}".format(self.__playmode))
    
    def __about_info(self):
        tkinter.messagebox.showinfo('About Me', 'QQ:334862088 注明来意\r\n邮箱:duanbixing@163.com')
        
    def __create_window(self):
        #self.root = Tk()
        self.root =  tk.ThemedTk()
        #设置窗口大小不可调整
        self.root.title("BFMPlayer")
        
        window_size_w = 200
        window_size_h = 360
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
        
        '''
        #grid布局方式
        f = Frame(self.root)
        f.pack()
        
        self.music_name_label = ttk.Label(f, text='')
        self.music_name_label.grid(row=0, column=0, padx=10)
        self.music_time_label = ttk.Label(f, text='')
        self.music_time_label.grid(row=0, column=1, padx=10)
        scale = ttk.Scale(f, from_=0, to=100, orient=HORIZONTAL, command = self.set_vol)
        scale.set(70)  # implement the default value of scale when music player starts
        pygame.mixer.music.set_volume(0.7)
        scale.grid(row=0, column=2, pady=10, padx=50)
        self.pretBtn = ttk.Button(f, text="上一首", command = self.__music_pret)
        self.pretBtn.grid(row=0, column=3, padx=10)
        self.playBtn = ttk.Button(f, text="播放", command = self.play_music)
        self.playBtn.grid(row=0, column=4, padx=10)
        self.nextBtn = ttk.Button(f, text="下一首", command = self.__music_next)
        self.nextBtn.grid(row=0, column=5, padx=10)
        #self.playBtn["state"] = DISABLED / NORMAL
        
        sc = Scrollbar(f)
        sc.grid(row=1, column=1, pady=50)
        self.playlistbox = Listbox(f, selectmode=SINGLE, yscrollcommand=sc.set)
        self.playlistbox.grid(row=1, column=0, padx=50, pady=50)
        self.playlistbox.bind("<Double-Button-1>", self.__double_click_playlist_item)
        sc.config(command=self.playlistbox.yview)
        if os.path.exists(self.PLAYLIST_FILE):
            with open(self.PLAYLIST_FILE, 'r') as f:
                while True:
                    m = f.readline()
                    if len(m) == 0:
                        break
                    m = m.replace('\n', '')
                    print(m)
                    print("-------")
                    self.music_file_list.append(m)
                    n = os.path.basename(m)
                    self.playlistbox.insert("end", n)
        '''
        #place布局方式
        listbox_h = 240
        self.music_name_label = ttk.Label(self.root, text='')
        self.music_name_label.place(x=0, y=listbox_h + 10, width=window_size_w - 40, height=22)
        self.music_time_label = ttk.Label(self.root, text='')
        self.music_time_label.place(x=int(window_size_w/2) - 20, y=listbox_h + 30, width=window_size_w - 40, height=22)
        
        self.music_count_label = ttk.Label(self.root, text='')
        self.music_count_label.place(x=4, y=listbox_h + 30, width=60, height=22)
        
        self.playmodeBtn = ttk.Button(self.root, text="顺", command = self.__set_music_playmode)
        self.playmodeBtn.place(x=window_size_w-40, y=listbox_h, width=30, height=30)
        
        self.scale = ttk.Scale(self.root, from_=0, to=100, orient=HORIZONTAL, command = self.set_vol)
        self.scale.set(70)  # implement the default value of scale when music player starts
        pygame.mixer.music.set_volume(0.7)
        self.scale.place(x=10, y=listbox_h  + 22 + 30, width=window_size_w - 20, height=22)
        
        self.pretBtn = ttk.Button(self.root, text="上一首", command = self.__music_pret)
        self.pretBtn.place(x=10, y=listbox_h + object_h_seq + 22 + object_h_seq + 22, width=int((window_size_w - 40)/3), height=30)
        self.playBtn = ttk.Button(self.root, text="播放", command = self.play_music)
        self.playBtn.place(x=20 + int((window_size_w - 40)/3), y=listbox_h + object_h_seq + 22 + object_h_seq + 22, width=int((window_size_w - 40)/3), height=30)
        self.nextBtn = ttk.Button(self.root, text="下一首", command = self.__music_next)
        self.nextBtn.place(x=30 + int((window_size_w - 40)/3)*2, y=listbox_h + object_h_seq + 22 + object_h_seq + 22, width=int((window_size_w - 40)/3), height=30)

        scrollbar_w = 20
        sc = Scrollbar(self.root)
        sc.place(x=window_size_w - scrollbar_w, y=0, width=scrollbar_w, height=240)
        self.playlistbox = Listbox(self.root, selectmode=SINGLE, yscrollcommand=sc.set)
        self.playlistbox.place(x=0, y=0, width=window_size_w - scrollbar_w, height=240)
        self.playlistbox.bind("<Double-Button-1>", self.__double_click_playlist_item)
        self.playlistbox.bind("<Button-3>", self.__rightclick_playlist_item)
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
                    cmins, csecs = divmod(t, 60)
                    cmins = round(cmins)
                    csecs = round(csecs)
                    self.music_time_label['text'] = "{:02d}:{:02d} / {:02d}:{:02d}".format(cmins, csecs, self.music_time_mins, self.music_time_secs)
                for event in pygame.event.get():
                    if event.type == self.musci_end_event:
                        self.music_time_label['text'] = "{:02d}:{:02d} / {:02d}:{:02d}".format(0, 0, self.music_time_mins, self.music_time_secs)
                        self.playBtn['text'] = "播放"
                        print("musci_end_event")
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
                            pass
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
                self.music_count_label['text'] = "{}/{}".format( self.__curr_play_item_number, len(self.music_file_list))
                time.sleep(0.1)
            except Exception as e:
                print("animation err:{}".format(e))

p = BigFishMusicPlayer()
#p.load_music_file("F:/音乐/JAY/0208.威廉古堡.mp3")
#p.play_music()
p.forever()
