import streamlit as st
import requests
import json
import os
import time
import re
import base64

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="GenAI Story Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Custom CSS Styling
# -------------------------------
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .story-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    .story-text {
        font-family: 'Georgia', serif;
        font-size: 18px;
        line-height: 1.6;
        color: #2c3e50;
        text-align: justify;
        white-space: pre-line;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    .story-stats {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 14px;
        color: #1565c0;
    }
    .tts-controls {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
        text-align: center;
    }
    .tts-button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        margin: 0.5rem;
        transition: all 0.3s ease;
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 14px;
        margin-top: 3rem;
        padding: 2rem 0;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Header
# -------------------------------
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 3rem; font-weight: 300;">GenAI Story Generator</h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">by Abi Karimireddy</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# API Configuration
# -------------------------------
def get_api_credentials():
    try:
        return {
            "api_key": st.secrets["IBM_API_KEY"],
            "project_id": st.secrets["IBM_PROJECT_ID"],
            "region": st.secrets["IBM_REGION"]
        }
    except:
        return {
            "api_key": os.getenv("IBM_API_KEY", "your-api-key"),
            "project_id": os.getenv("IBM_PROJECT_ID", "your-project-id"),
            "region": os.getenv("IBM_REGION", "us-south")
        }

CREDENTIALS = get_api_credentials()
VERSION = "2023-05-29"

# Model options
MODEL_OPTIONS = {
    "Google Flan-UL2": "google/flan-ul2",
    "IBM Granite-13B": "ibm/granite-13b-instruct-v2",
    "Meta Llama-2-70B": "meta-llama/llama-2-70b-chat",
    "Google Flan-T5-XXL": "google/flan-t5-xxl"
}

# -------------------------------
# FIXED Prompt Builder - Ensures Character Name & Settings Match
# -------------------------------
def create_story_prompt(character_name, story_type, context, writing_style, length_category, mood, setting):
    """Create a precise prompt that enforces all parameters and story context"""
    
    # Word count mapping
    word_counts = {
        "Short (300-500 words)": "400-500",
        "Medium (500-800 words)": "650-750", 
        "Long (800-1200 words)": "900-1000"
    }
    target_words = word_counts[length_category]
    
    # Enhanced prompt that focuses on the provided context
    prompt = f"""You are a professional story writer. Write a complete {story_type.lower()} story that follows this EXACT plot and context:

MAIN CHARACTER: {character_name} (use this exact name throughout)
SETTING: {setting} 
GENRE: {story_type}
MOOD: {mood}
WRITING STYLE: {writing_style}
TARGET LENGTH: {target_words} words

MANDATORY STORY CONTEXT (you MUST follow this plot):
{context}

CRITICAL INSTRUCTIONS:
1. Follow the provided story context EXACTLY - do not deviate from the plot points given
2. Use "{character_name}" as the protagonist's name throughout
3. Maintain {story_type.lower()} genre elements consistently
4. Keep the {mood.lower()} atmosphere throughout
5. Set the story in {setting} with appropriate details
6. Write a complete story with proper beginning, middle, and satisfying ending
7. Include dialogue and action that advances the plot
8. Make sure all plot points from the context are included and resolved
9. Write approximately {target_words} words
10. End the story properly - do not leave it incomplete or cut off

Remember: The story context provided contains the EXACT plot you must follow. Do not change major plot points, character names, or the sequence of events. Expand on the details while staying true to the given storyline.

Write the complete story now:

# -------------------------------
# FIXED IBM Watson API Integration
# -------------------------------
def get_iam_token(api_key):
    """Get IBM Cloud IAM token"""
    try:
        url = "https://iam.cloud.ibm.com/identity/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        return None

def generate_story_watson(prompt, model_id, max_tokens, temperature):
    """Generate story with Watson AI - FIXED version"""
    token = get_iam_token(CREDENTIALS["api_key"])
    if not token:
        return "Error: Authentication failed"

    try:
        url = f"https://{CREDENTIALS['region']}.ml.cloud.ibm.com/ml/v1/text/generation?version={VERSION}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Fixed parameters for better story generation
        payload = {
            "model_id": model_id,
            "input": prompt,
            "project_id": CREDENTIALS["project_id"],
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "min_new_tokens": max(200, max_tokens // 2),  # Ensure substantial length
                "top_k": 40,
                "top_p": 0.85,
                "repetition_penalty": 1.3,
                "decoding_method": "sample",
                "stop_sequences": ["THE END", "---", "STORY COMPLETE", "[END]"],
                "include_stop_sequence": False,
                "truncate_input_tokens": 4000
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            story = data["results"][0]["generated_text"].strip()
            return format_story(story)
        else:
            return "Error: No story generated. Please try again."
            
    except Exception as e:
        return f"Error: {str(e)}"

def format_story(story):
    """Clean up and format the story"""
    # Remove extra whitespace
    story = re.sub(r'\s+', ' ', story)
    
    # Create paragraphs (every 3-4 sentences)
    sentences = [s.strip() for s in story.split('.') if s.strip()]
    paragraphs = []
    current_para = []
    
    for i, sentence in enumerate(sentences):
        current_para.append(sentence)
        if len(current_para) >= 3 or i == len(sentences) - 1:
            paragraphs.append('. '.join(current_para) + '.')
            current_para = []
    
    return '\n\n'.join(paragraphs).strip()

def get_story_stats(story):
    """Calculate story statistics"""
    words = len(story.split())
    sentences = len([s for s in story.split('.') if s.strip()])
    paragraphs = len([p for p in story.split('\n\n') if p.strip()])
    
    return {
        "words": words,
        "sentences": sentences, 
        "paragraphs": paragraphs,
        "reading_time": max(1, words // 200)
    }

# -------------------------------
# Text-to-Speech Function
# -------------------------------
def create_tts_html(text):
    """Generate TTS controls"""
    clean_text = re.sub(r'[^\w\s\.,!?;:]', '', text)
    
    return f"""
    <div class="tts-controls">
        <h4>🎧 Listen to Your Story</h4>
        <button onclick="playStory()" class="tts-button">🔊 Play</button>
        <button onclick="pauseStory()" class="tts-button">⏸️ Pause</button>
        <button onclick="stopStory()" class="tts-button">⏹️ Stop</button>
        <div id="status" style="margin-top: 1rem;"></div>
    </div>
    
    <script>
        let synth = window.speechSynthesis;
        let utterance = null;
        let isPaused = false;
        
        function playStory() {{
            if (isPaused) {{
                synth.resume();
                isPaused = false;
                document.getElementById('status').textContent = 'Playing...';
                return;
            }}
            
            if (synth.speaking) synth.cancel();
            
            utterance = new SpeechSynthesisUtterance(`{clean_text}`);
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            
            utterance.onstart = () => document.getElementById('status').textContent = 'Playing...';
            utterance.onend = () => document.getElementById('status').textContent = 'Finished';
            utterance.onerror = () => document.getElementById('status').textContent = 'Error occurred';
            
            synth.speak(utterance);
        }}
        
        function pauseStory() {{
            if (synth.speaking && !isPaused) {{
                synth.pause();
                isPaused = true;
                document.getElementById('status').textContent = 'Paused';
            }}
        }}
        
        function stopStory() {{
            synth.cancel();
            isPaused = false;
            document.getElementById('status').textContent = 'Stopped';
        }}
    </script>
    """

# -------------------------------
# Session State
# -------------------------------
if 'story' not in st.session_state:
    st.session_state.story = ""
if 'stats' not in st.session_state:
    st.session_state.stats = {}

# -------------------------------
# Main UI
# -------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Story Details")
    
    character_name = st.text_input(
        "Character Name",
        value="Alex",
        help="Enter your protagonist's name"
    )
    
    story_context = st.text_area(
        "Story Context",
        height=120,
        placeholder="Describe what happens to your character, the situation they're in, or what they need to do...",
        help="Provide context for a better story"
    )
    
    col_set, col_mood = st.columns(2)
    with col_set:
        setting = st.selectbox(
            "Setting",
            ["Modern City", "Small Town", "Fantasy Realm", "Space Station", 
             "Medieval Castle", "Haunted House", "Desert Island", 
             "Underground Bunker", "Forest", "Other"]
        )
    
    with col_mood:
        mood = st.selectbox(
            "Mood",
            ["Dark & Mysterious", "Light & Hopeful", "Intense & Thrilling", 
             "Melancholic", "Humorous", "Romantic", "Eerie", "Inspirational"]
        )

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    model_name = st.selectbox("AI Model", list(MODEL_OPTIONS.keys()))
    model_id = MODEL_OPTIONS[model_name]
    
    story_type = st.selectbox(
        "Genre",
        ["Suspense", "Adventure", "Fantasy", "Drama", "Mystery", "Horror"]
    )
    
    writing_style = st.selectbox(
        "Writing Style", 
        ["Narrative", "Descriptive", "Dialogue-Heavy", "Action-Packed", "Literary"]
    )
    
    length_category = st.selectbox(
        "Length",
        ["Short (300-500 words)", "Medium (500-800 words)", "Long (800-1200 words)"]
    )
    
    # Map length to tokens
    length_tokens = {
        "Short (300-500 words)": 400,
        "Medium (500-800 words)": 650,
        "Long (800-1200 words)": 1000
    }
    max_tokens = length_tokens[length_category]
    
    temperature = st.slider("Creativity", 0.1, 1.5, 0.8, 0.1)

# -------------------------------
# Story Generation
# -------------------------------
with col1:
    # Check credentials
    if CREDENTIALS["api_key"] in ["your-api-key", ""]:
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ Setup Required</strong><br>
            Configure your IBM Watson credentials in .streamlit/secrets.toml:
            <pre>
IBM_API_KEY = "your_api_key"
IBM_PROJECT_ID = "your_project_id"  
IBM_REGION = "us-south"
            </pre>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🚀 Generate Story", help="Generate your story"):
        if not character_name.strip():
            st.error("Please enter a character name")
        elif not story_context.strip():
            st.error("Please provide story context")
        elif CREDENTIALS["api_key"] in ["your-api-key", ""]:
            st.error("Please configure IBM Watson credentials")
        else:
            # Clear previous story
            st.session_state.story = ""
            st.session_state.stats = {}
            
            with st.spinner("Generating your story..."):
                # Create prompt
                prompt = create_story_prompt(
                    character_name, story_type, story_context,
                    writing_style, length_category, mood, setting
                )
                
                # Generate story
                story = generate_story_watson(prompt, model_id, max_tokens, temperature)
                
                if not story.startswith("Error"):
                    st.session_state.story = story
                    st.session_state.stats = get_story_stats(story)
                    st.success("✅ Story generated successfully!")
                else:
                    st.error(story)

    # Display story
    if st.session_state.story and not st.session_state.story.startswith("Error"):
        st.markdown("### 📖 Your Story")
        
        # Stats
        stats = st.session_state.stats
        st.markdown(f"""
        <div class="story-stats">
            📊 {stats['words']} words • {stats['sentences']} sentences • 
            {stats['paragraphs']} paragraphs • ~{stats['reading_time']} min read
        </div>
        """, unsafe_allow_html=True)
        
        # Story display
        st.markdown(f"""
        <div class="story-container">
            <div class="story-text">{st.session_state.story}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # TTS
        tts_html = create_tts_html(st.session_state.story)
        st.components.v1.html(tts_html, height=200)
        
        # Download
        filename = f"{character_name}_{story_type}_story.txt"
        st.download_button(
            "📥 Download Story",
            st.session_state.story,
            filename,
            mime="text/plain"
        )
        
        if st.button("🔄 Generate New Version"):
            st.session_state.story = ""
            st.session_state.stats = {}
            st.rerun()
    
    elif st.session_state.story:
        st.error(st.session_state.story)

# -------------------------------
# Footer
# -------------------------------
st.markdown("""
<div class="footer">
    <p>🤖 Powered by IBM Watson AI | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
