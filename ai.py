import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_frame(frame_bytes):
    """
    Sends the frame to OpenAI for bird identification.
    Returns a dictionary or None if error.
    """
    if not client.api_key:
        print("Error: No OpenAI API Key found.")
        return None

    # Encode image to base64
    base64_image = base64.b64encode(frame_bytes).decode('utf-8')

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert ornithologist. You will be shown an image from a webcam. Identify if there is a bird in the image. If yes, provide the species name, a confidence score (0-1), and a short, interesting fact about it. Return ONLY raw JSON."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Identify the bird in this image. Return JSON format: { \"detected\": bool, \"species\": str, \"confidence\": float, \"interesting_fact\": str }"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
            response_format={ "type": "json_object" }
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)

    except Exception as e:
        print(f"AI Error: {e}")
        return None
