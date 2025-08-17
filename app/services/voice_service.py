import asyncio
import json
import logging
import io
from enum import Enum
from typing import Dict, Optional, Set

import av
from aiortc import RTCPeerConnection, RTCSessionDescription
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from app.services.audio_service import AudioService, get_audio_service
from app.services.agent_service import AgentService, get_agent_service 
from app.services.chat_service import ChatService, get_chat_service
from app.services.webrtc_utils import AiAudioTrack

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class VoiceServiceManager:
    def __init__(self):
        self._agents: Dict[str, VoiceAgent] = {}
        self.chat_service = get_chat_service()
        self.audio_service = get_audio_service()
        self.agent_service = get_agent_service()

    async def handle_message(self, session_id: str, message: dict, websocket):
        agent = self._agents.get(session_id)
        if message['type'] == 'offer':
            if agent:
                await agent.close()
            
            agent = VoiceAgent(
                session_id, 
                websocket, 
                self.agent_service,
                self.audio_service
            )
            self._agents[session_id] = agent
            
            response = await agent.handle_offer(message["sdp"], message["type"])
            await websocket.send_text(json.dumps(response))
        
    async def cleanup(self, session_id: str):
        if session_id in self._agents:
            await self._agents[session_id].close()
            del self._agents[session_id]

class VoiceAgent:
    """
    Manages a single end-to-end voice conversation session with state and interruption handling.
    """
    def __init__(self, session_id: str, websocket, agent_service: AgentService, audio_service: AudioService):
        self.session_id = session_id
        self.websocket = websocket
        self.audio_service = audio_service
        self.agent_service = agent_service
        
        self.pc = RTCPeerConnection()
        self.player = AiAudioTrack()
        self.pc.addTrack(self.player)
        
        self._inbound_audio_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._tasks: Set[asyncio.Task] = set()
        
        self.state = AgentState.IDLE
        self._interruption_event = asyncio.Event()
        self._current_tts_task: Optional[asyncio.Task] = None

        @self.pc.on("track")
        async def on_track(track):
            logger.info(f"Track {track.kind} received for session {self.session_id}")
            if track.kind == "audio":
                pipeline_task = asyncio.create_task(self._audio_pipeline(track))
                self._tasks.add(pipeline_task)

    # Method to set and broadcast the agent's state
    async def _set_state(self, new_state: AgentState):
        if self.state == new_state:
            return
        self.state = new_state
        logger.info(f"[{self.session_id}] State changed to: {self.state.value}")
        try:
            await self.websocket.send_text(
                json.dumps({"type": "state", "state": self.state.value})
            )
        except Exception as e:
            logger.warning(f"Could not send state update to client: {e}")

    async def handle_offer(self, sdp: str, type: str) -> Dict[str, str]:
        offer = RTCSessionDescription(sdp=sdp, type=type)
        await self.pc.setRemoteDescription(offer)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        return {"sdp": self.pc.localDescription.sdp, "type": "answer"}

    async def _audio_pipeline(self, track):
        await self._set_state(AgentState.LISTENING)
        
        audio_stream_task = asyncio.create_task(self._stream_audio_in(track))
        self._tasks.add(audio_stream_task)

        async for transcript in self.audio_service.stream_transcribe_audio(self._audio_generator()):
            logger.info(f"[{self.session_id}] User said: {transcript}")
            if not transcript.strip():
                continue

            # Interruption Logic
            if self.state == AgentState.SPEAKING:
                logger.info(f"[{self.session_id}] User interrupted AI. Stopping TTS.")
                self._interruption_event.set() # Signal the TTS task to stop
                if self._current_tts_task:
                    self._current_tts_task.cancel() # Cancel the running TTS task

            await self._set_state(AgentState.THINKING)
            
            full_answer = ""
            response_generator = self.agent_service.stream_agent_response(
                session_id=self.session_id, message=transcript
            )
            
            async for event in response_generator:
                if event["event"] == "token":
                    full_answer += event["data"]
                        
            logger.info(f"[{self.session_id}] AI response: {full_answer}")

            if full_answer.strip():
                self._interruption_event.clear() # Reset interruption event before speaking
                self._current_tts_task = asyncio.create_task(self._play_ai_response(full_answer))
                self._tasks.add(self._current_tts_task)
            else:
                await self._set_state(AgentState.LISTENING)

    async def _stream_audio_in(self, track):
        async for frame in track:
            resampled_frames = frame.resample(rate=16000, format="s16", layout="mono")
            for resampled_frame in resampled_frames:
                await self._inbound_audio_queue.put(resampled_frame.to_ndarray().tobytes())

    async def _audio_generator(self):
        while True:
            chunk = await self._inbound_audio_queue.get()
            if chunk is None: break
            yield chunk

    # Updated TTS playback to be interruptible
    async def _play_ai_response(self, text: str):
        await self._set_state(AgentState.SPEAKING)
        try:
            detected_lang = detect(text)
            tts_language_code = "id-ID" if detected_lang == "id" else "en-US"
        except LangDetectException:
            tts_language_code = "en-US"
        
        try:
            audio_bytes = await self.audio_service.synthesize_speech(text, language=tts_language_code)
            
            while not self.player._queue.empty():
                self.player._queue.get_nowait()

            container = av.open(io.BytesIO(audio_bytes), format="mp3")
            for frame in container.decode(audio=0):
                if self._interruption_event.is_set():
                    logger.info("TTS playback interrupted.")
                    break
                self.player.add_frame(frame)
        except asyncio.CancelledError:
            logger.info("TTS task was cancelled due to interruption.")
        except Exception as e:
            logger.error(f"Error during TTS playback: {e}")
        finally:
            await self._set_state(AgentState.LISTENING)

    async def close(self):
        logger.info(f"Closing agent for session {self.session_id}")
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.pc.close()
        