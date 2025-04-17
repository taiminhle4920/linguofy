from pydub import AudioSegment
import io
import librosa
import soundfile as sf
import numpy as np
import torch
from faster_whisper import WhisperModel
from datetime import datetime
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import json


load_dotenv()
google_key = os.getenv("GOOGLE_KEY")
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

googleClient = genai.Client(api_key=google_key)
agent_cache = {}
CACHE_TTL = 360


MONGOUSER = os.getenv("MONGOUSER")
MONGOPASS = os.getenv("MONGOPASS")
mongoURL = f"mongodb+srv://{MONGOUSER}:{MONGOPASS}@cluster0.v1pdg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
bcrypt = Bcrypt()
client = MongoClient(mongoURL)
db = client["LinguofyDB"]
users_collection = db["User"]


@app.after_request
def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers",
                         "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods",
                         "GET,POST,PUT,DELETE,OPTIONS")
    return response


@app.route('/', methods=['GET'])
def test():

    return "app.py is working"


@app.route("/signup", methods=['POST', 'OPTION'])
def signup():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    users_collection.insert_one({"email": email, "password": hashed_pw})

    return jsonify({"message": "User created successfully"}), 201


@app.route("/login", methods=['POST', 'OPTION'])
def login():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    user = users_collection.find_one({"email": email})
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "userID": str(user["_id"])}), 200


TARGET_RATE = 16000


def read_audio_file(file):
    if file.filename.lower().endswith('.webm'):
        seg = AudioSegment.from_file(file, format="webm")
        wav_io = io.BytesIO()
        seg.export(wav_io, format="wav")
        wav_io.seek(0)
        return sf.read(wav_io)
    return sf.read(file)


device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"


model = WhisperModel("base", device=device, compute_type=compute_type)


@app.route('/transcribe', methods=['POST', 'OPTION'])
def transcribe():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    try:
        audio_data, sample_rate = read_audio_file(file)
    except Exception as e:
        return jsonify({"error": f"Error reading audio file: {str(e)}"}), 400

    if sample_rate != TARGET_RATE:
        audio_data = librosa.resample(
            audio_data, orig_sr=sample_rate, target_sr=TARGET_RATE)

    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    temp_wav_path = "temp_audio.wav"
    sf.write(temp_wav_path, audio_data, TARGET_RATE)

    segments, info = model.transcribe(
        temp_wav_path, beam_size=5, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
    transcription = " ".join([segment.text for segment in segments]).strip()

    if device == "cuda":
        torch.cuda.empty_cache()
    return jsonify({"transcription": transcription})


def get_summary(text):
    response = googleClient.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"{text}/n give a summary about this coversation, remove weird word, such as: you, thank you for watching the video,  ..., make the conversation make more sense. Response with the format: Transcription: ...  Summary: ... . Don't add any extra word"
    )

    return response.text


@app.route('/save_transcription', methods=['POST', 'OPTION'])
def save_transcription():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))
    data = request.get_json() or {}
    transcribed_text = data.get("transcription")
    email = data.get("email")
    print('email', email)

    if not transcribed_text:
        return jsonify({"error": "No transcription provided"}), 400

    if not email:
        return jsonify({"error": "No email provided"}), 400

    timestamp = datetime.now().isoformat()
    summary = get_summary(transcribed_text)
    user = users_collection.find_one({"email": email})
    if user:

        if "history" in user and isinstance(user["history"], dict):
            user["history"][timestamp] = summary
            users_collection.update_one(
                {"email": email}, {"$set": {"history": user["history"]}})
            print(user["history"])
        else:

            users_collection.update_one(
                {"email": email}, {"$set": {"history": {timestamp: summary}}})

    return jsonify({"Summary": summary}), 200


@app.route('/get_history', methods=['POST', 'OPTION'])
def get_history():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "No email provided"}), 400

    user = users_collection.find_one({"email": email})
    if user and "history" in user:
        return jsonify({"history": user["history"]}), 200

    return jsonify({"history": {}}), 200


