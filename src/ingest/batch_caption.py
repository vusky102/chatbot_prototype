import base64
import json
import mimetypes
import os
import time
from pathlib import Path

from google import genai
from google.genai import types

from src.ingest.image_extraction import clean_env_val


class BatchCaptioner:
    """Wrapper to interact with Gemini Batch API for image captioning."""

    def __init__(self, provider: str = "gemini"):
        self.provider = provider.lower()
        if self.provider != "gemini":
            raise ValueError("Batch API currently only supported for 'gemini' provider.")
            
        self.api_key = clean_env_val(os.getenv("GEMINI_API_KEY"))
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        
        self.model = clean_env_val(
            os.getenv("GEMINI_MODEL") or os.getenv("GEMINI_API_MODEL") or "gemini-2.5-flash"
        )
        self.client = genai.Client(api_key=self.api_key)

    def create_batch_job(self, tasks: list[dict], prompt: str) -> str:
        """
        Creates a Batch Job using the Google GenAI SDK.
        tasks is a list of dict: {"id": "chunk_id", "path": Path}
        Returns the batch_job.name (the ID string).
        """
        requests_jsonl = []
        for task in tasks:
            image_path = task["path"]
            chunk_id = task["id"]
            
            image_bytes = image_path.read_bytes()
            mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            
            request_obj = {
                "id": chunk_id,
                "request": {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "inlineData": {
                                        "mimeType": mime_type,
                                        "data": encoded_image
                                    }
                                },
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.0
                    }
                }
            }
            requests_jsonl.append(json.dumps(request_obj))
            
        jsonl_content = "\n".join(requests_jsonl) + "\n"
        
        # Write temporarily to file
        temp_file = Path("temp_batch_upload.jsonl")
        temp_file.write_text(jsonl_content, encoding="utf-8")
        
        try:
            # Upload the file
            # the SDK requires mime_type inside config for non-standard files sometimes, 
            # but usually it auto-detects .jsonl as application/jsonl or text/plain.
            file_info = self.client.files.upload(
                file=str(temp_file),
                config=types.UploadFileConfig(mime_type="application/jsonl")
            )
            
            # Create batch job
            job = self.client.batches.create(
                model=self.model,
                src=file_info.name
            )
            return job.name
            
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def get_job_status(self, job_name: str) -> dict:
        """
        Returns the status of a batch job: PENDING, RUNNING, SUCCEEDED, FAILED, etc.
        Along with output_uri if succeeded.
        """
        job = self.client.batches.get(name=job_name)
        state_str = job.state.name if hasattr(job.state, "name") else str(job.state)
        state_str = state_str.replace("JobState.", "").replace("JOB_STATE_", "")
        return {
            "state": state_str,
            "output_uri": job.dest.file_name if getattr(job, "dest", None) else getattr(job, "output_uri", None),
            "error": getattr(job, "error", None)
        }

    def fetch_job_results(self, job_name: str) -> dict[str, str]:
        """
        Fetches and parses the results from a completed batch job.
        Returns a mapping of chunk_id -> generated_caption.
        """
        job_info = self.get_job_status(job_name)
        if "SUCCEEDED" not in job_info["state"]:
            raise ValueError(f"Job {job_name} is not SUCCEEDED. Current state: {job_info['state']}")
            
        output_uri = job_info["output_uri"]
        if not output_uri:
            return {}
            
        # The output_uri is usually a file resource URI like 'files/...' or a download link.
        # Developer API batch jobs save output to the files API.
        # Let's download it.
        # If output_uri is something like 'https://generativelanguage.googleapis.com/v1beta/files/xxx'
        # Or just 'files/xxx'.
        import requests
        
        if output_uri.startswith("files/") or not output_uri.startswith("http"):
            # Use SDK to download
            file_bytes = self.client.files.download(file=output_uri)
            text_content = file_bytes.decode("utf-8")
        else:
            # Fallback to requests if it's a raw URL
            download_url = f"{output_uri}&alt=media&key={self.api_key}" if "?" in output_uri else f"{output_uri}?alt=media&key={self.api_key}"
            res = requests.get(download_url)
            res.raise_for_status()
            text_content = res.text
        
        results = {}
        for line in text_content.strip().splitlines():
            if not line:
                continue
            data = json.loads(line)
            req_id = data.get("id")
            # Gemini Batch API response structure:
            # {"id": "...", "response": {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}}
            try:
                text = data["response"]["candidates"][0]["content"]["parts"][0]["text"]
                results[req_id] = text.strip()
            except (KeyError, IndexError, TypeError):
                results[req_id] = ""
                
        return results
