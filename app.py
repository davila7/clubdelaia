import streamlit as st
from streamlit_chat import message
import os
from dotenv import load_dotenv
import requests
import json
import whisper
from audiorecorder import audiorecorder
load_dotenv()

# whisper
model = whisper.load_model('base')

DEFAULT_WIDTH = 80
width = 40
width = max(width, 0.01)
side = max((100 - width) / 2, 0.01)

# Judini
judini_api_key= os.getenv("JUDINI_API_KEY")
agent_id_cap_7= os.getenv("JUDINI_AGENT_ID_CAP_7")
headers = {"Content-Type": "application/json; charset=utf-8", "Authorization": "Bearer "+judini_api_key}

 # Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

def load_chat():
    try:
        # container for chat history
        response_container = st.container()
        # container for text box
        container = st.container()

        with container:
            st.markdown("---", unsafe_allow_html=True)
            st.write('Realiza una pregunta por texto o por audio sobre el capitulo')
            audio = audiorecorder("Grabar audio", "Stop")
            user_audio = ''
            if len(audio) > 0:
                st.audio(audio.tobytes())
                # To save audio to a file:
                wav_file = open("audio.mp3", "wb")
                wav_file.write(audio.tobytes())
            with st.form(key='my_form', clear_on_submit=True):
                # Whisper
                if os.path.exists("audio.mp3"):
                    output = model.transcribe("audio.mp3")
                    user_audio = output['text']
                user_input = st.text_area("", key='input', height=100)
                submit_button = st.form_submit_button(label='Enviar pregunta')

            if submit_button and (user_input or user_audio != ''):
                if os.path.exists("audio.mp3"):
                    os.remove("audio.mp3")
                output, total_tokens, prompt_tokens, completion_tokens = generate_response(agent_id_cap_7, user_input, user_audio)
                st.session_state['past'].append(user_input)
                st.session_state['generated'].append(output)

        if st.session_state['generated']:
            with response_container:
                for i in range(len(st.session_state['generated'])):
                    try:
                        message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
                        message(st.session_state["generated"][i], key=str(i))
                    except json.JSONDecodeError as e:
                        print(f"Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Error: {e}")



def generate_response(agent_id, text_input, audio_input):
    prompt = text_input + ' .'+ audio_input
    st.session_state['messages'].append({"role": "user", "content": prompt})

    data = {
        "messages": [
            {
                "role": "user",
                "content":  prompt
            }
        ]
    }
    url = 'https://playground.judini.ai/api/v1/agent/'+agent_id
    response = requests.post(url, headers=headers, json=data, stream=True)
    token = ''
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            raw_data = chunk.decode('utf-8').replace("data: ", '')
            if raw_data != "[DONE]":
                try:
                    json_object = json.loads(raw_data.strip())
                    token += json_object['data']
                except json.JSONDecodeError as e:
                    print(f"Error al cargar el JSON: {e}")
    response = token
    st.session_state['messages'].append({"role": "assistant", "content": response})

    print(st.session_state['messages'])
    total_tokens = 0
    prompt_tokens = 0
    completion_tokens = 0
    return response, total_tokens, prompt_tokens, completion_tokens


def main():


    st.set_page_config(page_title="El Club de la IA", layout="wide")
    st.title("El Club de la IA")
    st.write("Chatea con nuestro bot Isaac, experto en cada capitulo")

    tabs = ['Cap 7']

    selected_tab = st.sidebar.radio("Selecciona un Capitulo", tabs)
    clear_button = st.sidebar.button("Limpiar conversación", key="clear")
    if selected_tab == "Cap 7":
        _, container, _ = st.columns([side, 47, side])
        VIDEO_DATA = "https://youtu.be/kXwl2KE4C9w"
        container.video(data=VIDEO_DATA)

        load_chat()
        
    st.markdown('Potenciado por [Judini](https://judini.ai)')

if __name__ == "__main__":
    main()