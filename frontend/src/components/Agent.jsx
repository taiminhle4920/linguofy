import React, { useState, useRef } from 'react';
import './Agent.css';
import Navbar from './Navbar';

const Agent = () => {
    const [recording, setRecording] = useState(false);
    const [transcription, setTranscription] = useState('');
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    // Start recording using the MediaRecorder API
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            audioChunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorderRef.current.onstop = handleRecordingStop;
            mediaRecorderRef.current.start();
            setRecording(true);
        } catch (error) {
            console.error('Error accessing microphone:', error);
        }
    };

    // Stop recording and trigger sending the audio to the server
    const stopRecording = () => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
            setRecording(false);
        }
    };

    // Called when recording stops; compiles audio data and sends it to the server
    const handleRecordingStop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudioToServer(audioBlob, 'webm');
    };

    // Function to send the audio blob to the backend server
    const sendAudioToServer = async (audioBlob, extension) => {
        console.log("Sending blob to server, size:", audioBlob.size, "Extension:", extension);
        const formData = new FormData();
        formData.append("file", audioBlob, `recording.${extension}`);

        try {
            const response = await fetch("http://127.0.0.1:5000/agent", {
                method: "POST",
                body: formData,
            });
            console.log("Response received from backend:", response);
            const data = await response.json();
            if (data.Translation) {
                console.log("Translation received:", data.Translation);
                setTranscription(data.Translation);
            } else {
                console.log("No translation in response:", data);
            }
        } catch (error) {
            console.error("Error sending audio to server:", error);
        }
    };

    // Toggle recording on button click
    const handleButtonClick = () => {
        if (recording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    return (
        <div className="agent-container">
            <div className="agent-transcription">
                <h2>Server Response:</h2>
                <p>{transcription}</p>
            </div>
            <div className="agent-footer">
                <button
                    className={`agent-button ${recording ? 'recording' : ''}`}
                    onClick={handleButtonClick}
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="32"
                        height="32"
                        fill="currentColor"
                        viewBox="0 0 16 16"
                    >
                        <path d="M8 11a3 3 0 0 0 3-3V3a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z" />
                        <path d="M5 8.5a.5.5 0 0 1 1 0v2a.5.5 0 0 1-1 0v-2z" />
                        <path d="M10 8.5a.5.5 0 0 1 1 0v2a.5.5 0 0 1-1 0v-2z" />
                        <path d="M8 14a3 3 0 0 0 3-3H5a3 3 0 0 0 3 3z" />
                    </svg>
                </button>
            </div>
        </div>
    );
};

export default Agent;
