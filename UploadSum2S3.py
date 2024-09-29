import os
import urllib.parse
import json
import boto3
from datetime import datetime, timedelta


def lambda_handler(event, context):
    # TODO implement
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    first_file_key = event['Records'][0]['s3']['object']['key'] #オブジェクトのフルパス
    # URLエンコードされたファイル名をデコードする
    first_file_key = urllib.parse.unquote(first_file_key)
    
    first_file_name = os.path.basename(first_file_key) #ファイル名のみ取得
    print(f'{bucket_name} バケットに、{first_file_name}が作成されました。')
    
    # 判定する時刻のリスト（時分秒）
    target_times = ['〇:〇:〇']
    
    
    
    # JSONファイル名から、年月日時分秒を取得する
    firstDatetime_str = first_file_name.split('.json')[0]
    ## str->datetimeへ変換
    firstDatetime = datetime.strptime(firstDatetime_str, '%Y-%m-%d_%H:%M:%S')
    print(f'firstDatetime: {firstDatetime}')
    
    # 2つ目のjsonファイルを取得する
    ## （課題）12時間前のファイルを取得する際に、保存されている時間がぴったし12時間前ではなかったらどうする？
    secondDatetime = firstDatetime - timedelta(hours=12)
    secondDate = secondDatetime.date()
    secondTime = secondDatetime.time()
    second_file_name = f'{secondDate}_{secondTime}.json'
    second_file_key = f'peak/{second_file_name}'
    print(f'second_file_key: {second_file_key}')
    
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
