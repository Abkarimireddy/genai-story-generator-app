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
    page_title="Creative Story Studio",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Custom CSS Styling - More Natural Look
# -------------------------------
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2.5rem 0;
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 25px 25px;
        color: white;
        box-shadow: 0 6px 25px rgba(0,0,0,0.15);
    }
    .story-container {
        background: #ffffff;
        padding: 2.5rem;
        border-radius: 12px;
        border: 1px solid #e1e8ed;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 2rem 0;
    }
    .story-text {
        font-family: 'Charter', 'Georgia', serif;
        font-size: 17px;
        line-height: 1.7;
        color: #2c3e50;
        text-align: justify;
        white-space: pre-line;
    }
    .info-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
        color: #475569;
    }
    .story-stats {
        background: #f0f9ff;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 14px;
        color: #0369a1;
        border-left: 4px solid #0ea5e9;
    }
    .tts-controls {
        background: #fafafa;
        padding: 2rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
        text-align: center;
    }
    .control-button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        margin: 0.4rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2);
    }
    .model-info {
        font-size: 13px;
        color: #64748b;
        font-style: normal;
        margin-top: 4px;
    }
    .footer {
        text-align: center;
        color: #64748b;
        font-size: 14px;
        margin-top: 4rem;
        padding: 2rem 0;
        border-top: 1px solid #e2e8f0;
    }
    .section-header {
        color: #334155;
        font-weight: 600;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Header
# -------------------------------
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 2.8rem; font-weight: 400;">Creative Story Studio</h1>
    <p style="margin: 0.8rem 0 0 0; font-size: 1.1rem; opacity: 0.95;">Craft compelling stories with advanced AI</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# API Configuration
# -------------------------------
def get_api_credentials():
    try:
        return {
            "api_key": st.secrets.get("OPENAI_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY") or st.secrets.get("API_KEY"),
            "provider": st.secrets.get("AI_PROVIDER", "openai")
        }
    except:
        return {
            "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("API_KEY"),
            "provider": os.getenv("AI_PROVIDER", "openai")
        }

CREDENTIALS = get_api_credentials()

# Updated Model options - Current and Relevant Models
MODEL_OPTIONS = {
    "GPT-4 Turbo": {
        "id": "gpt-4-turbo-preview",
        "provider": "openai",
        "description": "Latest GPT-4 model, excellent for creative writing"
    },
    "GPT-3.5 Turbo": {
        "id": "gpt-3.5-turbo",
        "provider": "openai", 
        "description": "Fast and reliable, great for most story types"
    },
    "Claude 3 Sonnet": {
        "id": "claude-3-sonnet-20240229",
        "provider": "anthropic",
        "description": "Excellent storytelling with natural dialogue"
    },
    "Claude 3 Haiku": {
        "id": "claude-3-haiku-20240307",
        "provider": "anthropic",
        "description": "Quick and creative, good for shorter stories"
    },
    "Llama 3 70B": {
        "id": "meta-llama-3-70b-instruct",
        "provider": "together",
        "description": "Open source model with strong creative capabilities"
    }
}

# Voice options for TTS
VOICE_OPTIONS = {
    "Natural": {"rate": 0.9, "pitch": 1.0, "voice": "default"},
    "Storyteller": {"rate": 0.8, "pitch": 0.95, "voice": "default"},
    "Quick Read": {"rate": 1.1, "pitch": 1.05, "voice": "default"},
    "Dramatic": {"rate": 0.85, "pitch": 0.9, "voice": "default"},
    "Cheerful": {"rate": 0.95, "pitch": 1.15, "voice": "default"}
}

# -------------------------------
# Enhanced Prompt Builder
# -------------------------------
def create_story_prompt(character_name, story_type, context, writing_style, length_category, mood, setting):
    """Create a well-structured prompt for story generation"""
    
    word_counts = {
        "Short (300-500 words)": {"target": 400, "range": "300-500"},
        "Medium (500-800 words)": {"target": 650, "range": "500-800"}, 
        "Long (800-1200 words)": {"target": 1000, "range": "800-1200"}
    }
    
    word_info = word_counts[length_category]
    
    prompt = f"""Write a complete {story_type.lower()} story with these specifications:

Character: {character_name}
Setting: {setting}
Style: {writing_style}
Mood: {mood}
Length: {word_info['range']} words

Story Context:
{context}

Requirements:
- Write a complete story with beginning, middle, and satisfying ending
- Target approximately {word_info['target']} words
- Use {writing_style.lower()} writing style throughout
- Maintain {mood.lower()} tone
- Include dialogue and character development
- Create a compelling narrative arc
- End with proper resolution

Write the story now:"""

    return prompt

# -------------------------------
# Story Generation Functions
# -------------------------------
def generate_story_openai(prompt, model_id, max_tokens, temperature):
    """Generate story using OpenAI API"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=CREDENTIALS["api_key"])
        
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are an expert creative writer who crafts engaging, complete stories with proper narrative structure."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error generating story: {str(e)}"

def generate_story_anthropic(prompt, model_id, max_tokens, temperature):
    """Generate story using Anthropic API"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=CREDENTIALS["api_key"])
        
        response = client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        return f"Error generating story: {str(e)}"

def generate_story(prompt, model_info, max_tokens, temperature):
    """Main story generation function"""
    provider = model_info.get("provider", "openai")
    model_id = model_info["id"]
    
    if provider == "openai":
        return generate_story_openai(prompt, model_id, max_tokens, temperature)
    elif provider == "anthropic":
        return generate_story_anthropic(prompt, model_id, max_tokens, temperature)
    else:
        return "Error: Unsupported AI provider"

def format_story(story):
    """Clean and format the generated story"""
    # Remove extra whitespace
    story = re.sub(r'\s+', ' ', story).strip()
    
    # Create proper paragraph breaks
    sentences = [s.strip() for s in story.split('.') if s.strip()]
    paragraphs = []
    current_para = []
    
    for i, sentence in enumerate(sentences):
        if not sentence.endswith('.'):
            sentence += '.'
        current_para.append(sentence)
        
        # Create paragraph breaks every 3-4 sentences
        if len(current_para) >= 3 and i < len(sentences) - 1:
            paragraphs.append(' '.join(current_para))
            current_para = []
    
    # Add remaining sentences
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    return '\n\n'.join(paragraphs)

def get_story_stats(story):
    """Calculate story statistics"""
    words = len(story.split())
    sentences = len([s for s in story.split('.') if s.strip()])
    paragraphs = len([p for p in story.split('\n\n') if p.strip()])
    
    reading_time = max(1, words // 225)
    listening_time = max(1, words // 155)
    
    return {
        "words": words,
        "sentences": sentences, 
        "paragraphs": paragraphs,
        "reading_time": reading_time,
        "listening_time": listening_time
    }

# -------------------------------
# Text-to-Speech Function
# -------------------------------
def create_tts_html(text, voice_settings):
    """Generate text-to-speech controls"""
    clean_text = re.sub(r'[^\w\s\.,!?;:\-\'"()]', '', text)
    clean_text = clean_text.replace('\n\n', '. ').replace('\n', ' ')
    clean_text_escaped = clean_text.replace('\\', '\\\\').replace('`', '\\`').replace('"', '\\"')
    
    word_count = len(clean_text.split())
    listening_time = max(1, word_count // 155)
    
    return f"""
    <div class="tts-controls">
        <h4>🎧 Audio Playback</h4>
        <div style="margin-bottom: 1.5rem; color: #64748b;">
            Voice: {voice_settings.get('name', 'Natural')} • Estimated time: {listening_time} min
        </div>
        
        <div style="margin-bottom: 1rem;">
            <button onclick="playStory()" class="control-button">▶️ Play</button>
            <button onclick="pauseStory()" class="control-button">⏸️ Pause</button>
            <button onclick="resumeStory()" class="control-button">⏵️ Resume</button>
            <button onclick="stopStory()" class="control-button">⏹️ Stop</button>
        </div>
        
        <div style="margin: 1rem 0;">
            <label for="speed-control" style="color: #475569;">Speed: </label>
            <input type="range" id="speed-control" min="0.6" max="1.4" step="0.1" value="{voice_settings['rate']}" 
                   onchange="updateSpeed(this.value)" style="width: 120px;">
            <span id="speed-value" style="margin-left: 8px; color: #64748b;">{voice_settings['rate']}</span>
        </div>
        
        <div id="status" style="margin-top: 1rem; font-weight: 500; color: #475569;">Ready</div>
    </div>
    
    <script>
        let synth = window.speechSynthesis;
        let utterance = null;
        let isPaused = false;
        let isPlaying = false;
        let currentRate = {voice_settings['rate']};
        
        const storyText = "{clean_text_escaped}";
        
        function updateSpeed(newRate) {{
            currentRate = parseFloat(newRate);
            document.getElementById('speed-value').textContent = newRate;
        }}
        
        function playStory() {{
            if (isPaused && utterance) {{
                synth.resume();
                isPaused = false;
                isPlaying = true;
                document.getElementById('status').textContent = 'Playing...';
                return;
            }}
            
            if (synth.speaking) synth.cancel();
            
            utterance = new SpeechSynthesisUtterance(storyText);
            utterance.rate = currentRate;
            utterance.pitch = {voice_settings['pitch']};
            
            utterance.onstart = () => {{
                document.getElementById('status').textContent = 'Playing...';
                isPlaying = true;
                isPaused = false;
            }};
            
            utterance.onend = () => {{
                document.getElementById('status').textContent = 'Finished';
                isPlaying = false;
                isPaused = false;
            }};
            
            synth.speak(utterance);
        }}
        
        function pauseStory() {{
            if (synth.speaking && !isPaused) {{
                synth.pause();
                isPaused = true;
                isPlaying = false;
                document.getElementById('status').textContent = 'Paused';
            }}
        }}
        
        function resumeStory() {{
            if (isPaused) {{
                synth.resume();
                isPaused = false;
                isPlaying = true;
                document.getElementById('status').textContent = 'Playing...';
            }}
        }}
        
        function stopStory() {{
            synth.cancel();
            isPaused = false;
            isPlaying = false;
            document.getElementById('status').textContent = 'Stopped';
        }}
    </script>
    """

# -------------------------------
# Session State
# -------------------------------
if 'generated_story' not in st.session_state:
    st.session_state.generated_story = ""
if 'story_stats' not in st.session_state:
    st.session_state.story_stats = {}

# -------------------------------
# Main Interface
# -------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<p class="section-header">Story Setup</p>', unsafe_allow_html=True)
    
    character_name = st.text_input(
        "Character Name",
        value="Alex",
        help="The main character in your story"
    )
    
    story_context = st.text_area(
        "Story Context",
        height=140,
        placeholder="Describe your story idea:\n• What situation is your character in?\n• What challenge do they face?\n• What's the main conflict or goal?\n\nExample: Alex discovers an old map in their grandmother's attic that leads to a hidden treasure, but they must solve ancient riddles while being followed by mysterious strangers.",
        help="The more detailed your context, the better your story will be"
    )
    
    col_setting, col_mood = st.columns(2)
    with col_setting:
        setting = st.selectbox(
            "Setting",
            ["Modern City", "Small Town", "Fantasy World", "Space Station", 
             "Medieval Kingdom", "Haunted Mansion", "Tropical Island", 
             "Underground Cave", "Ancient Forest", "Mountain Village"]
        )
    
    with col_mood:
        mood = st.selectbox(
            "Mood",
            ["Mysterious", "Adventurous", "Dramatic", "Lighthearted", 
             "Suspenseful", "Romantic", "Dark", "Inspirational", "Nostalgic"]
        )

with col2:
    st.markdown('<p class="section-header">Options</p>', unsafe_allow_html=True)
    
    # Model Selection
    model_name = st.selectbox(
        "AI Model",
        list(MODEL_OPTIONS.keys()),
        help="Different models have different writing styles"
    )
    
    model_info = MODEL_OPTIONS[model_name]
    st.markdown(f'<div class="model-info">{model_info["description"]}</div>', unsafe_allow_html=True)
    
    story_type = st.selectbox(
        "Genre",
        ["Adventure", "Mystery", "Fantasy", "Drama", "Thriller", 
         "Romance", "Sci-Fi", "Horror", "Comedy"]
    )
    
    writing_style = st.selectbox(
        "Writing Style", 
        ["Descriptive", "Fast-paced", "Character-focused", "Dialogue-heavy", 
         "Literary", "Cinematic", "Conversational"]
    )
    
    length_category = st.selectbox(
        "Story Length",
        ["Short (300-500 words)", "Medium (500-800 words)", "Long (800-1200 words)"]
    )
    
    length_tokens = {
        "Short (300-500 words)": 700,
        "Medium (500-800 words)": 1000,
        "Long (800-1200 words)": 1500
    }
    max_tokens = length_tokens[length_category]
    
    creativity = st.slider(
        "Creativity Level", 
        0.3, 1.2, 0.8, 0.1,
        help="Higher values = more creative and unexpected"
    )

# Voice Selection
with st.sidebar:
    st.markdown("### Audio Settings")
    selected_voice = st.selectbox(
        "Voice Style",
        list(VOICE_OPTIONS.keys())
    )
    voice_settings = VOICE_OPTIONS[selected_voice]
    voice_settings["name"] = selected_voice

# Generation Button
st.markdown("---")
if st.button("Generate Story", type="primary", use_container_width=True):
    if not character_name.strip():
        st.error("Please enter a character name")
    elif not story_context.strip():
        st.error("Please provide story context")
    elif not CREDENTIALS.get("api_key"):
        st.error("Please configure your API credentials")
    else:
        with st.spinner("Creating your story..."):
            prompt = create_story_prompt(
                character_name, story_type, story_context, 
                writing_style, length_category, mood, setting
            )
            
            story = generate_story(prompt, model_info, max_tokens, creativity)
            
            if not story.startswith("Error"):
                st.session_state.generated_story = format_story(story)
                st.session_state.story_stats = get_story_stats(st.session_state.generated_story)
                st.success("Story generated successfully!")
                st.rerun()
            else:
                st.error(story)

# Story Display
if st.session_state.generated_story:
    st.markdown("---")
    
    # Stats
    if st.session_state.story_stats:
        stats = st.session_state.story_stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Words", stats['words'])
        with col2:
            st.metric("Reading Time", f"{stats['reading_time']} min")
        with col3:
            st.metric("Listening Time", f"{stats['listening_time']} min")
        with col4:
            st.metric("Paragraphs", stats['paragraphs'])
    
    # Story Container
    st.markdown("""
    <div class="story-container">
        <h3 style="color: #2c3e50; margin-bottom: 1.5rem; font-weight: 600;">Your Story</h3>
        <div class="story-text">
    """, unsafe_allow_html=True)
    
    st.markdown(st.session_state.generated_story)
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Controls
    control_cols = st.columns(4)
    
    with control_cols[0]:
        story_filename = f"{character_name}_{story_type}_Story.txt"
        st.download_button(
            "💾 Download",
            st.session_state.generated_story,
            file_name=story_filename,
            mime="text/plain",
            use_container_width=True
        )
    
    with control_cols[1]:
        if st.button("📋 Copy Text", use_container_width=True):
            st.code(st.session_state.generated_story, language=None)
    
    with control_cols[2]:
        if st.button("🔄 Regenerate", use_container_width=True):
            with st.spinner("Regenerating..."):
                prompt = create_story_prompt(
                    character_name, story_type, story_context,
                    writing_style, length_category, mood, setting
                )
                story = generate_story(prompt, model_info, max_tokens, creativity)
                
                if not story.startswith("Error"):
                    st.session_state.generated_story = format_story(story)
                    st.session_state.story_stats = get_story_stats(st.session_state.generated_story)
                    st.rerun()
                else:
                    st.error(story)
    
    with control_cols[3]:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.generated_story = ""
            st.session_state.story_stats = {}
            st.rerun()
    
    # Audio Player
    st.markdown("---")
    tts_html = create_tts_html(st.session_state.generated_story, voice_settings)
    st.components.v1.html(tts_html, height=300)

# -------------------------------
# Story Templates
# -------------------------------
with st.expander("📋 Story Templates"):
    st.markdown("### Quick Start Templates")
    
    templates = {
        "🗝️ The Discovery": {
            "context": "{name} finds a mysterious object that changes everything about their ordinary day. What starts as curiosity leads to an adventure they never expected.",
            "setting": "Small Town",
            "genre": "Mystery"
        },
        "🚀 Space Mission": {
            "context": "{name} is part of the first mission to explore a newly discovered planet. When their ship encounters unexpected problems, they must use their skills to save the crew.",
            "setting": "Space Station", 
            "genre": "Sci-Fi"
        },
        "🏰 The Quest": {
            "context": "{name} is chosen for an important quest in a magical realm. They must overcome three challenges and face their greatest fear to succeed.",
            "setting": "Fantasy World",
            "genre": "Fantasy"
        },
        "🕵️ The Investigation": {
            "context": "{name} stumbles upon clues to a mystery that everyone else has given up on. As they dig deeper, they realize the truth is more complicated than expected.",
            "setting": "Modern City",
            "genre": "Mystery"
        }
    }
    
    for template_name, template_data in templates.items():
        if st.button(template_name, key=f"template_{template_name}"):
            st.info(f"Template: {template_name}")
            formatted_context = template_data["context"].replace("{name}", character_name or "[Character Name]")
            st.code(formatted_context, language=None)

# -------------------------------
# Writing Tips
# -------------------------------
with st.expander("💡 Writing Tips"):
    st.markdown("""
    **For Better Stories:**
    - Include specific details about your character's situation
    - Describe the main conflict or challenge they face
    - Mention what's at stake or why it matters
    - Add emotional elements to make readers care
    
    **Genre-Specific Tips:**
    - **Mystery**: Focus on clues, secrets, and revelations
    - **Adventure**: Emphasize journey, obstacles, and discovery
    - **Fantasy**: Establish magical rules and otherworldly elements
    - **Drama**: Highlight relationships and internal conflicts
    - **Romance**: Include emotional connection and character chemistry
    """)

# -------------------------------
# Footer
# -------------------------------
st.markdown("""
<div class="footer">
    <p><strong>Creative Story Studio</strong> • Powered by Advanced AI</p>
    <p>Professional storytelling tools for writers, educators, and creators</p>
    <div style="margin-top: 1rem; font-size: 12px; opacity: 0.7;">
        Built with modern AI models • Optimized for creative writing • Export-ready stories
    </div>
</div>
""", unsafe_allow_html=True)
