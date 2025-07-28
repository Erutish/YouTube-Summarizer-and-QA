#pip install youtube_transcript_api
#pip install deepmultilingualpunctuation
#pip install openai
#  python -m venv venv
#pip install -r requirements.txt
#$env:OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


from youtube_transcript_api import YouTubeTranscriptApi
from deepmultilingualpunctuation import PunctuationModel
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")

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
    transcript_joined=" ".join([i["text"] for i in raw])
    return transcript_joined

def punctuate_text(text):
    model = PunctuationModel()
    return model.restore_punctuation(text)

def summarize_text(client, text):
    prompt = f"Summarize this text. Do not miss any keywords:\n\n{text}"
    chat_completion = client.chat.completions.create(
        model="gpt-4.1-nano",  # Or 'gpt-4' if you have access
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=256,
    )
    return chat_completion.choices[0].message.content

def answer_question(client, text, question):
    prompt = f"Based on the following transcript, answer the question:\n\nTranscript:\n{text}\n\nQuestion: {question}"
    chat_completion = client.chat.completions.create(
        model="gpt-4.1-nano",  # Or 'gpt-4' if you have access
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=256,
    )
    return chat_completion.choices[0].message.content

def main():
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set. Please set it before running the script.")
    client = OpenAI(api_key=api_key)
    video_url = input("Enter YouTube video URL: ")
    print("Fetching transcript...")
    transcript = fetch_transcript(video_url)
    print("Restoring punctuation (this may take a moment)...")
    transcript_punctuated = punctuate_text(transcript)

    print("\nChoose an option:")
    print("1. Summarize the transcript")
    print("2. Ask a question about the video")
    choice = input("Enter 1 or 2: ")

    if choice == "1":
        summary = summarize_text(client, transcript_punctuated)
        print("\nSummary:\n", summary)
    elif choice == "2":
        question = input("Enter your question: ")
        answer = answer_question(client, transcript_punctuated, question)
        print("\nAnswer:\n", answer)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main() 