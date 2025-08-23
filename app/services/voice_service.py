import asyncio
import io
import json
import logging
from enum import Enum
from typing import Dict, Optional, Set

import av
from aiortc import RTCSessionDescription
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from app.services.audio_service import AudioService, get_audio_service
from app.services.agent_service import AgentService, get_agent_service
from app.services.webrtc_utils import AiAudioTrack
from app.services.webrtc_rtc_manager import PeerConnectionManager

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
        self.audio_service = get_audio_service()
        self.agent_service = get_agent_service()

    async def handle_message(self, session_id: str, message: dict, websocket):
        agent = self._agents.get(session_id)
        if message.get("type") == "offer":
            if agent:
                await agent.close()

            logger.info(f"Creating new VoiceAgent for session: {session_id}")
            agent = VoiceAgent(
                session_id=session_id,
                websocket=websocket,
                agent_service=self.agent_service,
                audio_service=self.audio_service,
            )
            self._agents[session_id] = agent
            await agent.handle_offer(message["sdp"], message["type"])

    async def cleanup(self, session_id: str):
        if session_id in self._agents:
            logger.info(f"Cleaning up agent for session: {session_id}")
            await self._agents[session_id].close()
            del self._agents[session_id]


class VoiceAgent:
    def __init__(self, session_id: str, websocket, agent_service: AgentService, audio_service: AudioService):
        self.session_id = session_id
        self.websocket = websocket
        self.audio_service = audio_service
        self.agent_service = agent_service
        self.rtc = PeerConnectionManager()
        self.pc = self.rtc.ensure_pc()
        self.player = AiAudioTrack()
        self.pc.addTrack(self.player)
        
        self._tasks: Set[asyncio.Task] = set()
        self.state = AgentState.IDLE
        self._conversation_task: Optional[asyncio.Task] = None

        @self.pc.on("track")
        async def on_track(track):
            logger.info(f"✅ Track {track.kind} received for session {self.session_id}")
            if track.kind == "audio":
                self._conversation_task = asyncio.create_task(self._conversation_loop(track))
                self._tasks.add(self._conversation_task)

    async def _set_state(self, new_state: AgentState):
        if self.state == new_state: return
        self.state = new_state
        logger.info(f"🚀 [{self.session_id}] State -> {self.state.value}")
        try:
            await self.websocket.send_text(json.dumps({"type": "state", "state": self.state.value}))
        except Exception as e:
            logger.warning(f"Could not send state update: {e}")

    async def handle_offer(self, sdp: str, type: str):
        logger.info(f"Handling offer for session {self.session_id}")
        local_description = await self.rtc.handle_offer(sdp, type)
        response = {"sdp": local_description.sdp, "type": "answer"}
        await self.websocket.send_text(json.dumps(response))
        logger.info(f"Sent answer for session {self.session_id}")

    async def _conversation_loop(self, track):
        inbound_audio_queue = asyncio.Queue()

        async def stream_audio_in():
            """Continuously streams audio from the client into a queue."""
            logger.info("Audio streaming from client has started.")
            async for frame in track:
                resampled = frame.resample(rate=16000, format="s16", layout="mono")
                for r_frame in resampled:
                    await inbound_audio_queue.put(r_frame.to_ndarray().tobytes())
            logger.info("Audio streaming from client has ended.")
            await inbound_audio_queue.put(None)

        async def audio_generator():
            """
            Yields audio chunks from the queue. This generator now includes a
            client-side timeout to ensure the listening phase always ends.
            """
            while True:
                try:
                    chunk = await asyncio.wait_for(inbound_audio_queue.get(), timeout=2.0)
                    if chunk is None:
                        logger.info("Audio generator received None, ending.")
                        break
                    yield chunk
                except asyncio.TimeoutError:
                    logger.info("Audio generator timed out (2s of silence). Ending turn.")
                    break

        stream_task = asyncio.create_task(stream_audio_in())
        self._tasks.add(stream_task)

        while True:
            await self._set_state(AgentState.LISTENING)
            
            while not inbound_audio_queue.empty():
                inbound_audio_queue.get_nowait()
            
            transcript = ""
            async for text in self.audio_service.stream_transcribe_audio(audio_generator()):
                transcript += text
            
            if not transcript.strip():
                logger.info("🎤 No speech detected or empty transcript.")
                continue

            logger.info(f"🗣️ User said: {transcript}")
            await self._set_state(AgentState.THINKING)

            full_answer = ""
            response_generator = self.agent_service.stream_agent_response(self.session_id, transcript)
            async for event in response_generator:
                if event.get("event") == "token":
                    full_answer += event.get("data", "")
            
            if full_answer.strip():
                logger.info(f"🤖 AI Response: {full_answer}")
                await self._play_ai_response(full_answer)
            else:
                logger.info("🤖 AI had no response.")

    async def _play_ai_response(self, text: str):
        await self._set_state(AgentState.SPEAKING)
        try:
            detected_lang = detect(text)
            tts_language_code = "id-ID" if detected_lang == "id" else "en-US"
        except LangDetectException:
            tts_language_code = "en-US"

        try:
            audio_bytes = await self.audio_service.synthesize_speech(text, language=tts_language_code)
            container = av.open(io.BytesIO(audio_bytes), format="mp3")
            for frame in container.decode(audio=0):
                self.player.add_frame(frame)
            await asyncio.sleep(0.1) 
        except Exception as e:
            logger.error(f"Error during TTS playback: {e}")

    async def close(self):
        logger.info(f"Closing agent for session {self.session_id}")
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.rtc.close()