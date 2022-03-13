from pathlib import Path
import pyaudio
from six.moves import queue

from kivy.config import Config
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.properties import StringProperty 
from kivy.uix.boxlayout import BoxLayout

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import threading


# GUI Windowの画面サイズ
Config.set('graphics', 'width', str(1000))
Config.set('graphics', 'height', str(300))

STREAMING_LIMIT = 240000  
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  

LabelBase.register(DEFAULT_FONT, 'ipaexg.ttf')

speech_to_text_list = []
stream_close = False

recordinng_data_dir_path = Path('recording_data')
if not recordinng_data_dir_path.exists():
    recordinng_data_dir_path.mkdir(parents=True)


class TextWidget(Widget):
    text = StringProperty()    

    def __init__(self, **kwargs):
        super(TextWidget, self).__init__(**kwargs)
        self.text = ''
        self.number = 0


    ## 開始ボタンを押したときの処理を行う関数
    def buttonClickedStart(self):        
        t1 = threading.Thread(target=excecute_speech_to_text_streaming, args=(self,))
        t1.start()


    ## 終了ボタンを押したときの処理を行う関数
    def buttonClickedEnd(self):        
        global stream_close
        global speech_to_text_list
        
        stream_close = True
        with open(recordinng_data_dir_path.joinpath('streaming_result.txt'), 'w' ) as file:
            text = '\n'.join(speech_to_text_list)
            file.writelines(text)

        self.text = ''
        speech_to_text_list = []


    def update(self):
        self.text = display_texts(max_n_text=6)
        

class SpeechToTextApp(App):
    def __init__(self, **kwargs):

        super(SpeechToTextApp, self).__init__(**kwargs)
        self.title = 'Speech to Text'    # ウィンドウの名前を変更

    def build(self):
        text_widget = TextWidget()
        return text_widget


## 取得した音声テキストから直近の指定行数文を一つの改行付きの1つのテキストにする関数
def display_texts(max_n_text=5):

    if len(speech_to_text_list) <= max_n_text:
        text = '\n'.join(speech_to_text_list)
    else:
        text = '\n'.join(speech_to_text_list[-max_n_text:])
    
    return text


class ResumableMicrophoneStream:

    def __init__(self, rate, chunk_size):
        
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
    
        self._buff = queue.Queue()                 
        
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._fill_buffer,
        )

        
    def __enter__(self):

        global stream_close
        stream_close = False
        return self

    
    def __exit__(self, type, value, traceback):

        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self._buff.put(None)
        self._audio_interface.terminate()
        global stream_close
        stream_close = True

        
    def _fill_buffer(self, in_data, *args, **kwargs):

        self._buff.put(in_data)
        return None, pyaudio.paContinue

    
    def generator(self):

        global stream_close
        while not stream_close:
            data = []

            chunk = self._buff.get()
            
            if chunk is None:
                return

            data.append(chunk)
            
            # キューがからになるまで繰り返す
            while True:
                try:
                    chunk = self._buff.get(block=False)

                    if chunk is None:
                        return
                    data.append(chunk)

                except queue.Empty:
                    break

            yield b''.join(data)



def listen_print_loop(responses, stream, text_widget):
    
    global stream_close
    global speech_to_text_list

    for response in responses:
        if stream_close:
            break

        if not response.results:
            continue

        result = response.results[0]

        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        if result.is_final:
            speech_to_text_list[-1] = transcript
            stream.last_transcript_was_final = True

        else:
            if len(speech_to_text_list) == 0:
                speech_to_text_list.append(transcript)
            else:
                if stream.last_transcript_was_final:
                    speech_to_text_list.append(transcript)
                else:
                    speech_to_text_list[-1] = transcript

            stream.last_transcript_was_final = False
           
        text_widget.update()
            
    
def excecute_speech_to_text_streaming(text_widget):

    print('Start Speech to Text Streaming')

    client = speech.SpeechClient()
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code='ja-JP',
        max_alternatives=1
    )
    streaming_config = speech.types.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
    with mic_manager as stream:
        
        audio_generator = stream.generator()

        requests = (
            speech.types.StreamingRecognizeRequest(audio_content=content) for content in audio_generator
        )

        responses = client.streaming_recognize(
            streaming_config,
            requests
        )
        
        listen_print_loop(responses, stream, text_widget)

    print('End Speech to Text Streaming')


if __name__ == '__main__':
   SpeechToTextApp().run()

