import asyncio
import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCIceServer,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def build_ice_servers(force_turn: bool = False) -> List[RTCIceServer]:
    """
    Keep config explicit. If force_turn=True and no TURN, warn early.
    """
    stun_urls = _split_csv(settings.STUN_URLS)
    turn_urls = _split_csv(settings.TURN_URLS)
    turn_username = settings.TURN_USERNAME
    turn_password = settings.TURN_PASSWORD

    servers: List[RTCIceServer] = []

    if force_turn and not turn_urls:
        logger.warning("force_turn=True but no TURN_URLS provided; connectivity may fail behind NAT/firewalls.")

    if not force_turn and stun_urls:
        servers.append(RTCIceServer(urls=stun_urls))

    if turn_urls:
        if not turn_username or not turn_password:
            logger.warning("TURN_URLS set but TURN_USERNAME or TURN_PASSWORD missing; TURN auth will fail.")
        servers.append(
            RTCIceServer(
                urls=turn_urls,
                username=turn_username,
                credential=turn_password,
            )
        )

    return servers


@dataclass
class PeerConnectionManager:
    """
    Minimal aiortc manager that:
    - Builds RTCConfiguration from env.
    - Returns SDP only after ICE gathering completes.
    - Can await 'connected' with timeout for diagnostics/UX.
    """
    force_turn: bool = True
    gather_timeout: float = 6.0
    connect_timeout: float = 15.0

    pc: Optional[RTCPeerConnection] = None

    def _new_pc(self) -> RTCPeerConnection:
        cfg = RTCConfiguration(iceServers=build_ice_servers(force_turn=self.force_turn))
        pc = RTCPeerConnection(configuration=cfg)

        # Basic logging
        @pc.on("iceconnectionstatechange")
        async def _on_ice():
            logger.info("ICE state: %s", pc.iceConnectionState)

        @pc.on("connectionstatechange")
        async def _on_conn():
            logger.info("PC state: %s", pc.connectionState)

        return pc

    def ensure_pc(self) -> RTCPeerConnection:
        if self.pc is None or self.pc.connectionState in ("failed", "closed"):
            self.pc = self._new_pc()
        return self.pc

    async def close(self) -> None:
        if self.pc:
            await self.pc.close()
            self.pc = None

    async def handle_offer(self, sdp: str, type_: str) -> RTCSessionDescription:
        """
        Creates/uses an RTCPeerConnection, attaches already-added tracks,
        sets remote description, gathers fully, and returns the local answer.
        """
        pc = self.ensure_pc()
        offer = RTCSessionDescription(sdp=sdp, type=type_)
        await pc.setRemoteDescription(offer)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        await self._wait_ice_gathering_complete(pc, timeout=self.gather_timeout)
        # After gathering done, return the (final) localDescription
        assert pc.localDescription is not None
        return pc.localDescription

    async def wait_connected(self, timeout: Optional[float] = None) -> Tuple[bool, str]:
        """
        Wait for connected/completed. If failed/closed or timeout, return (False, reason).
        """
        pc = self.ensure_pc()
        wanted = {"connected", "completed"}
        bad = {"failed", "closed", "disconnected"}

        # Fast-path
        if pc.iceConnectionState in wanted or pc.connectionState in wanted:
            return True, "already-connected"
        if pc.iceConnectionState in bad or pc.connectionState in bad:
            return False, f"bad-initial-state:{pc.iceConnectionState}/{pc.connectionState}"

        evt = asyncio.Event()

        async def _watch():
            while True:
                if pc.iceConnectionState in wanted or pc.connectionState in wanted:
                    evt.set()
                    return
                if pc.iceConnectionState in bad or pc.connectionState in bad:
                    evt.set()
                    return
                await asyncio.sleep(0.05)

        task = asyncio.create_task(_watch())
        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout or self.connect_timeout)
        except asyncio.TimeoutError:
            return False, "timeout"
        finally:
            task.cancel()

        state = f"{pc.iceConnectionState}/{pc.connectionState}"
        ok = pc.iceConnectionState in wanted or pc.connectionState in wanted
        return ok, state

    async def _wait_ice_gathering_complete(self, pc: RTCPeerConnection, timeout: float) -> None:
        if pc.iceGatheringState == "complete":
            return

        evt = asyncio.Event()

        @pc.on("icegatheringstatechange")
        async def _on_gather():
            if pc.iceGatheringState == "complete":
                evt.set()

        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("ICE gathering did not complete within %.1fs; returning partial candidates.", timeout)
