document.addEventListener('DOMContentLoaded', async () => {
  mermaid.initialize({ 
    startOnLoad: false, 
    theme: 'dark',
    fontFamily: 'Inter, sans-serif',
    flowchart: { htmlLabels: true, useMaxWidth: false }
  });

  const viewport = document.getElementById('slide-viewport');
  const indicator = document.getElementById('slide-indicator');
  const progressBar = document.getElementById('progress-bar');
  const notesBody = document.getElementById('notes-body');
  const notesDrawer = document.getElementById('notes-drawer');
  const overviewModal = document.getElementById('overview-modal');
  const overviewGrid = document.getElementById('overview-grid');

  let slides = [];
  let currentSlide = 0;

  try {
    const res = await fetch('slides.md?t=' + new Date().getTime());
    if (!res.ok) throw new Error('Failed to load slides.md');
    const text = await res.text();
    parseSlides(text);
    initRouter();
    renderSlide(currentSlide, false);
    setupEvents();
  } catch (err) {
    viewport.innerHTML = `<h2 style="color:red">Error loading slides: ${err.message}</h2>`;
  }

  function parseSlides(markdown) {
    const rawSlides = markdown.split(/\n---\n/);
    slides = rawSlides.map((raw, index) => {
      let content = raw.trim();
      let notes = '';

      // Extract notes
      const notesMatch = content.match(/Note:\s*([\s\S]*)$/);
      if (notesMatch) {
        notes = notesMatch[1].trim();
        content = content.replace(/Note:\s*([\s\S]*)$/, '');
      }

      // Inline stats and badges
      content = content.replace(/:::stat\s+(.*?)\s+\|\s+(.*?)\s+:::/g, '<div class="stat-card"><div class="stat-val">$1</div><div class="stat-lbl">$2</div></div>');
      content = content.replace(/\[badge-primary:\s*(.*?)\]/g, '<span class="badge badge-primary">$1</span>');
      content = content.replace(/\[badge-accent:\s*(.*?)\]/g, '<span class="badge badge-accent">$1</span>');
      content = content.replace(/\[badge-emerald:\s*(.*?)\]/g, '<span class="badge badge-emerald">$1</span>');
      content = content.replace(/\[badge:\s*(.*?)\]/g, '<span class="badge">$1</span>');

      // Add newlines around block directives so marked parses them into standalone <p> tags
      content = content.replace(/^:::(grid|box|callout|badges|stats)\s*$/gm, '\n\n:::$1\n\n');
      content = content.replace(/^:::\s*$/gm, '\n\n:::\n\n');

      let html = marked.parse(content);

      // Clean up block directives
      html = html.replace(/<p>:::grid<\/p>/g, '<div class="slide-grid">');
      html = html.replace(/<p>:::box<\/p>/g, '<div class="feature-box">');
      html = html.replace(/<p>:::callout<\/p>/g, '<div class="callout-box">');
      html = html.replace(/<p>:::badges<\/p>/g, '<div class="badge-group">');
      html = html.replace(/<p>:::stats<\/p>/g, '<div class="stats-grid">');
      html = html.replace(/<p>:::<\/p>/g, '</div>');
      
      // Table formatting
      html = html.replace(/<table>/g, '<table class="demo-table">');

      return {
        id: `slide-${index + 1}`,
        html,
        notes,
        raw
      };
    });
  }

  function renderSlide(index, animate = true) {
    if (index < 0 || index >= slides.length) return;
    currentSlide = index;

    const slide = slides[index];
    
    // Animation handling
    const oldCard = viewport.querySelector('.slide-card');
    if (oldCard && animate) {
      oldCard.classList.add('exiting');
      setTimeout(() => {
        injectNewCard(slide);
      }, 350);
    } else {
      injectNewCard(slide);
    }

    // Update UI
    indicator.textContent = `${index + 1} / ${slides.length}`;
    progressBar.style.width = `${((index + 1) / slides.length) * 100}%`;
    notesBody.innerHTML = marked.parse(slide.notes || '*No notes for this slide.*');
    
    // Hash router without triggering jump
    history.replaceState(null, null, `#${slide.id}`);
    
    // Update overview
    document.querySelectorAll('.thumb-card').forEach((el, i) => {
      el.classList.toggle('active', i === index);
    });
  }

  function injectNewCard(slide) {
    viewport.innerHTML = '';
    const card = document.createElement('div');
    card.className = 'slide-card entering';
    card.innerHTML = slide.html;
    viewport.appendChild(card);
    
    // Process mermaid
    const codes = card.querySelectorAll('pre code.language-mermaid');
    codes.forEach((codeBlock) => {
      const pre = codeBlock.parentNode;
      const mermaidDiv = document.createElement('div');
      mermaidDiv.className = 'mermaid';
      mermaidDiv.textContent = codeBlock.textContent;
      pre.parentNode.replaceChild(mermaidDiv, pre);
    });
    
    // Render mermaid
    if (card.querySelectorAll('.mermaid').length > 0) {
      mermaid.run({ nodes: card.querySelectorAll('.mermaid') }).catch(e => console.error(e));
    }

    // Trigger reflow and enter
    void card.offsetWidth; 
    card.classList.remove('entering');
  }

  function nextSlide() {
    if (currentSlide < slides.length - 1) renderSlide(currentSlide + 1);
  }

  function prevSlide() {
    if (currentSlide > 0) renderSlide(currentSlide - 1);
  }

  function toggleOverview() {
    if (overviewModal.classList.contains('hidden')) {
      renderOverview();
      overviewModal.classList.remove('hidden');
    } else {
      overviewModal.classList.add('hidden');
    }
  }

  function renderOverview() {
    overviewGrid.innerHTML = '';
    slides.forEach((slide, i) => {
      const thumb = document.createElement('div');
      thumb.className = `thumb-card ${i === currentSlide ? 'active' : ''}`;
      
      const titleMatch = slide.raw.match(/#+\s+(.*)/);
      const title = titleMatch ? titleMatch[1].replace(/<[^>]+>/g, '') : `Slide ${i + 1}`;
      
      thumb.innerHTML = `
        <div class="thumb-title">${title}</div>
        <div class="thumb-num">Slide ${i + 1}</div>
      `;
      thumb.onclick = () => {
        renderSlide(i, false);
        toggleOverview();
      };
      overviewGrid.appendChild(thumb);
    });
  }

  function toggleNotes() {
    notesDrawer.classList.toggle('hidden');
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }

  function setupEvents() {
    document.getElementById('btn-next').addEventListener('click', nextSlide);
    document.getElementById('btn-prev').addEventListener('click', prevSlide);
    document.getElementById('btn-overview').addEventListener('click', toggleOverview);
    document.getElementById('btn-close-overview').addEventListener('click', toggleOverview);
    document.getElementById('btn-notes').addEventListener('click', toggleNotes);
    document.getElementById('btn-close-notes').addEventListener('click', toggleNotes);
    document.getElementById('btn-fullscreen').addEventListener('click', toggleFullscreen);

    document.addEventListener('keydown', (e) => {
      if (overviewModal.classList.contains('hidden')) {
        switch(e.key) {
          case 'ArrowRight':
          case 'ArrowDown':
          case 'PageDown':
          case ' ':
            e.preventDefault();
            nextSlide();
            break;
          case 'ArrowLeft':
          case 'ArrowUp':
          case 'PageUp':
            e.preventDefault();
            prevSlide();
            break;
          case 'Home':
            e.preventDefault();
            renderSlide(0);
            break;
          case 'End':
            e.preventDefault();
            renderSlide(slides.length - 1);
            break;
        }
      } else {
        if (e.key === 'Escape') toggleOverview();
      }

      if (e.key.toLowerCase() === 'o') {
        e.preventDefault();
        toggleOverview();
      }
      if (e.key.toLowerCase() === 'n') {
        e.preventDefault();
        toggleNotes();
      }
      if (e.key.toLowerCase() === 'f') {
        e.preventDefault();
        toggleFullscreen();
      }
    });
  }

  function initRouter() {
    const hash = window.location.hash;
    if (hash && hash.startsWith('#slide-')) {
      const idx = parseInt(hash.replace('#slide-', '')) - 1;
      if (!isNaN(idx) && idx >= 0 && idx < slides.length) {
        currentSlide = idx;
      }
    }
  }
});
