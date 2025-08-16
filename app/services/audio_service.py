from typing import Optional
from google.cloud import speech
from google.cloud import texttospeech_v1 as texttospeech
from fastapi import UploadFile, HTTPException
from google.api_core.client_options import ClientOptions
from app.core.config import settings

class AudioService:
    """
    Asynchronous service to handle Speech-to-Text and Text-to-Speech using Google Cloud APIs.
    """
    def __init__(self):
        self.stt_client = speech.SpeechAsyncClient()
        self.tts_client = texttospeech.TextToSpeechAsyncClient()

    async def transcribe_audio(self, audio_bytes: bytes, content_type: str, language: str = "en-US") -> str:
        if content_type not in ["audio/wav", "audio/x-wav"]:
            raise HTTPException(status_code=415, detail=f"Unsupported audio format. Please upload a WAV file, not '{content_type}'.")

        recognition_audio = speech.RecognitionAudio(content=audio_bytes)

        speech_context = speech.SpeechContext(
            phrases=[
                "Fadhil Ahmad Hidayat",
                "NutriChef",
                "LawBot",
                "Politeknik Harapan Bersama",
                "React Native",
                "YOLOv8",
            ],
            boost=20.0,
        )
        
        primary = "en-US"
        alternatives = ["id-ID"]

        recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=primary,
            alternative_language_codes=alternatives,
            enable_automatic_punctuation=True,
            speech_contexts=[speech_context],
        )

        try:
            response = await self.stt_client.recognize(config=recognition_config, audio=recognition_audio)
        except Exception as e:
            print(f"Google STT API Error: {e}")
            raise HTTPException(status_code=500, detail="Error during audio transcription.")

        if response and response.results:
            return response.results[0].alternatives[0].transcript
        return ""

    async def synthesize_speech(self, text: str, language: str = "en-US") -> bytes:
        synthesis_input = texttospeech.SynthesisInput(text=text)

        if language.lower().startswith('id'):
            lang_code = 'id-ID'
            voice_name = 'id-ID-Standard-D' # standard Indonesian female voice
        else:
            lang_code = 'en-US'
            voice_name = 'en-US-Standard-J' # standard English male voice

        voice = texttospeech.VoiceSelectionParams(language_code=lang_code, name=voice_name)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = await self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return response.audio_content

_audio_service_instance: Optional[AudioService] = None

async def get_audio_service() -> AudioService:
    """
    Dependency injector for the AudioService.
    By being an async function, FastAPI will run this on the main event loop,
    ensuring Google's async clients are initialized correctly.
    """
    global _audio_service_instance
    if _audio_service_instance is None:
        _audio_service_instance = AudioService()
    return _audio_service_instance