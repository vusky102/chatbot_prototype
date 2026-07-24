from src.config import Settings
from src.ingest.batch_pipeline import finalize_batch_job
import logging

logging.basicConfig(level=logging.INFO)

settings = Settings()
try:
    res = finalize_batch_job("9fcfc3d0-e226-40cd-8696-c92a3144658f", settings)
    print("Success!", res)
except Exception as e:
    import traceback
    traceback.print_exc()
