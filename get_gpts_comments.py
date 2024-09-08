import os
from dotenv import load_dotenv
from openai import OpenAI #openai-1.41.0
from google.cloud import texttospeech
from google.oauth2 import service_account
from pydub import AudioSegment
import pygame
import io
import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler #標準化（平均0、標準偏差1）を行うためのライブラリ
import matplotlib.pyplot as plt



# キー用のファイルの読み込み
load_dotenv('gpt_key.env')

# Google Text_to_Speecによる音声出力
def text_to_speech(input_text):
    # 環境変数からAPIキーのパスを取得
    key_path = os.environ['GOOGLE_TEXT_TO_SPEECH_KEY']

    # 認証情報を取得してクライアントを作成
    credentials = service_account.Credentials.from_service_account_file(key_path)
    client = texttospeech.TextToSpeechClient(credentials=credentials)

    # 音声合成のための入力設定
    synthesis_input = texttospeech.SynthesisInput(text=input_text)

    # 日本語の音声パラメータ設定
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",  # 日本語の音声を指定
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # 出力フォーマットの設定
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # 音声合成リクエストを送信
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # バイナリデータをメモリ上で読み込む
    audio_data = io.BytesIO(response.audio_content)

    # pydubを使ってMP3データを読み込み
    sound = AudioSegment.from_mp3(audio_data)

    # wavフォーマットに変換（pygameはwav形式を扱うため必要）
    wav_data = io.BytesIO()
    sound.export(wav_data, format="wav")
    wav_data.seek(0)

    # pygameで音声を再生
    pygame.mixer.init()
    pygame.mixer.music.load(wav_data)
    pygame.mixer.music.play()

    # 再生が終了するまで待機
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


# DeepLのAPIを使って、翻訳を行う関数
def translate_use_deepl(input_text):
    #キー
    deepl_key = os.environ['DEEPL_KEY']
    API_KEY:str = deepl_key

    params = {
        "auth_key": API_KEY,
        "text": input_text,
        "source_lang": 'EN',
        "target_lang": 'JA',
        "formality": 'more'
    }
    request = requests.post("https://api-free.deepl.com/v2/translate", data=params)
    result = request.json()["translations"][0]["text"]
    return result


#波形データから、統計値を算出する関数
def calc_data():
    #サンプル振動データの生成
    np.random.seed(42) #シードを設定することで、常に同じ乱数を生成することができる
    time = np.arange(0, 500, 0.1) #時間軸
    vibration = np.sin(0.2 * time) + 0.5 * np.random.randn(len(time)) #正常な振動パターン + ノイズ

    #振動データをDataFrameに変換
    data = pd.DataFrame({
        'time': time,
        'vibration': vibration
    })

    #特徴量のスケーリング
    scaler = StandardScaler()
    data['scaled_vibration'] = scaler.fit_transform(data['vibration'].values.reshape(-1,1))

    #グラフの保存
    # fig_x = time
    # fig_y = data['scaled_vibration']
    # plt.plot(fig_x, fig_y)
    # plt.xlabel("time")
    # plt.ylabel("scaled_vibration")
    # plt.savefig('figure.png')

    #特徴量の計算
    data['mean'] = data['scaled_vibration'].rolling(window=50).mean() #rolling(window=20).mean(): 20個単位で、平均を算出する
    data['std_dev'] = data['scaled_vibration'].rolling(window=50).std()
    data['peak'] = data['scaled_vibration'].rolling(window=50).max()

    #下から4行取得
    last_four_rows = data[['mean', 'std_dev', 'peak']].tail(4)

    #行ごとに辞書形式に変換
    summary_list = last_four_rows.to_dict(orient='records')

    #各行を取得
    latest = summary_list[-1]
    second_last = summary_list[-2]
    third_last = summary_list[-3]
    fourth_last = summary_list[-4]

    return latest, second_last, third_last, fourth_last


#ChatGPTを用いて、コメントを出力する関数
def output_gpts_comment(latest, second_last, third_last, fourth_last):
    #キー
    openai_key = os.environ['OPEN_AI_KEY']
    client = OpenAI(api_key = openai_key)

    #要約データをテキスト化
    text_summary = f"""
    4 sensors data summary
    First
    - Mean value: {latest['mean']:.3f}
    - Standard deviation: {latest['std_dev']:.3f}
    - Peak value: {latest['peak']}
    Second
    - Mean value: {second_last['mean']:.3f}
    - Standard deviation: {second_last['std_dev']:.3f}
    - Peak value: {second_last['peak']}
    Third
    - Mean value: {third_last['mean']:.3f}
    - Standard deviation: {third_last['std_dev']:.3f}
    - Peak value: {third_last['peak']}
    Fourth
    - Mean value: {fourth_last['mean']:.3f}
    - Standard deviation: {fourth_last['std_dev']:.3f}
    - Peak value: {fourth_last['peak']}
    Based on these characteristics, please provide an analysis or maintenance recommendation for the machine. Please do not exceed 100 words.
    """

    response = client.chat.completions.create(
        model = "gpt-3.5-turbo-0125",
        messages = [
            {"role": "system", "content": "You are an expert in predictive maintenance for industrial machinery."},
            {"role": "user", "content": text_summary},
        ],
        stream = False, #False: 文章をまとめて出力する、True: 文章を生成のタイミングで出力する
        max_tokens=300
    )

    output_response = response.choices[0].message.content
    return output_response



if __name__ == "__main__":
    latest, second_last, third_last, fourth_last = calc_data()
    # print(f'latest : {latest}')
    # print(f'second_last : {second_last}')
    # print(f'third_last : {third_last}')
    # print(f'fourth_last : {fourth_last}')
    
    output_response = output_gpts_comment(latest, second_last, third_last, fourth_last) #ChatGPT
    result = translate_use_deepl(output_response) #DeepLを使って、翻訳を行う
    print(result)
    text_to_speech(result) #Google Text-to-Speechによる音声出力
