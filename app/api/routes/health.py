import asyncio
import json
import logging
import os
import re
import socket
from typing import Dict, List, Optional, Tuple
from fastapi import APIRouter
from app.core.config import settings
from app.services.webrtc_rtc_manager import build_ice_servers

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/live")
async def live():
    return {"ok": True}


@router.get("/webrtc")
async def webrtc_health():
    """
    Returns:
      - iceServers as seen by the server (source of truth for clients)
      - TURN config presence
      - DNS & quick TCP reachability probes for turns/tcp endpoints
    """
    servers = build_ice_servers(force_turn=settings.FORCE_TURN)
    serialized = []
    for s in servers:
        serialized.append(
            {
                "urls": s.urls if isinstance(s.urls, list) else [s.urls],
                "username": bool(getattr(s, "username", None)),
                "credential": bool(getattr(s, "credential", None)),
            }
        )

    turn_urls = []
    for s in servers:
        urls = s.urls if isinstance(s.urls, list) else [s.urls]
        for u in urls:
            if u.startswith("turn:") or u.startswith("turns:"):
                turn_urls.append(u)

    checks = await _probe_turn_endpoints(turn_urls, timeout=1.0)
    return {
        "ok": True,
        "iceServers": serialized,
        "turn": {
            "configured": bool(turn_urls),
            "endpoints": checks,
        },
        "env": {
            "TURN_URLS": bool(settings.TURN_URLS),
            "TURN_USERNAME": bool(settings.TURN_USERNAME),
            "TURN_PASSWORD": bool(settings.TURN_PASSWORD),
            "STUN_URLS": bool(settings.STUN_URLS),
        },
    }


async def _probe_turn_endpoints(urls: List[str], timeout: float) -> List[Dict]:
    """
    Best-effort: resolve DNS; if 'turns:' or '?transport=tcp' try TCP connect to port; skip UDP connect.
    """
    results = []
    for url in urls:
        host, port, scheme, transport = _parse_turn_url(url)
        resolved = False
        tcp_ok = None

        # DNS
        try:
            await asyncio.get_running_loop().getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
            resolved = True
        except Exception:
            resolved = False

        # TCP
        if scheme == "turns" or transport == "tcp":
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
                tcp_ok = True
            except Exception:
                tcp_ok = False

        results.append(
            {
                "url": url,
                "host": host,
                "port": port,
                "resolved": resolved,
                "tcp_connect": tcp_ok,  # None when not applicable
            }
        )
    return results


_TURN_RE = re.compile(r"^(?P<scheme>turns?):(?://)?(?P<host>[^:?\s]+)(?::(?P<port>\d+))?(?:\?transport=(?P<transport>\w+))?$")


def _parse_turn_url(url: str) -> Tuple[str, int, str, Optional[str]]:
    m = _TURN_RE.match(url.strip())
    if not m:
        raise ValueError(f"Invalid TURN url: {url}")
    scheme = m.group("scheme")
    host = m.group("host")
    port = int(m.group("port") or (443 if scheme == "turns" else 3478))
    transport = m.group("transport")
    return host, port, scheme, transport