import boto3
import json
from datetime import datetime, timedelta
import re
import os
from dotenv import load_dotenv


#CloudWatchのログストリームから指定した値を取得
def get_cloudwatch_value(input_txt, log_event):
    right_part = log_event['message'].split(input_txt, 1)[-1] #input_txtより右の文字を取得
    # 〜正規表現〜
    # [-+]? は、オプションの符号（+ または -）にマッチします。
    # \d* は0個以上の数字にマッチします（整数部分）。
    # \.? はオプションの小数点にマッチします。
    # \d+ は1つ以上の数字にマッチします（小数部分）。
    # (?:...) は非キャプチャグループを作成します。
    # [eE][-+]?\d+ は指数部分（e または E の後にオプションの符号と数字）にマッチします。
    message_value = float(re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', right_part)[0])
    return message_value


if __name__ == "__main__":
    # ID ※外部から取得
    id_name = "ma_id"
    id_value = "1234-5678"
    first_target_date = datetime(2024, 8, 24, 12, 5) #フィルタリングする日付を指定(1つ目) #※外部から取得する
    second_target_date = first_target_date + timedelta(minutes=30) #フィルタリングする日付を指定(2つ目)



    # #key用ファイルの読み込み
    load_dotenv('key.env')
    aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
    aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
    region_name = os.environ['REGION_NAME']
    log_group_path = os.environ['LOG_GROUP_PATH']
    #クライアント作成
    client = boto3.client('logs',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region_name)

    # ログストリームのリストを取得
    response = client.describe_log_streams(
        logGroupName = log_group_path,
        orderBy = 'LastEventTime', # 最後のイベント時間でソート
        descending = True # 新しい順に並べる
    )

    # 指定日時に一致するログストリームをフィルタリング
    filtered_log_streams = []
    for stream in response['logStreams']:
        creation_time = datetime.fromtimestamp(stream['creationTime'] / 1000) #ログストリームの作成時刻(unix時刻->datetime)
        creation_time = creation_time.replace(second=0, microsecond=0) #秒以下を切り捨てる
        #1つ目のログストリームを取得するための条件式
        first_condition = (creation_time >= first_target_date) and (creation_time <= first_target_date + timedelta(minutes=1))
        #2つ目のログストリームを取得するための条件式
        second_condition = (creation_time >= second_target_date) and (creation_time <= second_target_date + timedelta(minutes=1))
        if first_condition or second_condition:
            filtered_log_streams.append(stream['logStreamName'])


    # IDのパターン（正規表現） CloudWatchからIDを抽出するために必要
    id_value_pattern = r"'([a-zA-Z0-9\-]+)'"

    #「総回数」と「1時間平均」の文字の有無を判定するための変数を用意
    total_value_text = "総回数"
    avg_value_text = "1時間平均"

    #　「総回数」と「1時間平均」の合計値用
    total_value_sum = 0
    avg_value_sum = 0

    id_match_flag = False
    # フィルタリングされたログストリームの表示
    for log_stream in filtered_log_streams:
        # print(f'\nMessage in log stream: {log_stream}')
        # ログストリーム内のメッセージを取得
        events_response = client.get_log_events(
            logGroupName = log_group_path,
            logStreamName = log_stream,
        )
        #各イベントのメッセージを取得
        for event in events_response['events']:
            message = event['message']
            if id_name in message:
                id_match = re.search(id_value_pattern, message) #正規表現でma_idの値を取得
                ma_id = id_match.group(1) #1番目にマッチした部分を返す
                if ma_id == id_value:
                    id_match_flag = True

            if id_match_flag == True:
                #総回数
                if total_value_text in message:
                    total_value = get_cloudwatch_value(total_value_text, event)
                    total_value_sum += total_value
                #1時間平均
                if avg_value_text in message:
                    avg_value = get_cloudwatch_value(avg_value_text, event)
                    avg_value_sum += avg_value

    print(id_match_flag)
    if id_match_flag == True:
        avg_value_sum = avg_value_sum / 2 #1つ目のストリームと2つ目のストリームのデータの平均値
        print(f'total_value_sum : {total_value_sum}')
        print(f'avg_value_sum : {avg_value_sum}')