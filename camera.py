import cv2
import time
import numpy as np
import threading
from ultralytics import YOLO

class VideoCamera:
    def __init__(self):
        self.video = None
        self.current_source = 0
        self.lock = threading.Lock()
        self.open_camera(0)
        
        # Motion detection variables
        self.last_frame = None
        self.min_motion_frames = 8
        self.motion_counter = 0
        
        # Load YOLOv8 Model (Nano version)
        # It will auto-download 'yolov8n.pt' on first run
        self.model = YOLO('yolov8n.pt')
        
        # Detect Bird Class ID (usually 14 in COCO dataset)
        self.target_class_id = 14
        
        # Debug Mode
        self.debug_mode = False

    def toggle_debug(self, enabled: bool):
        self.debug_mode = enabled

    def open_camera(self, source=0):
        with self.lock:
            if self.video is not None:
                self.video.release()
            self.video = cv2.VideoCapture(source)
            self.current_source = source
            # Allow camera to warm up
            time.sleep(0.5)

    def set_source(self, source_index):
        try:
            source = int(source_index)
            self.open_camera(source)
        except ValueError:
            pass

    @staticmethod
    def list_cameras():
        import platform
        import subprocess
        import json
        
        system = platform.system()
        cameras = []
        if system == "Darwin":
            try:
                cmd = ["system_profiler", "SPCameraDataType", "-json"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                data = json.loads(result.stdout)
                items = data.get('SPCameraDataType', [])
                for i, item in enumerate(items):
                     cam_name = item.get('_name', f"Camera {i}")
                     cap = cv2.VideoCapture(i)
                     if cap.isOpened():
                         cameras.append({"id": i, "name": cam_name})
                         cap.release()
            except Exception as e:
                print(f"Error fetching Mac cameras: {e}")
        elif system == "Linux":
            import os
            try:
                for i in range(10):
                    if os.path.exists(f"/dev/video{i}"):
                        cameras.append({"id": i, "name": f"Camera/Device {i}"})
            except:
                pass

        if not cameras:
            for i in range(5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        cameras.append({"id": i, "name": f"Camera {i}"})
                    cap.release()
        return cameras

    def __del__(self):
        with self.lock:
            if self.video:
                self.video.release()

    def get_frame(self):
        with self.lock:
            if not self.video or not self.video.isOpened():
                return None, False
            success, frame = self.video.read()
            if not success:
                return None, False

        # --- 1. Basic Motion Trigger (CPU optimization) ---
        # We only run heavy YOLO inference if something is moving.
        
        resized_frame = cv2.resize(frame, (640, 480))
        gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        motion_detected = False
        significant_motion = False
        
        if self.last_frame is None:
            self.last_frame = gray
            return frame, False

        frame_delta = cv2.absdiff(self.last_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if cv2.contourArea(contour) < 500:
                continue
            significant_motion = True
            break
            
        if significant_motion:
            self.motion_counter += 1
        else:
            self.motion_counter = 0

        # --- 2. YOLO Detection Logic ---
        # Trigger if motion persists OR if strict debug mode forces it
        should_run_yolo = False
        if self.motion_counter >= 5: # Slightly faster trigger than before (was 8)
            should_run_yolo = True
        if self.debug_mode:
            should_run_yolo = True
            
        final_detections = []
        
        if should_run_yolo:
            # Run YOLO on the resized frame (faster) or original? 
            # YOLOv8n is fast (Nano). Let's try resized first for speed.
            # verbose=False suppresses stdout spam
            results = self.model(resized_frame, verbose=False, stream=True)
            
            # Calculate scaling back to original frame
            height, width = frame.shape[:2]
            scale_x = width / 640
            scale_y = height / 480
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Class 14 is 'bird' in COCO
                    if cls == self.target_class_id: 
                        # Confidence threshold
                        if conf > 0.4:
                            # Coordinates (x1, y1, x2, y2)
                            x1, y1, x2, y2 = box.xyxy[0]
                            
                            # Scale to original
                            sx1 = int(x1 * scale_x)
                            sy1 = int(y1 * scale_y)
                            sx2 = int(x2 * scale_x)
                            sy2 = int(y2 * scale_y)
                            
                            final_detections.append((sx1, sy1, sx2, sy2, conf))

        # --- 3. Action & Drawing ---
        
        if len(final_detections) > 0:
            # We found a bird!
            # If motion was also present (which triggered this), we confirm valid detection.
            # But wait, YOLO *confirms* it's a bird. Motion just woke us up.
            # So if we are here, it IS a bird.
            
            # Should we reset motion counter? No, let it stream as long as bird is there.
            # But the 'motion_detected' flag tells backend to save.
            # Only trigger backend save if motion counter is high enough to be stable.
            if self.motion_counter >= 5:
                motion_detected = True
            
            # Draw
            if self.debug_mode:
                for (x1, y1, x2, y2, conf) in final_detections:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"Bird {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                if motion_detected:
                     cv2.putText(frame, ">>> TRIGGERED <<<", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

        else:
            # No birds found by YOLO.
            # If motion was high, but YOLO sees nothing, it's just wind/leaves/book.
            # We do NOT set motion_detected = True.
            pass

        self.last_frame = gray
        return frame, motion_detected

    def get_jpeg(self, frame):
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
