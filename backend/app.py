# from pydub import AudioSegment
# import io
# import librosa
# import soundfile as sf
# import numpy as np
# import re
# from transformers import WhisperProcessor, WhisperForConditionalGeneration
# import torch
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os

# os.environ["TRANSFORMERS_NO_TF"] = "1"
# app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}})


# @app.after_request
# def add_cors_headers(response):
#     response.headers.add("Access-Control-Allow-Origin", "*")
#     response.headers.add("Access-Control-Allow-Headers",
#                          "Content-Type,Authorization")
#     response.headers.add("Access-Control-Allow-Methods",
#                          "GET,POST,PUT,DELETE,OPTIONS")
#     return response


# def read_audio_file(file):
#     if file.filename.lower().endswith('.webm'):
#         seg = AudioSegment.from_file(file, format="webm")
#         wav_io = io.BytesIO()
#         seg.export(wav_io, format="wav")
#         wav_io.seek(0)
#         return sf.read(wav_io)
#     return sf.read(file)


# TARGET_RATE = 16000

# WHISPER_MODEL_NAME = "openai/whisper-small"
# whisper_processor = WhisperProcessor.from_pretrained(WHISPER_MODEL_NAME)
# whisper_model = WhisperForConditionalGeneration.from_pretrained(
#     WHISPER_MODEL_NAME)


# @app.route('/transcribe', methods=['POST', 'OPTIONS'])
# def transcribe():
#     if request.method == "OPTIONS":
#         return add_cors_headers(jsonify({"status": "ok"}))
#     if 'file' not in request.files:
#         return jsonify({"error": "No file provided"}), 400
#     file = request.files['file']
#     try:
#         audio_data, sample_rate = read_audio_file(file)
#     except Exception as e:
#         return jsonify({"error": f"Error reading audio file: {str(e)}"}), 400
#     if sample_rate != TARGET_RATE:
#         audio_data = librosa.resample(
#             audio_data, orig_sr=sample_rate, target_sr=TARGET_RATE)
#     if len(audio_data.shape) > 1:
#         audio_data = audio_data[:, 0]

#     input_features = whisper_processor(
#         audio_data, sampling_rate=TARGET_RATE, return_tensors="pt").input_features

#     previous_prompt = []   
#     N_FRAMES = 3000
#     seek = 0
#     num_frames = input_features.shape[1]
#     lucid_threshold = 0.3

#     if ((seek + N_FRAMES) / num_frames < 1.0) or (seek == 0):
#         decode_prompt = previous_prompt
#     else:
#         lucid_score = (num_frames - seek) / N_FRAMES
#         decode_prompt = [] if lucid_score < lucid_threshold else previous_prompt

#     decode_options = {
#         "temperature": 0.0,
#         "num_beams": 5,
#         "repetition_penalty": 2.0,
#         "no_repeat_ngram_size": 3,
#         "length_penalty": 0.7,
#         "max_length": 512
#     }

#     predicted_ids = whisper_model.generate(input_features, **decode_options)
#     transcription = whisper_processor.batch_decode(
#         predicted_ids, skip_special_tokens=True)[0]


#     return jsonify({"transcription": transcription})


# if __name__ == '__main__':
#     app.run(debug=True)


from pydub import AudioSegment
import io
import librosa
import soundfile as sf
import numpy as np
import torch
import whisper
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from pymongo import MongoClient

load_dotenv()
google_key = os.getenv("GOOGLE_KEY")
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

googleClient = genai.Client(api_key=google_key)

# from userRoutes import userRoutes
# app.register_blueprint(userRoutes, url_prefix='/user')

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
    # client.server_info()
    return "app.py is working"

@app.route("/signup", methods=['POST', 'OPTION'])
def signup():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    # Check if user already exists
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

    # Check if user exists
    user = users_collection.find_one({"email": email})
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "userID": str(user["_id"])}), 200

def read_audio_file(file):
    if file.filename.lower().endswith('.webm'):
        seg = AudioSegment.from_file(file, format="webm")
        wav_io = io.BytesIO()
        seg.export(wav_io, format="wav")
        wav_io.seek(0)
        return sf.read(wav_io)
    return sf.read(file)


TARGET_RATE = 16000

# Load Whisper model
whisper_model = whisper.load_model("base")


@app.route('/transcribe', methods=['POST', 'OPTIONS'])
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

    result = whisper_model.transcribe(temp_wav_path)
    transcription = result["text"]
    
    return jsonify({"transcription": transcription})


def get_summary(text):
    response = googleClient.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"{text}/n give a summary about this coversation, remove weird word, such as random you, response with the format: Transcription: ...  Summary: ... . Don't add any extra word"
    )
    print(response.text)
    return response.text

@app.route('/save_transcription', methods=['POST', 'OPTION'])
def save_transcription():
    if request.method == "OPTIONS":
        return add_cors_headers(jsonify({"status": "ok"}))
    data = request.get_json() or {}
    transcribed_text = data.get("transcription")
    #transcribed_text = "Hello everyone, this is a test transcription. We had a detailed discussion on various topics, but then a weird word randomyou popped up unexpectedly in the middle.  Overall, the conversation was engaging and insightful."

    if not transcribed_text:
        return jsonify({"error": "No transcription provided"}), 400

    try:
        with open("transcription.txt", "w") as f:
            f.write(transcribed_text)
    except Exception as e:
        return jsonify({"error": f"Error saving transcription: {str(e)}"}), 500


    summary = get_summary(transcribed_text)
    print('DONE saving')
    return jsonify({
        "summary": summary
    })

if __name__ == '__main__':
    app.run(debug=True)
