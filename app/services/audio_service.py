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
        """
        Initializes the asynchronous clients for Google's STT and TTS services.
        It uses the GOOGLE_API_KEY from the application settings for authentication.
        """
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY must be set in your environment to use the AudioService.")

        client_options = ClientOptions(api_key=settings.GOOGLE_API_KEY)
        
        self.stt_client = speech.SpeechAsyncClient(client_options=client_options)
        self.tts_client = texttospeech.TextToSpeechAsyncClient(client_options=client_options)

    async def transcribe_audio(self, file: UploadFile) -> str:
        """
        Transcribes audio from a FastAPI UploadFile object to text.
        This version is restricted to ONLY accept WAV audio files to ensure
        compatibility with the Next.js frontend.
        """
        # Enforce that only WAV files are accepted.
        if file.content_type not in ["audio/wav", "audio/x-wav"]:
            raise HTTPException(
                status_code=415,  # Unsupported Media Type
                detail=f"Unsupported audio format. Please upload a WAV file, not '{file.content_type}'."
            )

        content = await file.read()
        recognition_audio = speech.RecognitionAudio(content=content)

        # Use the proven, reliable configuration for WAV (LINEAR16) files.
        recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )
        
        try:
            response = await self.stt_client.recognize(
                config=recognition_config, audio=recognition_audio
            )
        except Exception as e:
            print(f"Google STT API Error: {e}")
            raise HTTPException(status_code=500, detail="Error during audio transcription.")

        if response and response.results:
            return response.results[0].alternatives[0].transcript
        return ""

    async def synthesize_speech(self, text: str) -> bytes:
        """
        Converts a string of text to speech and returns the audio content as bytes.
        """
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = await self.tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return response.audio_content

# Singleton instance
audio_service = AudioService()

def get_audio_service() -> AudioService:
    """
    Dependency injector for the AudioService.
    """
    return audio_service