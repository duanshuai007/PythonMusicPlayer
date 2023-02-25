# Python Music Player

#### pygame, tkinter

## 说明

1.实现了添加单个文件和添加音乐文件路径，目前只支持mp3和wav(未测试)  
2.实现了显示当前播放的音乐文件名，歌曲总时长，当前播放的市场，歌曲总数量，当前播放的是第几首。  
3.实现了调整音乐大小的滑条。  
4.实现了上一首，下一首，以及暂停播放按钮。  
5.通过一个按钮实现了顺序播放/单曲循环/随机播放的播放模式的切换。  
6.实现了保存当前配置的主题，音量大小，播放模式，设置后关闭软件再次打开时会使用此配置。  


## 生成exe文件方法

```
安装pyinstaller工具
pip install pyinstaller
然后将pyinstaller工具添加到环境变量(WIN7)
$ which python
/c/Users/Administrator/AppData/Local/Programs/Python/Python37/python
一般pyinstaller就在/c/Users/Administrator/AppData/Local/Programs/Python/Python37/python/Scripts目录中
打开"计算机->属性->高级系统设置->环境变量"，在系统变量中寻找PATH，将/c/Users/Administrator/AppData/Local/Programs/Python/Python37/python/Scripts添加到PATH的尾部。



在项目根目录下执行
pyinstaller -F player.py
会在根目录的dist目录下生成player.exe文件
如果不想要显示控制台
pyinstaller -Fw player.py

因为项目中使用了自定的按钮图片，如果只使用以上的方式不能直接将资源文件包含到exe中。
这是可以使用
 pyi-makespec.exe -Fw -i image/icon.png mixer_music_play.py
生成mixer_music_play.spec文件
在代码中加入
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):   #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)
将所有使用到的资源文件仅进行绝对地址定位
如:
	random_playmode_image = "image/playmode.png"
需要执行以下操作得到绝对地址
	random_playmode_image = "image/playmode.png"
	random_playmode_image = resource_path(random_playmode_image)
修改mixer_music_play.spec文件中的Analysis->pathex 填入项目的绝对地址"C:/Users/Administrator/git/PythonMusicPlayer"
修改Analysis->datas 填入 ("image","image"), ("temp","temp")
意思是将目录中的image文件打包入exe中,取名为image
将目录中的temp文件打包如exe中,取名为temp
然后执行pyinstaller.exe mixer_music_play.spec 即可生成exe文件。

```
## ffmpeg命令

```
ffmpeg.exe -i "D:\git\xiangsheng\LIST-A\31号技师.m4a" -y -acodec libmp3lame -aq 0 "D:/git/xiangsheng/111.mp3"
ffmpeg.exe -i "D:\git\xiangsheng\LIST-A\31号技师.m4a" -y -f mp3 "D:/git/xiangsheng/111.mp3"

将输入文件从00:00:00开始切割1分钟长度生成输出文件，格式mp3
ffmpeg.exe -i "D:/git/xiangsheng/LIST-A/31号技师.m4a" -ss 00:00:00 -t 00:01:00 -f mp3 "D:/git/3333_1.mp3"
```


## 在python脚本中调用subprocess.call会弹出窗口

在调用`subprocess.call`时加入`shell=True`即可不再弹出窗口

```
subprocess.call(['ls', '-la'], shell=True)
```


### PyQt5-tools 


```
打开designer:
 pyqt5-tools.exe designer

将生成的ui文件转换成为代码可以使用的py文件
pyuic5.exe -o qt5player.py qt5player.ui

class Window(QtWidgets.QMainWindow, Ui_qt5player):
    def __init__(self):
        super(Window, self).__init__()
        self.setupUi(self)
		
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
```