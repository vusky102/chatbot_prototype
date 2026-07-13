---
name: pdf-image-extraction
description: Extract images and non-text visual elements (tables, charts, diagrams) from PDF files using AI vision + PyMuPDF
---

# PDF Image Extraction Skill

Extract embedded images and AI-detected visual elements (tables, charts, diagrams, figures) from PDF documents.

## Overview

This skill provides two extraction methods:

### 1. Embedded Image Extraction (No AI)
Uses PyMuPDF (`fitz`) to directly extract raster image objects stored inside the PDF.
- Fast, no API calls needed
- Only finds actual embedded images (photos, inserted pictures)
- Cannot find vector-drawn tables, charts, or diagrams

### 2. AI Vision-Based Extraction
Renders each PDF page to PNG, sends to a vision AI model, and crops detected visual elements.
- Finds tables, charts, diagrams, figures that are drawn as vectors
- Requires an AI API key (OpenAI or Google Gemini)
- Quality depends heavily on the model used

## Supported AI Providers

| Provider | Model | Spatial Accuracy | Speed | Cost |
|----------|-------|-----------------|-------|------|
| Google Gemini | `gemini-2.5-flash` | ★★★★☆ | Fast | Low |
| OpenAI | `gpt-4o` | ★★★★☆ | Medium | High |
| OpenAI | `gpt-4o-mini` | ★★☆☆☆ | Fast | Low |

> [!IMPORTANT]
> **GPT-4o-mini is NOT recommended** for this task. It produces inaccurate bounding boxes
> and hallucinates elements, resulting in blank/white cropped images.
> Use `gemini-2.5-flash` or `gpt-4o` for reliable results.

## Prerequisites

```bash
pip install pymupdf openai google-genai python-dotenv
```

## Configuration

Add API keys to `.env`:

```env
# For Gemini (recommended)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# For OpenAI 
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_MODEL=gpt-4o
```

## Usage

### Single PDF
```bash
python image_extraction.py --path docs/input/sample.pdf --provider gemini
```

### Directory of PDFs
```bash
python image_extraction.py --path docs/input/ --output output/ --provider gemini
```

### All options
```bash
python image_extraction.py \
  --path <pdf_or_directory> \
  --output <output_dir>     \
  --provider gemini|openai  \
  --render-dpi 150          \
  --crop-dpi 300
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--path` | (required) | PDF file or directory path |
| `--output` | `output` | Output directory for extracted images |
| `--provider` | `gemini` | AI backend: `gemini` or `openai` |
| `--render-dpi` | `150` | DPI for page rendering (sent to AI) |
| `--crop-dpi` | `300` | DPI for final cropped output images |

## Output Structure

```
output/
└── Public_001/
    ├── page_1_embedded_1.jpeg    # Directly extracted image
    ├── page_3_table_1.png        # AI-detected table
    ├── page_5_chart_1.png        # AI-detected chart
    └── page_7_diagram_1.png      # AI-detected diagram
```

## Quality Safeguards

The script includes automatic validation to prevent blank/bad crops:
- **White pixel check**: Crops that are >95% white are automatically skipped
- **Area ratio filter**: Elements <2% of page area (logos, icons) are skipped
- **Box validation**: Inverted or invalid bounding boxes are rejected
- **Minimum size**: Crops smaller than 10×10 PDF points are skipped

## Troubleshooting

### Getting mostly blank/white images
- Switch from `gpt-4o-mini` to `gemini-2.5-flash` or `gpt-4o`
- The model may be hallucinating elements — blank validation should now auto-skip these

### No elements detected on pages that have visual content
- Try increasing `--render-dpi` to 200 for clearer AI input
- Check if the visual elements are actually embedded images (use `--provider` flag)

### API errors
- Verify your API key in `.env` is correct and has vision capabilities
- Ensure the model name matches exactly (e.g., `gemini-2.5-flash`, not `Gemini 2.5 Flash`)
