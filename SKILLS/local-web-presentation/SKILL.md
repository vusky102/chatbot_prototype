---
name: local-web-presentation
description: Create, customize, and serve standalone local HTML/CSS slide deck presentations isolated from main backend logic
---

# Local Web Presentation Skill

A zero-dependency skill for creating, styling, and presenting modern, dark-themed HTML/CSS slide decks served on a simple local web server.

## Overview

This skill manages an isolated web application located at `docs/presentation/`. The presentation is 100% self-contained and completely independent of any project backend or database logic.

### Key Features
- **Modern UI**: HSL-tailored dark theme, glassmorphism cards, Google Fonts (`Outfit`, `Inter`, `Fira Code`), and animated slide transitions.
- **Markdown Driven**: Slides are dynamically parsed from `docs/presentation/slides.md`.
- **Keyboard Shortcuts**:
  - `Arrow Right` / `Arrow Down` / `Space` / `PageDown`: Next slide
  - `Arrow Left` / `Arrow Up` / `PageUp`: Previous slide
  - `Home` / `End`: Jump to start / end slide
  - `O` or `Esc`: Toggle slide visual grid overview
  - `N`: Toggle speaker notes overlay drawer
  - `F`: Toggle fullscreen presentation mode
- **Direct Anchors**: Slide links using hash URLs (e.g., `#slide-1`, `#slide-3`).

---

## Directory Structure

```
docs/presentation/
├── index.html        # Main HTML5 slide deck runner
├── styles.css        # Modern CSS design system & animations
├── app.js            # Client-side presentation engine & markdown parser
└── slides.md         # Slide content written in Markdown

SKILLS/local-web-presentation/
├── SKILL.md          # Skill documentation
└── scripts/
    └── present.py    # Zero-dependency Python CLI server script
```

---

## Usage

### 1. Launching the Presentation Server

To start the local HTTP server and view the presentation deck in your web browser:

```bash
python SKILLS/local-web-presentation/scripts/present.py serve
```

Options:
- `--port <number>`: Specify custom port (default: `8000`).
- `--no-open`: Disable auto-opening the browser.
- `--dir <path>`: Specify custom presentation directory.

Alternative native command (without script):
```bash
python -m http.server 8000 --directory docs/presentation
```

---

## Writing & Editing Slides

Edit `docs/presentation/slides.md` to update presentation content. 

### Slide Separator
Separate slides using `---` on its own line:

```markdown
# Slide 1 Title
Slide content here...

---

## Slide 2 Title
- Bullet point 1
- Bullet point 2
```

### Speaker Notes
Add speaker notes to any slide using `Note:` at the bottom of the slide:

```markdown
## Technical Overview
Details about the architecture...

Note: Remind the audience about performance benchmarks.
```

### Feature Grids & Cards
Create multi-column card layouts using `:::grid` and `:::box`:

```markdown
:::grid
:::box
### Feature A
Description of feature A.
:::
:::box
### Feature B
Description of feature B.
:::
:::
```

---

## Customizing Aesthetics

Theme variables can be customized directly in `docs/presentation/styles.css`:

- `--accent-primary`: Main accent color (default `#6366F1`)
- `--accent-secondary`: Cyan secondary color (default `#06B6D4`)
- `--bg-dark`: Page background (default `#090D16`)
- `--bg-card`: Glassmorphism card fill
