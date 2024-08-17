import os
from dotenv import load_dotenv
from openai import OpenAI #openai-1.41.0


if __name__ == "__main__":
    #キーの読み込み
    load_dotenv('gpt_key.env')
    openai_key = os.environ['OPEN_AI_KEY']
    client = OpenAI(api_key = openai_key)

    response = client.chat.completions.create(
        model = "gpt-3.5-turbo-0125",
        messages = [{"role": "user", "content": "Say this is a test"}],
        stream = False, #False: 文章をまとめて出力する、True: 文章を生成のタイミングで出力する
        max_tokens=10
    )

    #出力
    print(response.choices[0].message.content)