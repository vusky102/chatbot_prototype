import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Hero UI Prototype")

# 1. Custom CSS to style the layout and text to match Pinecone's feel
custom_css = """
<style>
    /* Reduce top padding of main container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Style the main title */
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        color: #1a202c; /* Dark text */
        line-height: 1.2;
        margin-bottom: 1rem;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Highlight the word 'context' */
    .hero-highlight {
        color: #0044ff; /* Pinecone blue */
    }
    
    /* Style the subtitle */
    .hero-subtitle {
        font-size: 1.25rem;
        color: #4a5568; /* Gray text */
        margin-bottom: 2rem;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Container for buttons */
    .button-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 4rem;
    }
    
    /* Custom Primary Button */
    .btn-primary {
        background-color: #0044ff;
        color: white !important;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        text-decoration: none;
        font-weight: 600;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        transition: background-color 0.2s;
    }
    .btn-primary:hover {
        background-color: #0033cc;
    }
    
    /* Custom Secondary Button */
    .btn-secondary {
        background-color: white;
        color: #1a202c !important;
        padding: 0.75rem 1.5rem;
        border-radius: 4px;
        text-decoration: none;
        font-weight: 600;
        border: 1px solid #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        transition: border-color 0.2s;
    }
    .btn-secondary:hover {
        border-color: #cbd5e0;
    }
    
    /* Hide the default Streamlit header */
    header {visibility: hidden;}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# 2. Define the Particle Animation HTML using tsParticles
particle_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <script src="https://cdn.jsdelivr.net/npm/tsparticles@2/tsparticles.bundle.min.js"></script>
  <style>
    body, html {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
    }
    #tsparticles {
      width: 100%;
      height: 100vh; /* Fill the component height */
      position: absolute;
      top: 0;
      left: 0;
      z-index: -1;
      background-color: transparent;
    }
  </style>
</head>
<body>
  <div id="tsparticles"></div>
  <script>
    tsParticles.load("tsparticles", {
      fpsLimit: 60,
      particles: {
        number: {
          value: 40,
          density: { enable: true, value_area: 800 }
        },
        color: { value: "#0044ff" }, /* Pinecone blue particles */
        shape: { type: "circle" },
        opacity: {
          value: 0.5,
          random: true,
          anim: { enable: true, speed: 1, opacity_min: 0.1, sync: false }
        },
        size: {
          value: 6,
          random: true,
          anim: { enable: true, speed: 2, size_min: 2, sync: false }
        },
        links: {
          enable: true,
          distance: 150,
          color: "#0044ff",
          opacity: 0.2,
          width: 1
        },
        move: {
          enable: true,
          speed: 1.5,
          direction: "none",
          random: true,
          straight: false,
          out_mode: "out",
          bounce: false,
        }
      },
      interactivity: {
        detectsOn: "canvas",
        events: {
          onHover: { enable: true, mode: "grab" },
          resize: true
        },
        modes: {
          grab: { distance: 140, links: { opacity: 0.5 } }
        }
      },
      retina_detect: true
    });
  </script>
</body>
</html>
"""

# 3. Build the layout
# We use columns to separate the text and the animation
col1, col2 = st.columns([1.2, 1]) # Adjust ratio to give left side slightly more room

with col1:
    # Add some top spacing to vertically center the text a bit
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    st.markdown('<div style="color: #0044ff; font-weight: 600; margin-bottom: 1rem;">BUILD KNOWLEDGEABLE AI</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="hero-title">Give agents <span class="hero-highlight">context</span></div>', 
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="hero-subtitle">Fast retrieval. Accurate results. Lower costs.<br>Start in seconds.</div>', 
        unsafe_allow_html=True
    )
    
    # Render Custom Buttons
    st.markdown(
        """
        <div class="button-container">
            <a href="#" class="btn-primary">Start Building</a>
            <a href="#" class="btn-secondary">Get a Demo</a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
with col2:
    # Embed the particle animation in the right column
    components.html(particle_html, height=500, scrolling=False)

# Optional: Add a simple logo ticker placeholder at the bottom
st.divider()
st.markdown('<div style="text-align: center; color: #718096; margin-bottom: 1rem;">TRUSTED BY INNOVATIVE TEAMS</div>', unsafe_allow_html=True)

ticker_html = """
<style>
.ticker-wrap {
    width: 100%;
    overflow: hidden;
    background-color: transparent;
    padding-left: 20%;
    box-sizing: content-box;
}
.ticker {
    display: inline-block;
    white-space: nowrap;
    padding-right: 100%;
    box-sizing: content-box;
    animation-iteration-count: infinite;
    animation-timing-function: linear;
    animation-name: ticker;
    animation-duration: 30s;
}
@keyframes ticker {
    0% { transform: translate3d(0, 0, 0); visibility: visible; }
    100% { transform: translate3d(-100%, 0, 0); }
}
.ticker-item {
    display: inline-block;
    padding: 0 2rem;
    font-size: 1.5rem;
    font-weight: bold;
    color: #a0aec0;
    font-family: sans-serif;
}
</style>
<div class="ticker-wrap">
    <div class="ticker">
        <div class="ticker-item">GONG</div>
        <div class="ticker-item">Delphi</div>
        <div class="ticker-item">Expensify</div>
        <div class="ticker-item">CISCO</div>
        <div class="ticker-item">zapier</div>
        <div class="ticker-item">sanofi</div>
    </div>
</div>
"""
st.markdown(ticker_html, unsafe_allow_html=True)
