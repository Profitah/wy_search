import openai  # type: ignore
from flask import Flask, request, render_template  # type: ignore
import requests  # type: ignore
from flask_cors import CORS  # type: ignore
import os

app = Flask(__name__)

#cors 에러 해결을 위한 코드
CORS(app)

# # 환경 변수에서 Google, OpenAI API 키, 검색 엔진 ID 가져오기
GOOGLE_API_KEY = os.getenv('USER_GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('USER_OPENAI_API_KEY')
CX = os.getenv('USER_CX')

openai.api_key = OPENAI_API_KEY 

# 이전에 반환된 이미지 URL을 저장하여 중복된 이미지가 반환되지 않도록 하는 리스트
previous_image_urls = []

# 키워드에 따라 반환 값이 달라지는 함수
def keyword_check(command):
    if '원영' in command and '사진' in command:
        return '장원영'
    else:
        return get_search_term(command)

# 반환된 값을 통해 api에게 답을 요청하는 함수
def get_search_term(command):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"{command}"},
            ],
            max_tokens=400, # max_tokens를 400으로 수정
            temperature=0.75, # temperature를 0.75으로 수정
        )

        responses = response['choices'][0]['message']['content'].strip()
        return responses

    except Exception as e:
        return f"OpenAI에서 응답을 가져올 수 없습니다: {str(e)}"

# 반환값 '장원영'을 이용해 이미지를 가져오는 함수
def get_image(search_term):
    if "OpenAI에서 응답을 가져올 수 없습니다" in search_term:
        return None

    if search_term != "장원영":
        return None

    try:
        response = requests.get(
            'https://www.googleapis.com/customsearch/v1',
            params={
                'key': GOOGLE_API_KEY,
                'cx': CX,
                'q': search_term.strip(),
                'searchType': 'image',
                'num': 10
            }
        )
        # 응답이 성공하면 이미지 URL을 반환
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if items:
                for item in items:
                    image_url = item['link']
                    if image_url not in previous_image_urls:
                        previous_image_urls.append(image_url)
                        return image_url
                
                # 더 이상 반환할 이미지가 없을 때
                return get_image(search_term) #재귀 호출을 사용해 다시 get요청을 보내고, 다른 이미지를 찾음. 구글애서 이미지를 찾을 수 없을 때까지 반복
            else:
                print(f"Google API 요청 실패: {response.status_code}, {response.text}")
                return None

    except requests.RequestException as e:
        print(f"Google API 요청 중 오류 발생: {str(e)}")
        return None


# 라우트 함수 정의.  get, post 메소드 사용
@app.route('/', methods=['GET', 'POST'])
# 이미지를 어플리케이션 층으로 가져오는 함수
def search_image(): 
    if request.method == 'POST': 
        command = request.form.get('command')
        search_term = keyword_check(command) 

        # 이미지 검색 로직에서 오류 발생 시 오류 메시지를 더 자세히 표시하도록 개선
        if "OpenAI에서 응답을 가져올 수 없습니다" in search_term: #openAI에서 응답을 가져올 수 없을 때
            return render_template('chat_pc.html', error=search_term, command=command)

        if search_term != "장원영": # 장원영 키워드를 반환받지 못했을 때
            return render_template('chat_pc.html', error=search_term, command=command)

        image_url = get_image(search_term) 
        if image_url: # 이미지가 반환되었을 때
            return render_template('chat_pc.html', image_url=image_url, command=command)
        else: # 이미지를 찾을 수 없을 때 (예 : 모든 이미지를 반환 해 더 이상 반환할 이미지가 없을 때)
            return render_template('chat_pc.html', error=f"이미지를 찾을 수 없습니다: {search_term}", command=command)

    return render_template('chat_pc.html')# Google API 요청을 실패했을 때

if __name__ == '__main__':
    app.run(debug=True)