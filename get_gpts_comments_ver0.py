import openai #openai-0.28.0


if __name__ == "__main__":
    #key用ファイルの読み込み
    key_file = open('gpt_key.txt', 'r')
    key_list = [line.strip() for line in key_file.readlines()] #改行を削除し、リストに格納

    #APIキーの設定
    openai.api_key = key_list[0]

    # 利用可能なモデルを取得
    # models = openai.Model.list()
    # for model in models['data']:
    #     print(f'Model ID : {model['id']}, Object : {model['object']}')

    #GPTによる応答生成
    prompt = "What your favorite food?"
    response = openai.ChatCompletion.create(
                        model = "gpt-3.5-turbo-0125",
                        messages = [
                            {"role": "system", "content": "You are a helpful assistant who provides explanations and insights based on technical data."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0,
                        max_tokens=20
                    )

    # 応答の表示
    text = response['choices'][0]['message']['content']
    print(text)

