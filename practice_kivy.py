from kivy.config import Config
# 画面サイズを決める
Config.set('graphics', 'width', str(1000))
Config.set('graphics', 'height', str(300))

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.properties import StringProperty 

LabelBase.register(DEFAULT_FONT, 'ipaexg.ttf')


class TextWidget(Widget):
    text = StringProperty()    

    def __init__(self, **kwargs):
        super(TextWidget, self).__init__(**kwargs)
        self.text = ''
        self.number = 0


    ## 開始ボタンを押したときの処理を行う関数
    def buttonClickedStart(self):        
        self.text = 'やったるぜぃ'


    ## 終了ボタンを押したときの処理を行う関数
    def buttonClickedEnd(self):        
        self.text = ''



class SpeechToTextApp(App):
    def __init__(self, **kwargs):

        super(SpeechToTextApp, self).__init__(**kwargs)
        self.title = 'Speech to Text'    # ウィンドウの名前を変更

    def build(self):
        text_widget = TextWidget()
        return text_widget



if __name__ == '__main__':
   SpeechToTextApp().run()

