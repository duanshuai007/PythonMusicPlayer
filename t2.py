from pydub import AudioSegment

def trans_m4a_to_mp3():
    song = AudioSegment.from_file("D:/gitwork/xiangsheng/LIST-C/十万个为什么.m4a")
    song.export("xxxxxx.mp3", format="mp3")
    
#trans_m4a_to_mp3()
    
    
from playsound import playsound

playsound("F://音乐//1111//0101.可爱女人.mp3")