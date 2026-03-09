"""
Proxy routes for the external measurement service.

Forwards LED and contact requests to the external service whose URL
is configured in station_config.json under external_service.url
(default: http://localhost:8003).

Requires: pip install requests
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import requests as _requests
from config import config_manager


router = APIRouter(prefix="/api/ext", tags=["external-measurement"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _base() -> str:
    return config_manager.get_config().external_service.url.rstrip("/")


def _get(path: str) -> Dict:
    try:
        resp = _requests.get(f"{_base()}{path}", timeout=5.0)
        resp.raise_for_status()
        return resp.json()
    except _requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="External service unreachable")
    except _requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="External service timeout")
    except _requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


def _post(path: str, body: Any = None) -> Dict:
    try:
        resp = _requests.post(f"{_base()}{path}", json=body, timeout=5.0)
        resp.raise_for_status()
        return resp.json()
    except _requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="External service unreachable")
    except _requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="External service timeout")
    except _requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


# ---------------------------------------------------------------------------
# LED
# ---------------------------------------------------------------------------

@router.get("/led/state")
def ext_led_state():
    """Get current LED state from external service."""
    return _get("/api/led/state")


@router.post("/led/on")
def ext_led_on():
    """Turn LED on (restores last saved settings) via external service."""
    return _post("/api/led/on")


@router.post("/led/off")
def ext_led_off():
    """Turn LED off via external service."""
    return _post("/api/led/off")


class SetLedRequest(BaseModel):
    mode: str  # 'Off' | 'Left' | 'Right' | 'Both'
    r: int
    g: int
    b: int


@router.post("/led/set")
def ext_led_set(request: SetLedRequest):
    """Set LED mode and color via external service."""
    return _post("/api/led/set", {
        "mode": request.mode,
        "r": request.r,
        "g": request.g,
        "b": request.b,
    })


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

@router.get("/contact/status")
def ext_contact_status():
    """Get current contact status from external service."""
    return _get("/api/contact/status")


@router.post("/contact/auto/start")
def ext_contact_auto_start():
    """Start automatic contact monitoring via external service."""
    return _post("/api/contact/auto/start")


@router.post("/contact/auto/stop")
def ext_contact_auto_stop():
    """Stop automatic contact monitoring via external service."""
    return _post("/api/contact/auto/stop")


# ---------------------------------------------------------------------------
# DevCom
# ---------------------------------------------------------------------------

@router.get("/devcom/status")
def ext_devcom_status():
    """Get DevCom connection status from external service."""
    return _get("/api/devcom/status")
