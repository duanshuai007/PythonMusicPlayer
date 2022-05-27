import os
import sys
import time
import logging
import subprocess
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
import threading

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#TEMPDIR = "{}\.BFMPlayerTemp".format(BASE_DIR)
#if not os.path.exists(TEMPDIR):
#    os.makedirs(TEMPDIR)

TEMPDIR = "temp\.BFMPlayerTemp"

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):   #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

TEMPDIR = resource_path(TEMPDIR)
if not os.path.exists(TEMPDIR):
    os.makedirs(TEMPDIR)
'''
{
    "31号技师" : [0,1,2,3,4,5,6]
}
'''
#将m4a格式音乐文件转换成mp3格式，并按照一定的时间长度进行分割
#first_section_times:用来指定第一段的时间长度，一般为60秒，因为要快一些切割完成，尽快播放减少等待时间。
#section_times:除第一段以后的其他段的时间长度，长度随意。一般选择300秒。
#-ss:指定切割的开始时间
#-t :指定切割的时间长度
#-f :指定切割文件保存的类型
#-n :如果文件已存在，则不重新生成。-y:如果文件已存在，则覆盖旧文件。
#ffmpeg.exe -i "d:/git/xinyue/xxxx.m4a" -ss "00:00:00" -t "00:01:00" -f mp3 -n "d:/git/xinyue/xxxx.mp3"
class ChangeM4AToMP3():
    #                                      0         1    2    3       4          5        6       7      8      9      10                   
    change_to_mp3_mulfile_cmd_list = ["ffmpeg.exe", "-i", "", "-ss", "00:00:00", "-t", "00:01:00", "-f", "mp3", "-n", "D:/gitwork/3333_1.mp3"]
    change_to_mp3_onefile_cmd_list = ["ffmpeg.exe", "-i", "", "-f", "mp3", "-n", ""]

    first_section_times = 60
    section_times = 300
    
    def __init__(self):
        self.__curr_m4a_filename = None
        self.__mp3_from_m4a_dict = {}
        
    def __change_m4a_to_mp3_task(self, filename:str, songname:str, seconds:int):
        count = 1
        exit_f = False
        cut_s_min = 1
        cut_s_sec = 0
        while True:
            newname = "{}\{}_{}.mp3".format(TEMPDIR, songname, count)
            self.change_to_mp3_mulfile_cmd_list[4] = "00:{:02d}:{:02d}".format(cut_s_min, cut_s_sec)
            if seconds > self.section_times:
                seconds -= self.section_times
                self.change_to_mp3_mulfile_cmd_list[6] = "00:{:02d}:00".format(int(self.section_times / 60))
                cut_s_min += int(self.section_times / 60)
            else:
                exit_f = True
                self.change_to_mp3_mulfile_cmd_list[6] = "00:{:02d}:{:02d}".format(int(seconds / 60), int(seconds % 60))
            self.change_to_mp3_mulfile_cmd_list[10] = newname
            #print("subprocess call {}".format(self.change_to_mp3_mulfile_cmd_list))
            try:
                if os.path.exists(newname):
                    a = MP3(newname)
                else:
                    subprocess.call(self.change_to_mp3_mulfile_cmd_list, shell=True)
            except Exception as e:
                self.change_to_mp3_mulfile_cmd_list[9] = "-y"
                subprocess.call(self.change_to_mp3_mulfile_cmd_list, shell=True)
            count += 1
            self.__mp3_from_m4a_dict[filename].append(newname) 
            if exit_f is True:
                break

    def get_curr_m4a_list(self):
        return self.__mp3_from_m4a_dict[self.__curr_m4a_filename]
        
    def change_m4a_to_mp3(self, filename:str):
        if filename.endswith(".m4a"):
            self.__curr_m4a_filename = filename
            t = MP4(filename)
            #print("m4a file length:{}".format(t.info.length))
            m,s = divmod(t.info.length, self.first_section_times)
            m = round(m)
            s = round(s)
            scount = t.info.length
            songname = filename.split('/')[-1]
            songname = songname.split('.')[0]
            #print(songname)
            self.__mp3_from_m4a_dict[filename] = []
            newname = ""
            if scount > self.first_section_times:
                newname = "{}\{}_0.mp3".format(TEMPDIR, songname)
                self.change_to_mp3_mulfile_cmd_list[2] = filename
                self.change_to_mp3_mulfile_cmd_list[4] = "00:00:00"
                self.change_to_mp3_mulfile_cmd_list[6] = "00:01:00"
                self.change_to_mp3_mulfile_cmd_list[10] = newname
                try:
                    if os.path.exists(newname):
                        a = MP3(newname)
                    else:
                        subprocess.call(self.change_to_mp3_mulfile_cmd_list, shell=True)
                except Exception as e:
                    self.change_to_mp3_mulfile_cmd_list[9] = "-y"
                    subprocess.call(self.change_to_mp3_mulfile_cmd_list, shell=True)
                t = threading.Thread(target = self.__change_m4a_to_mp3_task, args=[filename, songname, scount-self.first_section_times])
                t.setDaemon(True)
                t.start()
            else:
                self.change_to_mp3_onefile_cmd_list[2] = filename
                newname = "{}\{}.mp3".format(TEMPDIR, songname)
                self.change_to_mp3_onefile_cmd_list[6] = newname
                try:
                    if os.path.exists(newname):
                        a = MP3(newname)
                    else:
                        subprocess.call(self.change_to_mp3_onefile_cmd_list, shell=True)
                except Exception as e:
                    self.change_to_mp3_onefile_cmd_list[5] = "-y"
                    subprocess.call(self.change_to_mp3_onefile_cmd_list, shell=True)
            self.__mp3_from_m4a_dict[filename].append(newname) 
        
if __name__ == "__main__":
    r = change_m4a_to_mp3("D:/gitwork/xiangsheng/LIST-A/31号技师.m4a")
    count = 0
    while True:
        time.sleep(1)
        count += 1
        if count > 100:
            break