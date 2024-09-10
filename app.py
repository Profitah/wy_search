import openai  # type: ignore
from flask import Flask, request, render_template  # type: ignore
import requests  # type: ignore
from flask_cors import CORS  # type: ignore
import logging
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)

GOOGLE_API_KEY = os.getenv('USER_GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('USER_OPENAI_API_KEY')
CX = os.getenv('USER_CX')

openai.api_key = OPENAI_API_KEY

previous_image_urls = []

def get_search_term(command):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f" '{command}'에'원영'이 포함되어 있으면 '장원영', 없으면 'x'를 반환해."}
            ],
            max_tokens=100,
            temperature=0
        )

        responses = response['choices'][0]['message']['content'].strip()

        if '장원영' in responses:
            return "장원영"
        
        elif responses == 'x':
            return "사진 가져올 필요없음"
        else:
            return "사진 가져올 필요없음"  
        
    except Exception as e:
        app.logger.error(f"OpenAI API 호출 중 오류 발생: {e}")
        return "사진 가져올 필요없음"

def get_image(search_term):
    if search_term == "사진 가져올 필요없음":
        return None

    response = requests.get(
        'https://www.googleapis.com/customsearch/v1',
        params={
            'key': GOOGLE_API_KEY,
            'cx': CX,
            'q': search_term, 
            'searchType': 'image',
            'num': 10
        }
    )

    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        if items:
            for item in items:
                image_url = item['link']
                if image_url not in previous_image_urls:
                    previous_image_urls.append(image_url)
                    return image_url
        app.logger.debug("이미지 검색 결과가 없습니다.")
        return None
    else:
        app.logger.error(f'에러 {response.status_code}')
        return None

@app.route('/', methods=['GET', 'POST'])
def search_image():
    if request.method == 'POST':
        command = request.form.get('command')
        search_term = get_search_term(command)

        if search_term == "사진 가져올 필요없음":
            return render_template('chat_pc.html', error="검색 결과를 찾을 수 없습니다.", command=command)

        image_url = get_image(search_term)
        if image_url:
            return render_template('chat_pc.html', image_url=image_url, command=command)
        else:
            return render_template('chat_pc.html', error="이미지를 찾을 수 없습니다.", command=command)

    return render_template('chat_pc.html')

if __name__ == '__main__':
    app.run(debug=True)