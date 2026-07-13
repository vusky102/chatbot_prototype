import re
from pypdf import PdfReader

def clean_vietnamese_spacing(text):
    # Tone vowels list
    tone_vowels = (
        "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ"
        "ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮÝỲỶỸỴđĐ"
    )

    # 1. Spacing errors between vowels (diphthongs/triphthongs)
    text = re.sub(r"i\s+([ếệểềễ])", r"i\1", text)
    text = re.sub(r"I\s+([ẾỆỂỀỄ])", r"I\1", text)
    text = re.sub(r"u\s+([ốộổồỗớợởờỡầấậẩẫýỳỷỹỵ])", r"u\1", text)
    text = re.sub(r"U\s+([ỐỘỔỒỖỚỢỞỜỠẦẤẬẨẪÝỲỶỸỴ])", r"U\1", text)
    text = re.sub(r"y\s+([ếệểềễ])", r"y\1", text)
    text = re.sub(r"Y\s+([ẾỆỂỀỄ])", r"Y\1", text)
    text = re.sub(r"o\s+([áàảãạằắặẳẵ])", r"o\1", text)
    text = re.sub(r"O\s+([ÁÀẢÃẠẰẮẶẨẪ])", r"O\1", text)
    text = re.sub(r"ư\s+([ớờởợỡ])", r"ư\1", text)
    text = re.sub(r"Ư\s+([ỚỜỞỢỠ])", r"Ư\1", text)

    # 2. Consonant clusters (e.g. tr, th, ph, kh, ch, nh, ng, ngh, gi, qu) followed by space + vowel
    text = re.sub(rf"\b(ch|kh|ph|th|tr|gi|nh|ng|ngh|qu|CH|KH|PH|TH|TR|GI|NH|NG|NGH|QU)\s+([{tone_vowels}aeiouyAEIOUY])", r"\1\2", text)

    # 3. Single initials (b, c, d, đ, g, h, k, l, m, n, p, q, r, s, t, v, x) followed by space + vowel
    text = re.sub(rf"\b([b-df-hj-np-tv-zB-DF-HJ-NP-TV-ZđĐ])\s+([{tone_vowels}aeiouyAEIOUY])", r"\1\2", text)

    # Normalize spacing
    text = re.sub(r" {2,}", " ", text)
    return text

def format_headings(text):
    lines = text.split("\n")
    formatted_lines = []
    for line in lines:
        stripped = line.strip()
        # Level 4: e.g. 1.2.1.1. Đo điều kiện nhà
        m4 = re.match(r"^(\d+\.\d+\.\d+\.\d+)\.?\s+(.+)$", stripped)
        if m4:
            formatted_lines.append(f"#### {m4.group(2)}")
            continue
        
        # Level 3: e.g. 1.2.1 Dịch vụ nhà thông minh
        m3 = re.match(r"^(\d+\.\d+\.\d+)\.?\s+(.+)$", stripped)
        if m3:
            formatted_lines.append(f"### {m3.group(2)}")
            continue
            
        # Level 2: e.g. 1.1 Giới thiệu
        m2 = re.match(r"^(\d+\.\d+)\.?\s+(.+)$", stripped)
        if m2:
            formatted_lines.append(f"## {m2.group(2)}")
            continue
            
        # Level 1: e.g. 1. Nội dung chính
        m1 = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if m1:
            if len(m1.group(2)) < 80:
                formatted_lines.append(f"# {m1.group(2)}")
                continue
        
        formatted_lines.append(line)
        
    return "\n".join(formatted_lines)

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    seen_headers = set()
    
    for page_counter, page in enumerate(reader.pages, 1):
        header_parts = []
        body_parts = []
        
        def visitor(fragment_text, cm, tm, font_dict, font_size):
            y = tm[5]
            if y >= 700:
                header_parts.append(fragment_text)
            else:
                body_parts.append(fragment_text)
                
        page.extract_text(visitor_text=visitor)
        
        # Process header
        header_text = "".join(header_parts)
        cleaned_header = clean_vietnamese_spacing(header_text).strip()
        normalized_header = " ".join(cleaned_header.split())
        
        # Check for duplicate headers
        include_header = False
        if normalized_header:
            if normalized_header not in seen_headers:
                seen_headers.add(normalized_header)
                include_header = True
        
        # Process body
        body_text = "".join(body_parts)
        page_text = clean_vietnamese_spacing(body_text)
        
        # Prepend header if it's the first time we see it
        if include_header:
            cleaned_header_text = clean_vietnamese_spacing(header_text)
            page_text = cleaned_header_text + "\n" + page_text
        
        # Format headings
        page_text = format_headings(page_text)
        
        # Append page marker (using comments so it doesn't pollute the text body)
        text += f"\n<!-- Page: {page_counter} -->\n" + page_text + "\n"

    return text

if __name__ == "__main__":
    import os
    os.makedirs("docs/Training_data_GD4/output/Public_035", exist_ok=True)
    public_035 = extract_text_from_pdf("docs/Training_data_GD4/input/Public_035.pdf")
    with open("docs/Training_data_GD4/output/Public_035/Public_035.txt", "w", encoding="utf-8") as f:
        f.write(public_035)