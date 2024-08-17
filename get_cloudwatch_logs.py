import boto3
from datetime import datetime, timedelta
import re



if __name__ == "__main__":
    #key用ファイルの読み込み
    key_file = open('key.txt', 'r')
    # key_list[0]: アクセスキー
    # key_list[1]: シークレットキー
    # key_list[2]: リージョン（地域）
    key_list = [line.strip() for line in key_file.readlines()] #改行を削除し、リストに格納

    #AWSの資格情報を設定
    aws_access_key_id = key_list[0]
    aws_secret_access_key = key_list[1]
    region_name = key_list[2]

    #クライアント作成
    client = boto3.client('logs',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region_name)

    log_group_name = '/aws/lambda/CloudWatchLoggerFunction' #ロググループ名
    first_target_date = datetime(2024, 8, 14, 15, 14) #フィルタリングする日付を指定(1つ目)
    second_target_date = first_target_date + timedelta(minutes=30) #フィルタリングする日付を指定(2つ目)

    # ログストリームのリストを取得
    response = client.describe_log_streams(
        logGroupName = log_group_name,
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

    # 「総回数」と「1時間平均」の文字の有無を判定するための変数を用意
    total_value_text = "総回数"
    avg_value_text = "1時間平均"
    #　「総回数」と「1時間平均」の合計値用
    total_value_sum = 0
    avg_value_sum = 0
    # フィルタリングされたログストリームの表示
    for log_stream in filtered_log_streams:
        print(f'\nMessage in log stream: {log_stream}')

        # ログストリーム内のメッセージを取得
        events_response = client.get_log_events(
            logGroupName = log_group_name,
            logStreamName = log_stream,
        )

        #各イベントのメッセージを表示
        for event in events_response['events']:
            #総回数
            if total_value_text in event['message']:
                right_part_total = event['message'].split(total_value_text, 1)[-1]
                
                # 〜正規表現〜
                # [-+]? は、オプションの符号（+ または -）にマッチします。
                # \d* は0個以上の数字にマッチします（整数部分）。
                # \.? はオプションの小数点にマッチします。
                # \d+ は1つ以上の数字にマッチします（小数部分）。
                # (?:...) は非キャプチャグループを作成します。
                # [eE][-+]?\d+ は指数部分（e または E の後にオプションの符号と数字）にマッチします。
                total_value = float(re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', right_part_total)[0])
                # print(f'total_value : {total_value}')
                total_value_sum += total_value
            #1時間平均
            if avg_value_text in event['message']:
                right_part_avg = event['message'].split(avg_value_text, 1)[-1]
                avg_value = float(re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', right_part_avg)[0])
                # print(f'avg_value : {avg_value}')
                avg_value_sum += avg_value
    
    avg_value_sum = avg_value_sum / 2 #前半と後半のデータの平均値
    print(f'total_value_sum : {total_value_sum}')
    print(f'avg_value_sum/2 : {avg_value_sum/2}')