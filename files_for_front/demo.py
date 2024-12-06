import streamlit as st
import requests
from streamlit_chat import message
import speech_recognition as sr

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

# 초기 상태 설정
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
        message(f"Error: Message at index {i} is missing required keys.", is_user=False, key=f"message_{i}")

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("음성 인식 시작됨... 마이크에 대고 말해 주세요.")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language="ko-KR")
            return text
        except sr.UnknownValueError:
            return "음성을 인식할 수 없습니다."
        except sr.RequestError:
            return "음성 인식 서비스를 사용할 수 없습니다."

# 음성 인식 후 처리 함수
def handle_speech_input():
    text = recognize_speech()  # 음성 인식 결과
    if text:
        st.session_state['speech_input'] = text  # 음성 인식 결과를 `speech_input`에 저장
        st.session_state['input_changed'] = True  # 입력이 변경되었음을 표시

# 초기 메시지 상태 설정
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# 사용자 입력 처리
with st.container():
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("User Input:", key="user_input")
    with col2:
        if st.button("🎤"):
            handle_speech_input()  # 음성 인식 처리

# 음성 인식 후 메시지 확인
if 'input_changed' in st.session_state and st.session_state['input_changed']:
    # 음성 인식 결과 메시지 출력
    st.session_state.messages.append({"data": st.session_state['speech_input'], "is_user": True})  # 사용자 메시지
    st.session_state.messages.append({"data": f"음성 인식 결과: {st.session_state['speech_input']} 맞나요?", "is_user": False})  # 봇의 확인 메시지
    st.session_state['input_changed'] = False  # 변경 상태 초기화

# 확인 메시지 처리 (사용자가 '맞아요' 또는 '아니요'로 응답)
if len(st.session_state.messages) > 1 and "맞나요?" in st.session_state.messages[-1]["data"]:
    confirm_input = st.text_input("확인: '맞아요' 또는 '아니요'로 답해주세요", key="confirmation_input")

    if confirm_input.lower() == "맞아요":
        st.session_state.messages.append({"data": "확인되었습니다! 음성 인식이 맞습니다.", "is_user": False})
    elif confirm_input.lower() == "아니요":
        st.session_state.messages.append({"data": "다시 시도해주세요. 음성 인식이 잘못되었습니다.", "is_user": False})
