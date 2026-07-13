"""
AI-driven PDF Image and Non-text Element Extractor.

Supports two AI backends:
  - OpenAI (GPT-4o / GPT-4o-mini) via openai SDK
  - Google Gemini (gemini-2.5-flash etc.) via google-genai SDK

Usage:
  python image_extraction.py --path <pdf_or_dir> [--output <dir>] [--provider openai|gemini] [--dpi 300]
"""
import os
import argparse
import base64
import json
import re
from pathlib import Path
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def clean_env_val(val):
    if val is None:
        return None
    val = val.strip()
    if val.startswith(('"', "'")) and val.endswith(('"', "'")):
        val = val[1:-1]
    return val.strip()


def robust_json_loads(s):
    """
    Attempts to parse JSON from a string, repairing common LLM formatting errors
    such as missing closing square brackets in box_2d list values.
    """
    if not s:
        return {}
    
    s = s.strip()
    
    # 1. Strip markdown code block wrappers if present
    if s.startswith("```"):
        lines = s.splitlines()
        if len(lines) >= 2:
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            s = "\n".join(lines).strip()
            
    # 2. Try parsing directly
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
        
    # 3. Repair mismatched closing bracket for box_2d coordinate arrays
    # e.g. [ymin, xmin, ymax, xmax} -> [ymin, xmin, ymax, xmax]
    # We capture the trailing brace so we do not lose the object close token.
    s = re.sub(
        r'\[\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*([\}])',
        r'[\1, \2, \3, \4]\5',
        s
    )
    
    # Try parsing again
    return json.loads(s)


# ─── AI Provider Setup ───────────────────────────────────────────────────────

def get_openai_client():
    from openai import OpenAI

    api_key = clean_env_val(os.getenv("OPENAI_API_KEY"))
    base_url = clean_env_val(
        os.getenv("OPENAI_API_BASEURL") or os.getenv("OPENAI_BASE_URL")
    )
    model = clean_env_val(
        os.getenv("OPENAI_API_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    )

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env")

    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)

    return client, model


def get_gemini_client():
    from google import genai

    api_key = clean_env_val(os.getenv("GEMINI_API_KEY"))
    model = clean_env_val(
        os.getenv("GEMINI_MODEL") or os.getenv("GEMINI_API_MODEL") or "gemini-2.5-flash"
    )

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")

    client = genai.Client(api_key=api_key)
    return client, model


# ─── Vision Analysis ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an expert document analysis system. Your job is to identify all NON-TEXT "
    "visual elements on the uploaded PDF page image.\n\n"
    "Non-text elements include:\n"
    "- Tables (gridded or gridless structured data)\n"
    "- Charts & Graphs (bar, line, pie, scatter, etc.)\n"
    "- Diagrams & Schematics (flowcharts, architectures, blueprints)\n"
    "- Figures, Photos & Illustrations (photographs, vector graphics, product images)\n"
    "- Mathematical formulas or equations displayed as images\n"
    "- Drawings & Signatures\n\n"
    "Do NOT detect:\n"
    "- Plain paragraphs of text\n"
    "- Page headers, footers, page numbers\n"
    "- Small logos or decorative icons (under ~5% of page area)\n"
    "- Background watermarks or timestamps\n"
    "- Document header/footer tables (title blocks with document ID, version info, organization name)\n\n"
    "For each detected element, output:\n"
    "1. type: 'table', 'chart', 'diagram', 'figure', 'formula', 'signature', or 'other'\n"
    "2. description: A brief summary of what the element shows\n"
    "3. box_2d: Bounding box as [ymin, xmin, ymax, xmax] in PIXEL coordinates "
    "relative to the image dimensions provided. Be as accurate as possible.\n\n"
    "IMPORTANT ACCURACY RULES:\n"
    "- The bounding box must tightly enclose the visual element with minimal padding.\n"
    "- Do NOT guess or hallucinate elements that are not clearly visible.\n"
    "- If the page contains ONLY text, return contains_non_text_elements: false.\n\n"
    "Respond ONLY with valid JSON:\n"
    '{"contains_non_text_elements": true/false, "elements": [{"type": "...", '
    '"description": "...", "box_2d": [ymin, xmin, ymax, xmax]}]}'
)


