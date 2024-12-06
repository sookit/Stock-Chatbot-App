
import streamlit as st
import requests
from streamlit_chat import message


# API 호출 함수
def send_query_to_api(query, time_limit):
    try:
        response = requests.post('http://192.168.1.101:5000/api/query', json={"query": query, "time_limit": int(time_limit)})
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def send_chat_to_api(analysis_query):
    try:
        response = requests.post('http://192.168.1.101:5000/api/chat', json={"analysis_query": analysis_query})
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

#초기상태 설정
if 'step' not in st.session_state:
    st.session_state['step'] = 'query_input'
    st.session_state['query'] = ""
    st.session_state['past'] = []
    st.session_state['generated'] = []
    st.session_state['messages'] = [{'data': "What keyword would you like to search for?", 'is_user': False}]  # 초기 메시지 추가

# 입력 처리 함수
def on_input_change():
    user_input = st.session_state.user_input.strip()

    if st.session_state.step == 'query_input':
        st.session_state['query'] = user_input
        st.session_state.messages.append({"data": user_input, "is_user": True})  # 사용자 메시지 추가
        st.session_state.messages.append({"data": "Enter the time limit for crawling (in seconds):", "is_user": False})  # 봇의 응답
        st.session_state.step = 'time_limit'

    elif st.session_state.step == 'time_limit':
        try:
            st.session_state.messages.append({"data": user_input, "is_user": True})  # 사용자 입력 추가
            time_limit = int(user_input)
            api_response = send_query_to_api(st.session_state['query'], time_limit)
            st.session_state.messages.append({"data": f"Server response: {api_response}", "is_user": False})  # 봇의 응답
            st.session_state.messages.append({"data": "Enter your analysis query:", "is_user": False})  # 봇의 응답
            st.session_state.step = 'analysis_query'
        except ValueError:
            st.session_state.messages.append({"data": "Please enter a valid number for the time limit.", "is_user": False})  # 봇의 응답

    elif st.session_state.step == 'analysis_query':
        st.session_state.messages.append({"data": user_input, "is_user": True})  # 사용자 입력 추가
        api_response = send_chat_to_api(user_input)
        st.session_state.messages.append({"data": f"Server response: {api_response}", "is_user": False})  # 봇의 응답
        st.session_state.step = 'query_input'

    st.session_state.user_input = ""

# 메시지 삭제 함수
def on_del_btn():
    st.session_state['messages'] = []
    st.session_state['step'] = 'query_input'

# UI 구성
st.title("STOCK")

# 대화 기록 표시
for i, msg in enumerate(st.session_state['messages']):
    # 메시지가 `data`와 `is_user`를 포함하는지 확인하고, 이를 기준으로 출력
    if 'data' in msg and 'is_user' in msg:
        message(msg['data'], is_user=msg['is_user'], key=f"message_{i}")
    else:
        print(f"Error: Message at index {i} is missing required keys.")



import speech_recognition as sr

# 음성 인식 함수
def recognize_speech():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("음성 인식 시작됨... 마이크에 대고 말해 주세요.")
        
        # 음성 인식 시작
        audio = recognizer.listen(source)
        try:
            # 음성을 텍스트로 변환
            text = recognizer.recognize_google(audio, language="ko-KR")
            return text
        except sr.UnknownValueError:
            return "음성을 인식할 수 없습니다."
        except sr.RequestError:
            return "음성 인식 서비스를 사용할 수 없습니다."


# 입력 필드와 음성 인식 버튼
with st.container():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.text_input("User Input:", on_change=on_input_change, key="user_input")
    with col2:
        if st.button("🎤"):
            text = recognize_speech()  # 음성 인식 결과
            st.session_state.user_input = text  # 음성 인식 결과를 입력값으로 설정
            on_input_change()  # API 요청 실행