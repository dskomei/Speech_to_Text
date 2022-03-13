from pathlib import Path
import subprocess
import os
import wave
import numpy as np
import scipy.signal
import struct


def convert_from_m4a_to_wav(target_file_path, output_file_path):

    if target_file_path.suffix == '.m4a':
        
        if output_file_path.exists():
            os.remove(output_file_path)
        
        subprocess.call([
            'ffmpeg',
            '-i',
            target_file_path.__str__(), 
            output_file_path.__str__()
        ])

        
def readWav(filename):
    """
    wavファイルを読み込んで，データ・サンプリングレートを返す関数
    """
    wf = wave.open(filename)
    fs = wf.getframerate()
    # -1 ~ 1までに正規化した信号データを読み込む
    data = np.frombuffer(wf.readframes(wf.getnframes()),dtype="int16")/32768.0
    return (data,fs)


def upsampling(conversion_rate,data,fs):
    """
    アップサンプリングを行う．
    入力として，変換レートとデータとサンプリング周波数．
    アップサンプリング後のデータとサンプリング周波数を返す．
    """
    # 補間するサンプル数を決める
    interpolationSampleNum = conversion_rate-1

    # FIRフィルタの用意をする
    nyqF = fs/2.0     # 変換後のナイキスト周波数
    cF = (fs/2.0-500.)/nyqF             # カットオフ周波数を設定（変換前のナイキスト周波数より少し下を設定）
    taps = 511                          # フィルタ係数（奇数じゃないとだめ）
    b = scipy.signal.firwin(taps, cF)   # LPFを用意

    # 補間処理
    upData = []
    for d in data:
        upData.append(d)
        # 1サンプルの後に，interpolationSampleNum分だけ0を追加する
        for i in range(interpolationSampleNum):
            upData.append(0.0)

    # フィルタリング
    resultData = scipy.signal.lfilter(b,1,upData)
    return (resultData,fs*conversion_rate)
        

def downsampling(conversion_rate,data,fs):
    """
    ダウンサンプリングを行う．
    入力として，変換レートとデータとサンプリング周波数．
    ダウンサンプリング後のデータとサンプリング周波数を返す．
    """
    # 間引くサンプル数を決める
    decimationSampleNum = conversion_rate-1

    # FIRフィルタの用意をする
    nyqF = fs/2.0             # 変換後のナイキスト周波数
    cF = (fs/conversion_rate/2.0-500.)/nyqF     # カットオフ周波数を設定（変換前のナイキスト周波数より少し下を設定）
    taps = 511                                  # フィルタ係数（奇数じゃないとだめ）
    b = scipy.signal.firwin(taps, cF)           # LPFを用意

    #フィルタリング
    data = scipy.signal.lfilter(b,1,data)

    #間引き処理
    downData = []
    for i in range(0,len(data),decimationSampleNum+1):
        downData.append(data[i])

    return (downData,fs/conversion_rate)


def writeWav(filename,data,fs):
    """
    入力されたファイル名でwavファイルを書き出す．
    """
    # データを-32768から32767の整数値に変換
    data = [int(x * 32767.0) for x in data]
    #バイナリ化
    binwave = struct.pack("h" * len(data), *data)
    wf = wave.Wave_write(filename)
    wf.setparams((
        1,                          # channel
        2,                          # byte width
        fs,                         # sampling rate
        len(data),                  # number of frames
        "NONE", "not compressed"    # no compression
        ))
    wf.writeframes(binwave)
    wf.close()