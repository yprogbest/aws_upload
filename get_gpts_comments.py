import os
from dotenv import load_dotenv
from openai import OpenAI #openai-1.41.0
import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler #標準化（平均0、標準偏差1）を行うためのライブラリ

# キー用のファイルの読み込み
load_dotenv('gpt_key.env')

# DeepLのAPIを使って、翻訳を行う関数
def translate_deepl(input_text):
    #キー
    deepl_key = os.environ['DEEPL_KEY']
    API_KEY:str = deepl_key

    params = {
        "auth_key": API_KEY,
        "text": input_text,
        "source_lang": 'EN',
        "target_lang": 'JA'
    }

    request = requests.post("https://api-free.deepl.com/v2/translate", data=params)
    result = request.json()["translations"][0]["text"]

    return result

#波形データから、統計値を算出する関数
def calc_data():
    #サンプル振動データの生成
    np.random.seed(42) #シードを設定することで、常に同じ乱数を生成することができる
    time = np.arange(0, 100, 0.1) #時間軸
    vibration = np.sin(0.2 * time) + 0.5 * np.random.randn(len(time)) #正常な振動パターン + ノイズ

    #振動データをDataFrameに変換
    data = pd.DataFrame({
        'time': time,
        'vibration': vibration
    })

    #特徴量のスケーリング
    scaler = StandardScaler()
    data['scaled_vibration'] = scaler.fit_transform(data['vibration'].values.reshape(-1,1))

    #特徴量の計算
    data['mean'] = data['scaled_vibration'].rolling(window=20).mean() #rolling(window=20).mean(): 20個単位で、平均を算出する
    data['std_dev'] = data['scaled_vibration'].rolling(window=20).std()
    data['peak'] = data['scaled_vibration'].rolling(window=20).max()

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
    Based on these characteristics, please provide an analysis or maintenance recommendation for the machine.
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
    result = translate_deepl(output_response) #DeepLを使って、翻訳を行う
    print(result)


if __name__ == "__main__":
    latest, second_last, third_last, fourth_last = calc_data()
    print(f'latest : {latest}')
    print(f'second_last : {second_last}')
    print(f'third_last : {third_last}')
    print(f'fourth_last : {fourth_last}')
    # output_gpts_comment(latest, second_last, third_last, fourth_last)