@app.route('/update_history', methods=['PUT'])
def update_history():
    """Update a specific transcription entry."""
    data = request.get_json() or {}
    email = data.get("email")
    timestamp = data.get("timestamp")
    updated_summary = data.get("updated_summary")

    if not email or not timestamp or not updated_summary:
        return jsonify({"error": "Missing data"}), 400

    user = users_collection.find_one({"email": email})
    if user and "history" in user and timestamp in user["history"]:
        user["history"][timestamp] = updated_summary
        users_collection.update_one(
            {"email": email}, {"$set": {"history": user["history"]}})
        return jsonify({"message": "History updated successfully"}), 200

    return jsonify({"error": "Invalid request"}), 400


@app.route('/translate', methods=['POST', 'OPTION'])
def translate():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))
    data = request.get_json() or {}
    transcribed_text = data.get("transcription")
    print(transcribed_text)
    if not transcribed_text:
        return jsonify({"error": "No transcription provided"}), 400

    translation = googleClient.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"{transcribed_text}. /n Translate this to English. No extra text, just translation")

    if translation.text:
        return jsonify({"Translation": translation.text}), 200
    return jsonify({"Translation": "No translation avaiable"}), 400


@app.route('/agenttext', methods=['POST', 'OPTION'])
def agenttext():
    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({"status": "ok"}))

    data = request.get_json()

    if not data or 'prompt' not in data:
        return jsonify({"error": "No prompt provided"}), 400

    prompt = data.get('prompt')
    cache_key = hashlib.md5(prompt.encode('utf-8')).hexdigest()
    current_time = datetime.now()

    if cache_key in agent_cache:
        cached_answer, timestamp = agent_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            print("Returning cached answer")
            return add_cors_headers(jsonify({"Translation": cached_answer})), 200
        else:
            del agent_cache[cache_key]

    cache_data_str = json.dumps({k: v[0] for k, v in agent_cache.items()})

    answer = googleClient.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"Question: {prompt}. Cache: {cache_data_str}.\nUse the cache to help you to answer the question if needed. You are an assistant for the user. Don't send the cache in the answer.Don't yap, answer directly. If the user send additional information for previous answer, then answer it as well."
    )

    if answer.text:
        agent_cache[cache_key] = (answer.text, current_time)
        return jsonify({"answer": answer.text}), 200

    return add_cors_headers(jsonify({"answer": "Unable to provide the answer. Please ask again!"})), 400

@app.route('/agent', methods=['POST', 'OPTIONS'])
def agent():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    try:
        audio_data, sample_rate = read_audio_file(file)
    except Exception as e:
        return jsonify({"error": f"Error reading audio file: {str(e)}"}), 400

    if sample_rate != TARGET_RATE:
        audio_data = librosa.resample(
            audio_data, orig_sr=sample_rate, target_sr=TARGET_RATE)

    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]

    temp_wav_path = "temp_audio.wav"
    sf.write(temp_wav_path, audio_data, TARGET_RATE)

    segments, info = model.transcribe(
        temp_wav_path, beam_size=5, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
    transcription = " ".join([segment.text for segment in segments]).strip()

    cache_key = hashlib.md5(transcription.encode("utf-8")).hexdigest()
    current_time = datetime.now().isoformat()

    if cache_key in agent_cache:
        cached_answer, timestamp = agent_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            print("Returning cached answer")
        else:
            del agent_cache[cache_key]
    

    # cache_data_str = json.dumps(agent_cache)
    cache_data_str = json.dumps({k: v[0] for k, v in agent_cache.items()})
    answer = googleClient.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"Question:{transcription}. Cache:{cache_data_str}./n Use the cache to help you to answer the question if needed. You are an assistant for the user. Don't send the cache in the answer. Don't yap, answer directly. If the user send additional information for previous answer, then answer it as well.",

    )
    if answer.text:
        agent_cache[cache_key] = (answer.text, current_time)
        return jsonify({"answer": answer.text, "question": transcription}), 200
    return jsonify({"answer": "Unable to provide the answer. Please ask again!", "question": transcription}), 400




if __name__ == '__main__':
    app.run(debug=True)
