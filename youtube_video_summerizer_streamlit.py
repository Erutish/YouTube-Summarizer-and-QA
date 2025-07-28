import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from deepmultilingualpunctuation import PunctuationModel
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

def get_video_id(url_link):
    if "watch?v=" in url_link:
        return url_link.split("watch?v=")[-1]
    elif "youtu.be/" in url_link:
        return url_link.split("youtu.be/")[-1]
    else:
        return url_link  # fallback if only ID is given

def fetch_transcript(video_url):
    video_id = get_video_id(video_url)
    transcript = YouTubeTranscriptApi().fetch(video_id)
    raw = transcript.to_raw_data()  # returns List[Dict]
    transcript_joined = " ".join([i["text"] for i in raw])
    return transcript_joined

def punctuate_text(text):
    model = PunctuationModel()
    return model.restore_punctuation(text)

def summarize_text(client, text):
    prompt = f"Summarize this text. Do not miss any keywords:\n\n{text}"
    chat_completion = client.chat.completions.create(
        model="gpt-4.1-nano",  # Or 'gpt-4' if you have access
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=256,
    )
    return chat_completion.choices[0].message.content

def answer_question(client, text, question):
    prompt = f"Based on the following transcript, answer the question:\n\nTranscript:\n{text}\n\nQuestion: {question}"
    chat_completion = client.chat.completions.create(
        model="gpt-4.1-nano",  # Or 'gpt-4' if you have access
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=256,
    )
    return chat_completion.choices[0].message.content

def main():
    st.set_page_config(page_title="YouTube Video Summarizer & Q&A", page_icon="🎬", layout="centered")
    st.markdown("""
        <style>
        body, .stApp {background-color: #f5f7fa !important;}
        .big-title {font-size:2.5rem; font-weight:700; color:#FF4B4B; text-align:center; margin-bottom:0.5em;}
        .subtitle {font-size:1.2rem; color:#333; text-align:center; margin-bottom:2em;}
        .stButton>button {background-color:#FF4B4B; color:white; font-weight:bold;}
        .stSelectbox>div>div>div>div {font-weight:bold;}
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="big-title">YouTube Video Summarizer & Q&A</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Paste a YouTube video URL, and get a summary or ask a question about the content!</div>', unsafe_allow_html=True)

    api_key = st.secrets["OPENAI_API_KEY"]
    if not api_key:
        st.error("OPENAI_API_KEY environment variable not set. Please set it before running the app.")
        return
    client = OpenAI(api_key=api_key)

    st.markdown("### 1. Enter YouTube Video URL")
    video_url = st.text_input("YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")

    # Automatically fetch transcript and punctuation when video_url is entered
    transcript = st.session_state.get("transcript", None)
    transcript_punctuated = st.session_state.get("transcript_punctuated", None)
    if video_url:
        if (not transcript) or (st.session_state.get("last_url", None) != video_url):
            with st.spinner("Fetching transcript and restoring punctuation..."):
                try:
                    transcript = fetch_transcript(video_url)
                    transcript_punctuated = punctuate_text(transcript)
                    st.session_state["transcript"] = transcript
                    st.session_state["transcript_punctuated"] = transcript_punctuated
                    st.session_state["last_url"] = video_url
                    st.success("Transcript fetched and punctuation restored!")
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state["transcript"] = None
                    st.session_state["transcript_punctuated"] = None
                    st.session_state["last_url"] = None

    transcript_punctuated = st.session_state.get("transcript_punctuated", None)
    if transcript_punctuated:
        st.markdown("---")
        st.markdown("### 2. Choose an Action")
        option = st.selectbox("What would you like to do?", ("Summarize the transcript", "Ask a question about the video"))
        if option == "Summarize the transcript":
            if st.button("Summarize", use_container_width=True):
                with st.spinner("Summarizing..."):
                    try:
                        summary = summarize_text(client, transcript_punctuated)
                        st.markdown("#### 📝 Summary:")
                        st.success(summary)
                    except Exception as e:
                        st.error(f"Error summarizing: {e}")
        elif option == "Ask a question about the video":
            question = st.text_input("Enter your question:", placeholder="e.g. What are the main points discussed?")
            if st.button("Get Answer", use_container_width=True) and question:
                with st.spinner("Answering..."):
                    try:
                        answer = answer_question(client, transcript_punctuated, question)
                        st.markdown("#### 💡 Answer:")
                        st.success(answer)
                    except Exception as e:
                        st.error(f"Error answering question: {e}")

if __name__ == "__main__":
    main() 
