from pydub import AudioSegment
import io
import librosa
import soundfile as sf
import numpy as np
import re
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

os.environ["TRANSFORMERS_NO_TF"] = "1"
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.after_request
def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers",
                         "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods",
                         "GET,POST,PUT,DELETE,OPTIONS")
    return response


def read_audio_file(file):
    if file.filename.lower().endswith('.webm'):
        seg = AudioSegment.from_file(file, format="webm")
        wav_io = io.BytesIO()
        seg.export(wav_io, format="wav")
        wav_io.seek(0)
        return sf.read(wav_io)
    return sf.read(file)


TARGET_RATE = 16000

WHISPER_MODEL_NAME = "openai/whisper-small"
whisper_processor = WhisperProcessor.from_pretrained(WHISPER_MODEL_NAME)
whisper_model = WhisperForConditionalGeneration.from_pretrained(
    WHISPER_MODEL_NAME)


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

    input_features = whisper_processor(
        audio_data, sampling_rate=TARGET_RATE, return_tensors="pt").input_features

    previous_prompt = []   
    N_FRAMES = 3000
    seek = 0
    num_frames = input_features.shape[1]
    lucid_threshold = 0.3

    if ((seek + N_FRAMES) / num_frames < 1.0) or (seek == 0):
        decode_prompt = previous_prompt
    else:
        lucid_score = (num_frames - seek) / N_FRAMES
        decode_prompt = [] if lucid_score < lucid_threshold else previous_prompt

    decode_options = {
        "temperature": 0.0,
        "num_beams": 5,
        "repetition_penalty": 2.0,
        "no_repeat_ngram_size": 3,
        "length_penalty": 0.7,
        "max_length": 512
    }

    predicted_ids = whisper_model.generate(input_features, **decode_options)
    transcription = whisper_processor.batch_decode(
        predicted_ids, skip_special_tokens=True)[0]


    return jsonify({"transcription": transcription})


if __name__ == '__main__':
    app.run(debug=True)
