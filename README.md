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
```
# PythonMusicPlayer
