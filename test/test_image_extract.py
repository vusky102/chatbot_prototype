import os
import sys
from pathlib import Path

# Add project root to python path to resolve functions package import
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from functions import extract_images

def run_test():
    pdf_path = project_root / "docs/Training_data_GD4/input/Public_035.pdf"
    output_dir = project_root / "output"

    print(f"Extracting images from: {pdf_path}")
    print(f"Target output directory: {output_dir}")

    try:
        result = extract_images(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            provider=None  # Autodetect from env (gemini / openai)
        )
        print("\n--- Extraction Results Summary ---")
        print(f"Status: Success")
        print(f"Embedded Images Extracted: {result['embedded_count']}")
        print(f"AI-detected Elements: {result['ai_extracted_count']}")
        print(f"Output Folder: {result['output_dir']}")
    except Exception as e:
        print(f"\n--- Extraction Failed ---")
        print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
