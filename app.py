from fastapi import FastAPI, Query, HTTPException
from gradio_client import Client
import requests
import os

app = FastAPI()

HF_MODEL = "yanze/PuLID-FLUX"
BASE_URL = "https://yanze-pulid-flux.hf.space/file="  # Ensure this is correct
TEMP_DIR = "/tmp"  # Folder to store temp image downloads

def download_image(image_url: str) -> str:
    """Downloads image from URL and saves it locally."""
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download image")

        filename = os.path.join(TEMP_DIR, "input_image.jpg")
        with open(filename, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return filename
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading image: {str(e)}")

@app.get("/generate")
def generate_image(prompt: str, image_url: str):
    client = Client(HF_MODEL)
    
    # Download image from URL first
    image_path = download_image(image_url)

    width, height = 1080, 1080  # Instagram format (fixed size)

    try:
        result = client.predict(
            prompt=prompt,
            id_image=image_path,  # File path instead of URL
            start_step=0,
            guidance=4,
            seed="-1",
            true_cfg=1,
            width=width,
            height=height,
            num_steps=20,
            id_weight=1,
            neg_prompt="bad quality, worst quality, text, signature, watermark, extra limbs",
            timestep_to_start_cfg=1,
            max_sequence_length=128,
            api_name="/generate_image"
        )

        if not result or not isinstance(result, list) or len(result) == 0:
            raise HTTPException(status_code=500, detail="Model did not return a valid response")

        file_path = result[0]
        full_url = f"{BASE_URL}{file_path}"
        return {"image_url": full_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
