import io
from PIL import Image
import torch
from transformers import EfficientNetImageProcessor, EfficientNetForImageClassification

class BirdClassifier:
    _instance = None
    _model = None
    _processor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BirdClassifier, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        print("Loading Local Bird Classifier (dennisjooo/Birds-Classifier-EfficientNetB2)...")
        model_name = "dennisjooo/Birds-Classifier-EfficientNetB2"
        try:
            self._processor = EfficientNetImageProcessor.from_pretrained(model_name)
            self._model = EfficientNetForImageClassification.from_pretrained(model_name)
            self._model.eval() # Set to evaluation mode
            print("Bird Classifier loaded successfully.")
        except Exception as e:
            print(f"Failed to load Bird Classifier: {e}")
            self._model = None

    def predict(self, image_bytes):
        if not self._model or not self._processor:
            return None, 0.0

        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Preprocess
            inputs = self._processor(image, return_tensors="pt")
            
            # Inference
            with torch.no_grad():
                logits = self._model(**inputs).logits
            
            # Get prediction
            probs = torch.nn.functional.softmax(logits, dim=-1)
            top_prob, top_idx = torch.max(probs, dim=-1)
            
            label = self._model.config.id2label[top_idx.item()]
            score = top_prob.item()
            
            return label, score
            
        except Exception as e:
            print(f"Error during classification: {e}")
            return None, 0.0
