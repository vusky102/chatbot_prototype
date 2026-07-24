import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

# 1. Create a dummy jsonl file
with open("test_batch.jsonl", "w") as f:
    f.write(json.dumps({
        "request": {
            "contents": [{"role": "user", "parts": [{"text": "Hello world"}]}]
        }
    }) + "\n")

# 2. Upload it
file_info = client.files.upload(file="test_batch.jsonl")
print("Uploaded file:", file_info.name)

# 3. Create batch job
job = client.batches.create(
    model="gemini-2.5-flash",
    src=file_info.name
)
print("Job created:", job.name)
print("Job state:", job.state)
print("Output URI:", job.dest.file_name if getattr(job, "dest", None) else getattr(job, "output_uri", None))

import time
job = client.batches.get(name=job.name)
print("Job state:", job.state)
print("Final Output URI:", job.dest.file_name if getattr(job, "dest", None) else getattr(job, "output_uri", None))

# get all methods of batches
print(dir(client.batches))