def analyze_page_openai(client, model, png_bytes, img_width, img_height):
    """Use OpenAI Vision API to detect non-text elements."""
    base64_image = base64.b64encode(png_bytes).decode("utf-8")

    user_text = (
        f"Analyze this PDF page image ({img_width}x{img_height} pixels). "
        f"Return bounding boxes in pixel coordinates where x ranges from 0 to {img_width} "
        f"and y ranges from 0 to {img_height}. "
        f"Return any non-text elements as JSON."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.0,
    )

    try:
        return robust_json_loads(response.choices[0].message.content)
    except Exception as e:
        print("\n--- DEBUG: RAW OPENAI RESPONSE START ---")
        print(response.choices[0].message.content)
        print("--- DEBUG: RAW OPENAI RESPONSE END ---\n")
        raise e


def analyze_page_gemini(client, model, png_bytes, img_width, img_height):
    """Use Google Gemini Vision API to detect non-text elements."""
    from google.genai import types

    user_text = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Analyze this PDF page image ({img_width}x{img_height} pixels). "
        f"Return bounding boxes in pixel coordinates where x ranges from 0 to {img_width} "
        f"and y ranges from 0 to {img_height}. "
        f"Return any non-text elements as JSON."
    )

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
                    types.Part.from_text(text=user_text),
                ],
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        ),
    )

    try:
        return robust_json_loads(response.text)
    except Exception as e:
        print("\n--- DEBUG: RAW GEMINI RESPONSE START ---")
        print(response.text)
        print("--- DEBUG: RAW GEMINI RESPONSE END ---\n")
        raise e


# ─── Page Rendering & Cropping ───────────────────────────────────────────────

def render_page_to_png(page, target_dpi=150):
    """Renders a PDF page to PNG bytes at the given DPI."""
    zoom = target_dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png"), pix.width, pix.height


