import asyncio
import fractions
import time
from typing import Optional

import av
from aiortc import MediaStreamTrack
from av.audio.resampler import AudioResampler

AUDIO_PTIME = 0.020  # 20ms audio packetization
SAMPLE_RATE = 16000
AUDIO_SAMPLES_PER_FRAME = int(SAMPLE_RATE * AUDIO_PTIME)
AUDIO_TIME_BASE = fractions.Fraction(1, SAMPLE_RATE)


class AiAudioTrack(MediaStreamTrack):
    """
    A custom audio track for sending AI-generated speech.
    
    This track consumes audio frames from an asyncio.Queue and streams them
    to the WebRTC client. It handles resampling to the required codec format.
    """
    kind = "audio"

    def __init__(self):
        super().__init__()
        self._queue: asyncio.Queue[av.AudioFrame] = asyncio.Queue()
        self._resampler = AudioResampler(
            format="s16", layout="mono", rate=SAMPLE_RATE
        )
        self._start_time: Optional[float] = None
        self._frame_pts = 0

    async def recv(self) -> av.AudioFrame:
        """
        Receive the next audio frame from the queue.
        This is called by the WebRTC library to get data to send.
        """
        frame = await self._queue.get()
        
        # Resample the frame to the format expected by the opus codec
        resampled_frames = self._resampler.resample(frame)
        if not resampled_frames:
            # If resampling needs more data, wait for the next frame
            return await self.recv()
            
        # We only expect one frame out for each input frame
        output_frame = resampled_frames[0]

        # Set the presentation timestamp (PTS)
        if self._start_time is None:
            self._start_time = time.time()
        
        self._frame_pts += output_frame.samples
        output_frame.pts = self._frame_pts
        output_frame.time_base = AUDIO_TIME_BASE
        
        return output_frame

    def add_frame(self, frame: av.AudioFrame):
        """
        Add a raw audio frame to the queue to be sent.
        """
        self._queue.put_nowait(frame)

    def end(self):
        """
        Signal the end of the stream.
        """
        self._queue.put_nowait(None)