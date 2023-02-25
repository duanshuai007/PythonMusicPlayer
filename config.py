import os
import sys

PLAYLIST_FILE = ".__playlist.txt"

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):   #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

PLAYLIST_FILE = resource_path(PLAYLIST_FILE)
if not os.path.exists(PLAYLIST_FILE):
    #os.makedirs(PLAYLIST_FILE)
    with open(PLAYLIST_FILE, "w") as f:
        f.write('')
    
#检查文件是否已经在配置文件中，如果存在返回True，否则返回False
def check_file_is_exists(filename:str):
    if filename.startswith('file:///'):
        filename = filename.replace('file:///', '')
    filename = filename + '\n'
    with open(PLAYLIST_FILE, 'r') as f:
        m = f.readlines()
        #print("m={} filename={}".format(m, filename))
        for i in m:
            if filename == i:
                return True
    return False

def save_file_to_config(filename:str):
    if filename.startswith('file:///'):
        filename = filename.replace('file:///', '')
    with open(PLAYLIST_FILE, "a") as f:
        f.write(filename + '\n')

def del_file_from_config(index:int):
    wh = open("./.temp", "w");
    with open(PLAYLIST_FILE, "r") as f:
        m = f.readlines()
        c = 0
        for i in m:
            if c == index:
                pass
            else:
                wh.write(i)
            c += 1
    wh.close()
    os.remove(PLAYLIST_FILE)
    os.rename("./.temp", PLAYLIST_FILE)

def get_file_from_config():
    ll = []
    with open(PLAYLIST_FILE, 'r') as f:
        m = f.readlines()
        for i in m:
            i = i.replace('\n', '')
            ll.append(i)
    return ll
    
def get_file_by_index_from_config(index:int):
    with open(PLAYLIST_FILE, "r") as f:
        m = f.readlines()
        c = 0
        for i in m:
            if c == index:
                filename = i.replace('\n', '')
                return filename
            c += 1
    
class Config():
    __save_par = {
        "VOLUME" : "",
        "MODE" : "",
    }
    CONFIG_FILE = ".config"
    def __init__(self):
        self.CONFIG_FILE = resource_path(self.CONFIG_FILE)
        if not os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "w") as f:
                message = "MODE:1\nVOLUME:70\n"
                f.write(message)
            self.__save_par["VOLUME"] = "70"
            self.__save_par["MODE"] = "1"
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