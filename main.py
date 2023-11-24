import streamlit as st

st.set_page_config(
    page_title="Drowsiness Detection | SixthSens AI",
    page_icon="https://learnopencv.com/wp-content/uploads/2017/12/favicon.png",
    layout="wide",  # centered, wide
    initial_sidebar_state="expanded",
)

hide_streamlit_style = """
            <style>
            .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
            .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
            .viewerBadge_text__1JaDK {display: none;}
            MainMenu {visibility: hidden;}
            header { visibility: hidden; }
            footer {visibility: hidden;}
            #GithubIcon {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

import os
import av
import threading

from streamlit_webrtc import VideoHTMLAttributes, webrtc_streamer

from audio_handling import AudioFrameHandler
from drowsy_detection import VideoFrameHandler

# Define the audio file to use.
alarm_file_path = os.path.join("audio", "wake_up.wav")

st.title("Drowsiness Detection!!!🥱😪😴")

with st.container():
    c1, c2 = st.columns(spec=[1, 1])
    with c1:
        WAIT_TIME = st.slider("Seconds to wait before sounding alarm:", 0.0, 5.0, 1.0, 0.25)

    with c2:
        EAR_THRESH = st.slider("Eye Aspect Ratio threshold:", 0.0, 0.4, 0.18, 0.01)

thresholds = {
    "EAR_THRESH": EAR_THRESH,
    "WAIT_TIME": WAIT_TIME,
}


class VideoHandlerResource:
    def __init__(self):
        self.video_handler = VideoFrameHandler()

    def close(self):
        # Add any necessary cleanup code here
        pass

    def read(self):
        return self.video_handler

class AudioHandlerResource:
    def __init__(self):
        self.audio_handler = AudioFrameHandler(sound_file_path=alarm_file_path)

    def close(self):
        # Add any necessary cleanup code here
        pass

    def read(self):
        return self.audio_handler

video_handler = st.cache_resource(VideoHandlerResource)().read()
audio_handler = st.cache_resource(AudioHandlerResource)().read()

lock = threading.Lock()  # For thread-safe access & to prevent race-condition.
shared_state = {"play_alarm": False}

def video_frame_callback(frame: av.VideoFrame):
    frame = frame.to_ndarray(format="bgr24")  # Decode and convert frame to RGB

    frame, play_alarm = video_handler.process(frame, thresholds)  # Process frame
    with lock:
        shared_state["play_alarm"] = play_alarm  # Update shared state
    return av.VideoFrame.from_ndarray(frame, format="bgr24")  # Encode and return BGR frame

def audio_frame_callback(frame: av.AudioFrame):
    with lock:  # access the current “play_alarm” state
        play_alarm = shared_state["play_alarm"]

    new_frame: av.AudioFrame = audio_handler.process(frame, play_sound=play_alarm)
    return new_frame

ctx = webrtc_streamer(
    key="drowsiness-detection",
    video_frame_callback=video_frame_callback,
    audio_frame_callback=audio_frame_callback,
    rtc_configuration={"iceServers": [
        {
            "urls": "turn:a.relay.metered.ca:80?transport=tcp",
            "username": "9d79830e9a30b210d0582c23",
            "credential": "6TzT7r9tBsdKHdMD",
        },
        {
            "urls": "turn:a.relay.metered.ca:443?transport=tcp",
            "username": "9d79830e9a30b210d0582c23",
            "credential": "6TzT7r9tBsdKHdMD",
        },

    ]},  # Add this to config for cloud deployment.
    media_stream_constraints={"video": {"height": {"ideal": 480}}, "audio": True},
    video_html_attrs=VideoHTMLAttributes(autoPlay=True, controls=False, muted=False),
)
