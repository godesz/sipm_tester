from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse
import cv2
import serial
import threading
import time
import re

import serial

from datetime import datetime
import os

CAPTURE_DIR = "captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],   # ⭐ must allow OPTIONS + POST
    allow_headers=["*"],
)

# --- Serial Setup ---
SERIAL_PORT = "COM5"       # Adjust to your actual port
BAUDRATE = 115200
ser = None
ser_pnp = None      # COM5 (PnP machine)
ser_light = None    # COM3 (ESP32 RGB controller)
serial_lock = threading.Lock()

@app.post("/connect_pnp")
async def connect_port(data: dict):
    port = data["port"]

    try:
        global ser_pnp
        ser_pnp = serial.Serial(port, 115200, timeout=0.2)
        print(f"Connected to {port}")
        return {"status": "ok", "port": port}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- State ---
lock = threading.Lock()
position = {"X": 0.0, "Y": 0.0, "Z": 0.0}

# --- GCODE Helpers ---
def send_gcode(cmd: str):
    cmd = cmd.strip() + "\n"
    ser_pnp.write(cmd.encode("utf-8"))
    ser_pnp.flush()
    print(f">> {cmd.strip()}")
    time.sleep(0.05)

def read_line():
    try:
        return ser_pnp.readline().decode(errors="ignore").strip()
    except Exception:
        return ""

def query_position():
    send_gcode("M114")
    line = read_line()
    print(f"<< {line}")
    match = re.findall(r"([XYZ])\s*(-?\d+\.?\d*)", line)
    pos = {axis: float(val) for axis, val in match}
    if pos:
        position.update(pos)
    return position


@app.get("/move")
def move_axis(axis: str, distance: float):
    with lock:
        send_gcode("G91")
        send_gcode(f"G0 {axis.upper()}{distance:.3f} F5000")
        send_gcode("G90")
        pos = query_position()
    return {"status": "ok", "position": pos}


@app.get("/home")
def home_machine():
    with lock:
        send_gcode("G28")
        time.sleep(2)
        pos = query_position()
    return {"status": "homed", "position": pos}


@app.get("/position")
def get_position():
    pos = query_position()
    return {"position": pos}


# --- CAMERA STREAMING ---
cameras = {}

def get_camera(id=0):
    if id not in cameras:
        cam = cv2.VideoCapture(id)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
        cameras[id] = cam
    return cameras[id]

def gen_frames(camera_id=0):
    cam = get_camera(camera_id)
    while True:
        success, frame = cam.read()
        if not success:
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Store open camera handles
cameras = {}
camera_locks = {}

def list_cameras(max_devices: int = 10):
    """Try opening a few camera indexes and return which respond."""
    available = []
    for i in range(max_devices):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # CAP_DSHOW avoids warnings on Windows
        if cap is not None and cap.isOpened():
            available.append(i)
            cap.release()
    return available

@app.get("/cameras")
def get_cameras():
    """List available camera indexes"""
    return {"available_cameras": list_cameras()}

def get_camera(id: int):
    """Open a camera if not already open"""
    if id not in cameras:
        cap = cv2.VideoCapture(id, cv2.CAP_DSHOW)
        if not cap.isOpened():
            raise RuntimeError(f"Camera {id} not available")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cameras[id] = cap
        camera_locks[id] = threading.Lock()
    return cameras[id]

def gen_frames(camera_id: int = 0):
    """Generator for MJPEG streaming"""
    cam = get_camera(camera_id)
    while True:
        with camera_locks[camera_id]:
            success, frame = cam.read()
        if not success:
            continue
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

@app.get("/video")
def video_feed(camera_id: int = Query(0, description="Camera index")):
    """Stream camera video as MJPEG"""
    try:
        return StreamingResponse(
            gen_frames(camera_id),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/connect_light")
async def connect_light(data: dict):
    global ser_light
    port = data["port"]  # "COM3"
    try:
        ser_light = serial.Serial(port, 115200, timeout=1)
        return {"status": "connected", "port": port}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/disconnect_light")
async def disconnect_light():
    global ser_light

    if ser_light is not None:
        try:
            ser_light.close()
        except:
            pass

        ser_light = None

    return {"status": "disconnected"}
  
@app.post("/set_light")
async def set_light(data: dict):
    global ser_light
    if ser_light is None:
        raise HTTPException(status_code=400, detail="Light serial not connected")

    r = int(data["r"])
    g = int(data["g"])
    b = int(data["b"])

    cmd = f"SET_RGB {r} {g} {b}\n"
    ser_light.write(cmd.encode())

    return {"status": "ok"}
 
@app.post("/light/brightness")
async def set_brightness(data: dict):
    global ser_light
    if ser_light is None:
        raise HTTPException(400, "Light not connected")

    value = int(data["value"])
    ser_light.write(f"SET_BRIGHTNESS {value}\n".encode())
    return {"status": "ok"}

@app.post("/light/segment")
async def set_segment(data: dict):
    global ser_light
    if ser_light is None:
        raise HTTPException(400, "Light not connected")

    seg = int(data["segment"])
    r = int(data["r"])
    g = int(data["g"])
    b = int(data["b"])

    ser_light.write(f"SET_SEG {seg} {r} {g} {b}\n".encode())
    return {"status": "ok"}

@app.post("/light/preset")
async def preset(data: dict):
    global ser_light
    if ser_light is None:
        raise HTTPException(400, "Light not connected")

    name = data["name"].upper()
    ser_light.write(f"PRESET {name}\n".encode())
    return {"status": "ok"}

@app.post("/capture_image")
async def capture_image(camera_id: int = 0):
    print(f"Capturing image of camera.")
    cap = cv2.VideoCapture(camera_id)

    # force resolution (same as stream)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return {"error": "Camera capture failed"}

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{CAPTURE_DIR}/cam{camera_id}_{ts}.png"

    cv2.imwrite(filename, frame)

    print(f"Image saved: {filename}")

    return {
        "status": "ok",
        "file": filename
    }