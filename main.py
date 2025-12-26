import cv2
import threading
import time
import os
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import pydantic
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from camera import VideoCamera
from ai import analyze_frame
from database import init_db, add_detection, get_recent_detections, clear_all_detections
from classifier import BirdClassifier
import shutil

app = FastAPI()

# Mount static files (Legacy captures)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount React Assets
if os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

# templates = Jinja2Templates(directory="templates") # No longer needed

# Initialize DB
init_db()

# Global camera instance
camera = VideoCamera()
classifier = BirdClassifier()

# Processing lock/flag to prevent overlapping AI calls
is_processing = False
last_ai_call_time = 0
AI_COOLDOWN = 10  # Seconds between AI checks

# Config
ENABLE_CLOUD_AI = os.getenv("ENABLE_CLOUD_AI", "true").lower() == "true"

def process_bird_detection(clean_frame, detections):
    """
    Background task to handle AI analysis on specific crops.
    """
    global is_processing, last_ai_call_time
    
    print(f"Processing {len(detections)} detection(s)...")
    
    # Update timestamp immediately
    last_ai_call_time = time.time()
    
    try:
        for i, (x1, y1, x2, y2, conf) in enumerate(detections):
            # Crop the bird
            # Ensure coordinates are within bounds
            h, w, _ = clean_frame.shape
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            if x1 >= x2 or y1 >= y2:
                continue
                
            bird_crop = clean_frame[y1:y2, x1:x2]
            
            # Encode just the crop for the classifier
            ret, crop_jpeg = cv2.imencode('.jpg', bird_crop)
            if not ret:
                continue
            crop_bytes = crop_jpeg.tobytes()
            
            print(f"Analyzing Bird #{i+1}...")
            
            # Local Classification
            label, score = classifier.predict(crop_bytes)
            
            # Save if it's a valid bird
            if label and score > 0.1:
                # Format label to Title Case (e.g., "Snowy Plover")
                bird_name = label.replace('_', ' ').lower().title()
                
                if score < 0.4:
                    description = "Low confidence match."
                else:
                    description = "Visual match confirmed."
                
                print(f"Identified Bird #{i+1}: {bird_name} ({score:.2f})")
                
                # Save crop to disk
                filename = f"capture_{int(time.time())}_{i}.jpg"
                filepath = os.path.join("static/captures", filename)
                
                with open(filepath, "wb") as f:
                    f.write(crop_bytes)
                    
                # Save to DB
                add_detection(bird_name, score, filepath, description)
            else:
                print(f"Bird #{i+1} too weak: {label} ({score})")

    except Exception as e:
        print(f"Error processing detection: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        is_processing = False

def gen(camera):
    """Video streaming generator function."""
    global is_processing, last_ai_call_time
    
    while True:
        frame, motion_detected, detections, clean_frame = camera.get_frame()
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
                    print(f"MAIN: Motion Triggered with {len(detections)} birds! Starting classification thread...")
                    # Start background thread for specific tasks
                    is_processing = True
                    # Pass the clean frame and the detections list
                    t = threading.Thread(target=process_bird_detection, args=(clean_frame, detections))
                    t.daemon = True
                    t.start()
                else:
                    remaining = AI_COOLDOWN - (time.time() - last_ai_call_time)
                    print(f"MAIN: Cooldown active ({remaining:.1f}s remaining)")
            else:
                print("MAIN: Already processing (locked)")

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n\r\n')


# @app.get("/", response_class=HTMLResponse)
# async def index(request: Request):
#    return templates.TemplateResponse("index.html", {"request": request})

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

class UpdateDetectionRequest(pydantic.BaseModel):
    species: str
    interesting_fact: str
    confidence: float

@app.put("/api/detections/{id}")
def update_detection_endpoint(id: int, request: UpdateDetectionRequest):
    from database import update_detection
    success = update_detection(id, request.species, request.interesting_fact, request.confidence)
    if success:
        return {"status": "success", "message": "Detection updated"}
    else:
        raise HTTPException(status_code=404, detail="Detection not found")

@app.delete("/api/detections/{id}")
def delete_detection_endpoint(id: int):
    from database import delete_detection
    success = delete_detection(id)
    if success:
        return {"status": "success", "message": "Detection deleted"}
    else:
        raise HTTPException(status_code=404, detail="Detection not found")

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

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Specialized handling to avoid shadowing API/Video routes if they weren't matched
    # But FastAPI matches specific routes first.
    # Check if file exists in frontend/dist (e.g. favicon.ico)
    possible_path = os.path.join("frontend/dist", full_path)
    if os.path.isfile(possible_path):
        return FileResponse(possible_path)
        
    # Default to index.html for SPA routing
    return FileResponse("frontend/dist/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
