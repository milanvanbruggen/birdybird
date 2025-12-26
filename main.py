import cv2
import threading
import time
import os
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from camera import VideoCamera
from ai import analyze_frame
from database import init_db, add_detection, get_recent_detections, clear_all_detections
import shutil

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize DB
init_db()

# Global camera instance
camera = VideoCamera()

# Processing lock/flag to prevent overlapping AI calls
is_processing = False
last_ai_call_time = 0
AI_COOLDOWN = 10  # Seconds between AI checks

# Config
ENABLE_CLOUD_AI = os.getenv("ENABLE_CLOUD_AI", "true").lower() == "true"

def process_bird_detection(frame_bytes):
    """
    Background task to handle AI analysis (or local logging).
    """
    global is_processing, last_ai_call_time
    
    print("Processing detection...")
    
    if ENABLE_CLOUD_AI:
        print("Starting Cloud AI analysis...")
        result = analyze_frame(frame_bytes)
    # Update timestamp immediately to prevent double triggers
    last_ai_call_time = time.time()
    
    print("Processing detection locally...")
    
    try:
        # Local Classification
        label, score = classifier.predict(image_bytes)
        
        if label and score > 0.4: # 40% confidence threshold
            bird_name = label
            description = f"Detected via local EfficientNetB2 model with {score*100:.1f}% confidence."
            print(f"Identified: {bird_name} ({score:.2f})")
            
            # Save to cleanup
            filename = f"capture_{int(time.time())}.jpg"
            filepath = os.path.join("static/captures", filename)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
                
            # Save to DB
            add_detection(bird_name, score, filepath, description)
        else:
            print(f"Detection too weak or failed: {label} ({score})")

    except Exception as e:
        print(f"Error processing detection: {e}")
        
    finally:
        is_processing = False

def gen(camera):
    """Video streaming generator function."""
    global is_processing, last_ai_call_time
    
    while True:
        frame, motion_detected = camera.get_frame()
        if frame is None:
            break
            
        # Encode for streaming/AI
        jpeg_bytes = camera.get_jpeg(frame)
        
        # Motion Logic Trigger
        # Only trigger if:
        # 1. Motion detected
        # 2. Not currently processing
        # 3. Cooldown passed
        if motion_detected:
            # print("Motion detected!") # excessive spam
            if not is_processing:
                if (time.time() - last_ai_call_time) > AI_COOLDOWN:
                    # Start background thread for specific tasks
                    # is_processing = True
                    # t = threading.Thread(target=process_bird_detection, args=(jpeg_bytes,))
                    # t.daemon = True
                    # t.start()
                    pass
                else:
                    # print("Cooldown active")
                    pass
            else:
                # print("Already processing")
                pass

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n\r\n')

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(gen(camera), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/cameras")
def get_cameras():
    return camera.list_cameras()

@app.post("/api/cameras/{index}")
def set_camera(index: int):
    camera.set_source(index)
    return {"status": "success", "message": f"Switched to camera {index}"}

@app.post("/api/debug/{enabled}")
def set_debug_mode(enabled: str):
    is_enabled = enabled.lower() == "true"
    camera.toggle_debug(is_enabled)
    return {"status": "success", "debug_mode": is_enabled}

@app.get("/api/detections")
def get_detections():
    return get_recent_detections()

@app.delete("/api/detections")
def clear_detections():
    # 1. Clear DB
    clear_all_detections()
    
    # 2. Clear images
    folder = "static/captures"
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
                
    return {"status": "success", "message": "All detections cleared"}

@app.get("/api/status")
def get_status():
    return {"processing": is_processing, "cooldown": max(0, AI_COOLDOWN - (time.time() - last_ai_call_time))}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