def crop_and_save_element(page, box_2d, render_width, render_height, output_path, dpi=300):
    """
    Crops a region from the PDF page based on PIXEL coordinates from the rendered
    image, then re-renders at high DPI for output quality.
    """
    ymin, xmin, ymax, xmax = box_2d

    page_width = page.rect.width
    page_height = page.rect.height

    # Convert pixel coords (from rendered image) to PDF points
    x0 = (xmin / render_width) * page_width
    y0 = (ymin / render_height) * page_height
    x1 = (xmax / render_width) * page_width
    y1 = (ymax / render_height) * page_height

    # Add small padding (2% of dimension)
    pad_x = (x1 - x0) * 0.02
    pad_y = (y1 - y0) * 0.02
    x0 = max(0, x0 - pad_x)
    y0 = max(0, y0 - pad_y)
    x1 = min(page_width, x1 + pad_x)
    y1 = min(page_height, y1 + pad_y)

    rect = fitz.Rect(x0, y0, x1, y1)
    rect.intersect(page.rect)

    if rect.is_empty or rect.width < 10 or rect.height < 10:
        print(f"    Warning: Box {box_2d} results in too-small crop region. Skipping.")
        return False

    # Skip elements in header region (top 12%) or footer region (bottom 8%)
    center_y = (y0 + y1) / 2
    if center_y < page_height * 0.12:
        print(f"    Warning: Element center is in header region. Skipping.")
        return False
    if center_y > page_height * 0.92:
        print(f"    Warning: Element center is in footer region. Skipping.")
        return False

    # Check if crop area is too small relative to page (likely a logo/icon)
    area_ratio = (rect.width * rect.height) / (page_width * page_height)
    if area_ratio < 0.02:
        print(f"    Warning: Crop area is only {area_ratio*100:.1f}% of page — likely a small icon. Skipping.")
        return False

    # Render crop at high DPI
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=rect)

    # Validate: check if the crop is mostly blank (>95% white pixels)
    samples = pix.samples
    total_pixels = pix.width * pix.height
    n = pix.n  # components per pixel
    white_count = 0
    step = max(1, total_pixels // 5000)  # Sample ~5000 pixels for speed
    for p in range(0, len(samples), n * step):
        if p + min(n, 3) <= len(samples):
            if all(samples[p + c] > 245 for c in range(min(n, 3))):
                white_count += 1
    sampled = total_pixels // step
    white_pct = (white_count / max(sampled, 1)) * 100

    if white_pct > 95:
        print(f"    Warning: Crop is {white_pct:.0f}% white — likely blank/mislocated. Skipping.")
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pix.save(output_path)
    return True


# ─── Embedded Image Extraction (No AI needed) ───────────────────────────────

def extract_embedded_images(doc, page, page_num, output_dir, min_size=50):
    """
    Extract actual embedded raster images from the PDF page using PyMuPDF.
    No AI needed — these are image objects stored in the PDF.
    Filters out tiny images (logos, icons) by min_size threshold.
    """
    images = page.get_images(full=True)
    extracted = 0

    for img_idx, img in enumerate(images):
        xref = img[0]
        try:
            base_image = doc.extract_image(xref)
        except Exception:
            continue

        w = base_image["width"]
        h = base_image["height"]

        # Skip tiny images (logos, icons)
        if w < min_size or h < min_size:
            continue

        ext = base_image["ext"]
        img_bytes = base_image["image"]

        out_name = f"page_{page_num + 1}_embedded_{img_idx + 1}.{ext}"
        out_path = output_dir / out_name
        os.makedirs(str(output_dir), exist_ok=True)

        with open(str(out_path), "wb") as f:
            f.write(img_bytes)

        print(f"    -> Embedded image: {out_name} ({w}x{h})")
        extracted += 1

    return extracted


# ─── Main Processing ─────────────────────────────────────────────────────────

def process_pdf(pdf_path, output_dir, ai_client, model, provider, render_dpi=150, crop_dpi=300):
    """Processes a single PDF file, extracting both embedded images and AI-detected elements."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        msg = f"Error: PDF path '{pdf_path}' does not exist."
        print(msg)
        return {
            "embedded_count": 0,
            "ai_extracted_count": 0,
            "output_dir": None,
            "error": msg
        }

    print(f"\n{'='*60}")
    print(f"Processing: {pdf_path.name}")
    print(f"Provider: {provider} | Model: {model}")
    print(f"{'='*60}")

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return {
            "embedded_count": 0,
            "ai_extracted_count": 0,
            "output_dir": None,
            "error": str(e)
        }

    pdf_output_dir = Path(output_dir) / pdf_path.stem
    total_embedded = 0
    total_ai_extracted = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"\n  Page {page_num + 1}/{len(doc)}")

        # Phase 1: Extract embedded raster images (no AI)
        embedded = extract_embedded_images(doc, page, page_num, pdf_output_dir)
        total_embedded += embedded

        # Phase 2: AI-powered visual element detection
        print(f"    AI analyzing...", end="", flush=True)
        try:
            png_bytes, img_w, img_h = render_page_to_png(page, target_dpi=render_dpi)

            if provider == "gemini":
                analysis = analyze_page_gemini(ai_client, model, png_bytes, img_w, img_h)
            else:
                analysis = analyze_page_openai(ai_client, model, png_bytes, img_w, img_h)

            if not analysis.get("contains_non_text_elements") or not analysis.get("elements"):
                print(" No visual elements detected.")
                continue

            elements = analysis["elements"]
            print(f" Found {len(elements)} element(s).")

            for idx, element in enumerate(elements):
                el_type = element.get("type", "other").lower()
                box_2d = element.get("box_2d")
                desc = element.get("description", "")

                if not box_2d or len(box_2d) != 4:
                    print(f"    - Element {idx+1}: Invalid box {box_2d}. Skipping.")
                    continue

                # Validate box values are reasonable
                ymin, xmin, ymax, xmax = box_2d
                if ymin >= ymax or xmin >= xmax:
                    print(f"    - Element {idx+1}: Inverted box {box_2d}. Skipping.")
                    continue

                out_name = f"page_{page_num + 1}_{el_type}_{idx + 1}.png"
                out_path = pdf_output_dir / out_name

                success = crop_and_save_element(
                    page, box_2d, img_w, img_h, str(out_path), dpi=crop_dpi
                )
                if success:
                    print(f"    -> Saved: {out_name} ({desc[:60]})")
                    total_ai_extracted += 1

        except Exception as e:
            print(f" Error: {e}")

    print(f"\n  Summary for {pdf_path.name}:")
    print(f"    Embedded images extracted: {total_embedded}")
    print(f"    AI-detected elements extracted: {total_ai_extracted}")
    doc.close()

    return {
        "embedded_count": total_embedded,
        "ai_extracted_count": total_ai_extracted,
        "output_dir": pdf_output_dir
    }


def extract_images(pdf_path, output_dir="output", provider=None, render_dpi=150, crop_dpi=300):
    """
    Exposes a clean, programmatic function to extract images and non-text visual elements from a PDF.
    
    If 'provider' is None (default), it will automatically select 'gemini' if GEMINI_API_KEY
    is set, or 'openai' if OPENAI_API_KEY is set.
    """
    if not provider:
        if os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        else:
            raise ValueError(
                "Neither GEMINI_API_KEY nor OPENAI_API_KEY was found in environment. "
                "Please set one of these keys in your environment or write it to .env."
            )

    if provider == "gemini":
        ai_client, model = get_gemini_client()
    elif provider == "openai":
        ai_client, model = get_openai_client()
    else:
        raise ValueError(f"Unsupported provider specified: {provider}")

    return process_pdf(
        pdf_path=pdf_path,
        output_dir=output_dir,
        ai_client=ai_client,
        model=model,
        provider=provider,
        render_dpi=render_dpi,
        crop_dpi=crop_dpi
    )


def main():
    parser = argparse.ArgumentParser(
        description="AI-driven PDF Image and Non-text Element Extractor.\n"
                    "Supports OpenAI and Google Gemini as vision backends.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path", type=str, required=True,
        help="Path to a PDF file or directory containing PDF files.",
    )
    parser.add_argument(
        "--output", type=str, default="output",
        help="Root directory for extracted images (default: output).",
    )
    parser.add_argument(
        "--provider", type=str, default="gemini", choices=["openai", "gemini"],
        help="AI provider to use: 'openai' or 'gemini' (default: gemini).",
    )
    parser.add_argument(
        "--render-dpi", type=int, default=150,
        help="DPI for rendering pages for AI analysis (default: 150).",
    )
    parser.add_argument(
        "--crop-dpi", type=int, default=300,
        help="DPI for final cropped output images (default: 300).",
    )

    args = parser.parse_args()

    # Setup AI client
    try:
        if args.provider == "gemini":
            client, model = get_gemini_client()
        else:
            client, model = get_openai_client()
        print(f"Using {args.provider} provider with model: {model}")
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    path_to_process = Path(args.path)

    if path_to_process.is_file():
        if path_to_process.suffix.lower() == ".pdf":
            process_pdf(
                path_to_process, args.output, client, model,
                args.provider, args.render_dpi, args.crop_dpi,
            )
        else:
            print("Provided file must be a .pdf")
    elif path_to_process.is_dir():
        pdf_files = sorted(path_to_process.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in: {path_to_process}")
            return
        print(f"Found {len(pdf_files)} PDF files.")
        for pdf_file in pdf_files:
            process_pdf(
                pdf_file, args.output, client, model,
                args.provider, args.render_dpi, args.crop_dpi,
            )
    else:
        print("Provided path does not exist.")


if __name__ == "__main__":
    main()
