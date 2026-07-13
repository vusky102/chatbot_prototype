import os
import argparse
import base64
import json
from pathlib import Path
import fitz  # PyMuPDF
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def clean_env_val(val):
    if val is None:
        return None
    val = val.strip()
    if val.startswith(('"', "'")) and val.endswith(('"', "'")):
        val = val[1:-1]
    return val.strip()

def get_openai_client():
    api_key = clean_env_val(os.getenv("OPENAI_API_KEY"))
    
    # Try multiple common key names for URL and Model
    base_url = clean_env_val(os.getenv("OPENAI_API_BASEURL") or os.getenv("OPENAI_BASE_URL"))
    model = clean_env_val(os.getenv("OPENAI_API_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment or .env file. Please configure it."
        )

    # Allow custom base url (e.g. for compatible vision models)
    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)

    return client, model

def page_to_base64_png(page, target_dpi=150):
    """Renders a PDF page to base64 encoded PNG bytes."""
    # Render page to a pixmap
    zoom = target_dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    return base64.b64encode(png_bytes).decode("utf-8")

def analyze_page_for_non_text_elements(client, model, base64_image):
    """Hits the OpenAI Vision API and returns parsed non-text element locations."""
    system_prompt = (
        "You are an expert document analysis system. Your job is to identify all NON-TEXT elements "
        "on the uploaded PDF page image. Non-text elements include:\n"
        "- Tables (gridded or gridless lists of structured data)\n"
        "- Charts & Graphs (bar charts, line graphs, pie charts, scatter plots)\n"
        "- Diagrams & Schematics (flowcharts, architectures, blueprint drawings)\n"
        "- Figures, Photos & Illustrations (photographs, paintings, clipart, vector graphics, product images)\n"
        "- Drawings & Signatures\n\n"
        "Do NOT detect general paragraphs of text, page headers, footers, page numbers, or background decorations.\n"
        "For each detected element, output:\n"
        "1. The type of element (e.g., 'table', 'chart', 'diagram', 'figure', 'signature', 'other').\n"
        "2. A brief, descriptive summary of what it displays.\n"
        "3. A 2D bounding box [ymin, xmin, ymax, xmax] relative to the overall page image coordinates normalized on a 0 to 1000 scale.\n"
        "   - ymin represents the top edge distance from top.\n"
        "   - xmin represents the left edge distance from left.\n"
        "   - ymax represents the bottom edge distance from top.\n"
        "   - xmax represents the right edge distance from left.\n\n"
        "Respond ONLY with a valid JSON object of the following format:\n"
        "{\n"
        '  "contains_non_text_elements": true/false,\n'
        '  "elements": [\n'
        "    {\n"
        '      "type": "table/chart/diagram/figure/signature/other",\n'
        '      "description": "Short description of what the element shows",\n'
        '      "box_2d": [ymin, xmin, ymax, xmax]\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this PDF page image and return any non-text elements in JSON format."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.0
    )

    result_text = response.choices[0].message.content
    return json.loads(result_text)

def crop_and_save_element(page, box_2d, output_path, dpi=300):
    """Crops a region from the PDF page based on normalized 0-1000 coordinates & saves it."""
    ymin, xmin, ymax, xmax = box_2d

    # Get page dimensions in points (72 points per inch)
    page_width = page.rect.width
    page_height = page.rect.height

    # Convert 0-1000 normalized coordinates to PDF page points
    x0 = (xmin / 1000.0) * page_width
    y0 = (ymin / 1000.0) * page_height
    x1 = (xmax / 1000.0) * page_width
    y1 = (ymax / 1000.0) * page_height

    # Create rect for cropping. Ensure a tiny margin and valid boundaries
    rect = fitz.Rect(x0, y0, x1, y1)
    
    # Clip rect to page boundary to be safe
    rect.intersect(page.rect)

    if rect.is_empty or rect.width < 5 or rect.height < 5:
        print(f"Warning: Calculated box {box_2d} results in an empty or too-small crop region.")
        return False

    # Render crop area at designated dpi (e.g. 300 dpi for good print quality)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=rect)

    # Save pixmap as PNG
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pix.save(output_path)
    return True

def process_pdf(pdf_path, output_dir, client, model):
    """Processes a single PDF file, page by page, extracting non-text elements."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF path '{pdf_path}' does not exist.")
        return

    print(f"\nProcessing PDF: {pdf_path.name}...")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return

    pdf_output_name = pdf_path.stem
    pdf_output_dir = Path(output_dir) / pdf_output_name

    total_extracted = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"  Analyzing Page {page_num + 1}/{len(doc)}...", end="", flush=True)

        try:
            # 1. Render page to base64
            base64_image = page_to_base64_png(page, target_dpi=150)

            # 2. Vision API analysis
            analysis = analyze_page_for_non_text_elements(client, model, base64_image)

            # Check if elements were found
            if not analysis.get("contains_non_text_elements") or not analysis.get("elements"):
                print(" No non-text elements detected.")
                continue

            elements = analysis["elements"]
            print(f" Detected {len(elements)} element(s). Saving...")

            # 3. Crop and save detected elements
            for idx, element in enumerate(elements):
                el_type = element.get("type", "other").lower()
                box_2d = element.get("box_2d")

                if not box_2d or len(box_2d) != 4:
                    print(f"    - Skipping element {idx + 1}: Invalid bounding box {box_2d}")
                    continue

                desc = element.get("description", "Non-text element")
                output_filename = f"page_{page_num + 1}_{el_type}_{idx + 1}.png"
                output_filepath = pdf_output_dir / output_filename

                # Crop at high quality (300 DPI)
                success = crop_and_save_element(page, box_2d, str(output_filepath), dpi=300)
                if success:
                    print(f"    -> Extracted: {output_filename} ({desc[:50]}...)")
                    total_extracted += 1

        except Exception as e:
            print(f" Error analyzing page {page_num + 1}: {e}")

    print(f"Finished processing {pdf_path.name}. Total elements extracted: {total_extracted}")
    doc.close()

def main():
    parser = argparse.ArgumentParser(description="AI-driven PDF Image and Non-text element extractor.")
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Path to a PDF file or directory containing PDF files."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Root directory where the extracted image files will be saved."
    )

    args = parser.parse_args()

    try:
        client, model = get_openai_client()
    except ValueError as e:
        print(e)
        return

    path_to_process = Path(args.path)

    if path_to_process.is_file():
        if path_to_process.suffix.lower() == ".pdf":
            process_pdf(path_to_process, args.output, client, model)
        else:
            print("Provided file path must have a .pdf extension.")
    elif path_to_process.is_dir():
        pdf_files = list(path_to_process.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in directory: {path_to_process}")
            return
        print(f"Found {len(pdf_files)} PDF files in directory.")
        for pdf_file in pdf_files:
            process_pdf(pdf_file, args.output, client, model)
    else:
        print("Provided path does not exist. Check --path argument.")

if __name__ == "__main__":
    main()
