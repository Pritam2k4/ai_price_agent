import modal
import os
from modal import Image

# Setup

app = modal.App("hello")
image = Image.debian_slim().pip_install("requests", "transformers", "torch")

# Hello!

@app.function(image=image)
def hello() -> str:
    import requests

    response = requests.get("https://ipinfo.io/json")
    data = response.json()
    city, region, country = data["city"], data["region"], data["country"]
    return f"Hello from {city}, {region}, {country}!!"


@app.function(image=image, region="eu")
def hello_europe() -> str:
    import requests

    response = requests.get("https://ipinfo.io/json")
    data = response.json()
    city, region, country = data["city"], data["region"], data["country"]
    return f"Hello from {city}, {region}, {country}!!"


@app.function(image=image, secrets=[modal.Secret.from_name("huggingface")])
def generate(text: str) -> str:
    from transformers import pipeline
    generator = pipeline("text-generation", model="meta-llama/Llama-3.2-3B")
    result = generator(text, max_new_tokens=50)
    return result[0]["generated_text"]
