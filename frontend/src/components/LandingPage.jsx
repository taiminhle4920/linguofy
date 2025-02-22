import React, { useEffect, useRef, useState } from "react";
import logo from "../assets/logo.svg";
import "./LandingPage.css";

const LandingPage = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [transcription, setTranscription] = useState("");
    const [translation, setTranslation] = useState("");
    const [microphoneAllowed, setMicrophoneAllowed] = useState(false);
    const [selectedModel, setSelectedModel] = useState("custom");

    const canvasRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const animationFrameRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const modelOptions = [
        { value: "custom", label: "Linguofy.ai Model" },
        { value: "whisper", label: "OpenAI Whisper" },
    ];

    useEffect(() => {
        const initializeAudio = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaStreamRef.current = stream;
                setMicrophoneAllowed(true);


                audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
                analyserRef.current = audioContextRef.current.createAnalyser();
                analyserRef.current.fftSize = 2048;


                const source = audioContextRef.current.createMediaStreamSource(stream);
                source.connect(analyserRef.current);


                mediaRecorderRef.current = new MediaRecorder(stream);
                audioChunksRef.current = [];

                mediaRecorderRef.current.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunksRef.current.push(event.data);
                    }
                };

                mediaRecorderRef.current.start(100);
                setIsRecording(true);


                startVisualization();
            } catch (error) {
                console.error("Microphone access denied:", error);
                alert("Microphone access is required for this app to work.");
            }
        };

        const startVisualization = () => {
            const canvas = canvasRef.current;
            const ctx = canvas.getContext('2d');
            const analyser = analyserRef.current;
            const dataArray = new Uint8Array(analyser.frequencyBinCount);

            const draw = () => {
                animationFrameRef.current = requestAnimationFrame(draw);
                analyser.getByteTimeDomainData(dataArray);
                ctx.fillStyle = '#2a2a2a';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.lineWidth = 2;
                ctx.strokeStyle = '#2196f3';  
                ctx.beginPath();

                const sliceWidth = canvas.width / dataArray.length;
                let x = 0;

                for (let i = 0; i < dataArray.length; i++) {
                    const v = dataArray[i] / 128.0;
                    const y = (v * canvas.height) / 2;

                    if (i === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }

                    x += sliceWidth;
                }

                ctx.lineTo(canvas.width, canvas.height / 2);
                ctx.stroke();
            };

            draw();
        };

        initializeAudio();

        
        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
            if (audioContextRef.current) {
                audioContextRef.current.close();
            }
            if (mediaStreamRef.current) {
                mediaStreamRef.current.getTracks().forEach(track => track.stop());
            }
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                mediaRecorderRef.current.stop();
            }
        };
    }, []);

    useEffect(() => {
        const updateCanvasSize = () => {
            const canvas = canvasRef.current;
            if (canvas) {
                const width = canvas.offsetWidth;
                const height = canvas.offsetHeight;
                canvas.width = width;
                canvas.height = height;
            }
        };

        window.addEventListener('resize', updateCanvasSize);
        updateCanvasSize();

        return () => window.removeEventListener('resize', updateCanvasSize);
    }, []);

    return (
        <div className="container">
            <div className="header">
                <div className="logo-container">
                    <img src={logo} alt="App Logo" className="logo" />
                    <span className="logo-text">Linguofy.ai</span>
                </div>
                <div className="model-selector">
                    <select
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        className="model-select"
                    >
                        {modelOptions.map(option => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="visualizer-container">
                <canvas
                    ref={canvasRef}
                    className="audio-visualizer"
                />
            </div>

            <div className="bottomSection">
                <div className="box">
                    <h3>Transcription</h3>
                    <textarea
                        className="textArea"
                        value={transcription}
                        readOnly
                        placeholder="Transcription will appear here..."
                    />
                </div>

                <button
                    onClick={() => {
                        const translatedText = `Translated: ${transcription}`;
                        setTranslation(translatedText);
                    }}
                    className="translateButton"
                >
                    Translate
                </button>

                <div className="box">
                    <h3>Translation</h3>
                    <textarea
                        className="textArea"
                        value={translation}
                        readOnly
                        placeholder="Translation will appear here..."
                    />
                </div>
            </div>
        </div>
    );
};

export default LandingPage;