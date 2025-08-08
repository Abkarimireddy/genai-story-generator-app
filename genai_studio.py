import streamlit as st
import requests
import json
import os
import time
import re

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
    .tips-section {
        background: #f0f8ff;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    .model-status {
        font-size: 12px;
        color: #666;
        font-style: italic;
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
    <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Enhanced Edition by Abi Karimireddy</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# API Configuration - OpenAI/Hugging Face Models
# -------------------------------
def get_api_credentials():
    """Get API credentials from secrets or environment variables"""
    try:
        # Try OpenAI first
        if "OPENAI_API_KEY" in st.secrets:
            return {
                "provider": "openai",
                "api_key": st.secrets["OPENAI_API_KEY"]
            }
        # Try Hugging Face
        elif "HF_API_KEY" in st.secrets:
            return {
                "provider": "huggingface",
                "api_key": st.secrets["HF_API_KEY"]
            }
    except:
        pass
    
    # Check environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    hf_key = os.getenv("HF_API_KEY")
    
    if openai_key:
        return {"provider": "openai", "api_key": openai_key}
    elif hf_key:
        return {"provider": "huggingface", "api_key": hf_key}
    
    return {"provider": "none", "api_key": ""}

CREDENTIALS = get_api_credentials()

# Updated Model options with working free models
MODEL_OPTIONS = {
    "GPT-3.5 Turbo": {
        "provider": "openai",
        "id": "gpt-3.5-turbo",
        "status": "✅ Fast & Creative",
        "description": "OpenAI's GPT-3.5 - excellent for storytelling"
    },
    "GPT-4": {
        "provider": "openai", 
        "id": "gpt-4",
        "status": "✅ Premium Quality",
        "description": "Best quality but slower generation"
    },
    "Llama 2 7B": {
        "provider": "huggingface",
        "id": "meta-llama/Llama-2-7b-chat-hf",
        "status": "✅ Free & Good",
        "description": "Free Hugging Face model, good for stories"
    },
    "Mistral 7B": {
        "provider": "huggingface",
        "id": "mistralai/Mistral-7B-Instruct-v0.1", 
        "status": "✅ Creative & Free",
        "description": "Creative storytelling, free on Hugging Face"
    },
    "CodeLlama Instruct": {
        "provider": "huggingface",
        "id": "codellama/CodeLlama-7b-Instruct-hf",
        "status": "⚠️ Experimental",
        "description": "Good for structured stories"
    }
}

# -------------------------------
# Enhanced Prompt Builder
# -------------------------------
def create_enhanced_story_prompt(character_name, story_type, context, writing_style, length_category, mood, setting):
    """Create a precise prompt for better story generation"""
    
    word_counts = {
        "Short (300-500 words)": {"target": 450, "min": 350, "max": 500},
        "Medium (500-800 words)": {"target": 650, "min": 550, "max": 750}, 
        "Long (800-1200 words)": {"target": 950, "min": 800, "max": 1000}
    }
    
    word_info = word_counts[length_category]
    
    prompt = f"""Write a complete {story_type.lower()} story with these requirements:

CHARACTER: {character_name} (use this name consistently)
GENRE: {story_type}
SETTING: {setting}
MOOD: {mood}
STYLE: {writing_style}
LENGTH: {word_info['target']} words (between {word_info['min']}-{word_info['max']})

STORY PLOT: {context}

STRUCTURE:
- Clear beginning that establishes character and setting
- Rising action with conflict and tension
- Climax with peak drama/revelation  
- Resolution that wraps up all plot points
- Satisfying ending that feels complete

REQUIREMENTS:
- Use "{character_name}" as the protagonist throughout
- Follow the provided plot context exactly
- Include dialogue and character development
- Maintain {mood.lower()} atmosphere
- Write in {writing_style.lower()} style
- Create proper paragraph breaks
- End with a complete, satisfying conclusion
- NO abrupt endings or "to be continued"

Write the complete story now:"""

    return prompt

# -------------------------------
# API Functions for Different Providers
# -------------------------------
def generate_story_openai(prompt, model_id, max_tokens, temperature):
    """Generate story using OpenAI API"""
    try:
        headers = {
            "Authorization": f"Bearer {CREDENTIALS['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            story = data["choices"][0]["message"]["content"].strip()
            return format_story_enhanced(story)
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def generate_story_huggingface(prompt, model_id, max_tokens, temperature):
    """Generate story using Hugging Face API"""
    try:
        headers = {
            "Authorization": f"Bearer {CREDENTIALS['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model_id}",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                story = data[0]["generated_text"].strip()
                return format_story_enhanced(story)
            else:
                return "Error: Unexpected response format"
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def generate_story_enhanced(prompt, model_name, max_tokens, temperature):
    """Main story generation function"""
    model_info = MODEL_OPTIONS[model_name]
    model_id = model_info["id"]
    provider = model_info["provider"]
    
    if provider == "openai":
        return generate_story_openai(prompt, model_id, max_tokens, temperature)
    elif provider == "huggingface":
        return generate_story_huggingface(prompt, model_id, max_tokens, temperature)
    else:
        return "Error: Unsupported model provider"

def format_story_enhanced(story):
    """Enhanced story formatting"""
    # Remove extra whitespace
    story = re.sub(r'\s+', ' ', story).strip()
    
    # Remove any prompt echoes
    story = re.sub(r'^.*?(?:write|story|once upon|in the beginning)', '', story, flags=re.IGNORECASE)
    story = story.strip()
    
    # Ensure proper capitalization
    if story and not story[0].isupper():
        story = story[0].upper() + story[1:]
    
    # Create better paragraph breaks
    sentences = [s.strip() + '.' for s in story.split('.') if s.strip()]
    paragraphs = []
    current_para = []
    
    for i, sentence in enumerate(sentences):
        current_para.append(sentence)
        
        # Create paragraph breaks at natural points
        if (len(current_para) >= 3 and 
            ('.' in sentence or '!' in sentence or '?' in sentence) and
            i < len(sentences) - 1):
            paragraphs.append(' '.join(current_para))
            current_para = []
    
    # Add remaining sentences
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    return '\n\n'.join(paragraphs)

def get_story_stats_enhanced(story):
    """Enhanced story statistics"""
    words = len(story.split())
    sentences = len([s for s in story.split('.') if s.strip()])
    paragraphs = len([p for p in story.split('\n\n') if p.strip()])
    
    # Reading time calculation
    reading_time = max(1, words // 225)
    
    return {
        "words": words,
        "sentences": sentences, 
        "paragraphs": paragraphs,
        "reading_time": reading_time,
        "average_sentence_length": round(words / max(sentences, 1), 1)
    }

# -------------------------------
# Session State Initialization
# -------------------------------
if 'generated_story' not in st.session_state:
    st.session_state.generated_story = ""
if 'story_stats' not in st.session_state:
    st.session_state.story_stats = {}
if 'story_history' not in st.session_state:
    st.session_state.story_history = []

# -------------------------------
# Main UI Layout
# -------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Story Creation")
    
    character_name = st.text_input(
        "🎭 Character Name",
        value="Alex",
        help="Enter your main character's name"
    )
    
    story_context = st.text_area(
        "📖 Story Context & Plot",
        height=150,
        placeholder="Describe what happens in your story:\n- What situation is your character in?\n- What challenge do they face?\n- What do they need to accomplish?\n- How should the story end?\n\nExample: Alex discovers a mysterious letter in their grandmother's attic that leads to a hidden treasure map. They must solve three riddles and overcome their fear of heights to find the treasure before sunset.",
        help="Provide detailed context for a better, more coherent story."
    )
    
    col_set, col_mood = st.columns(2)
    with col_set:
        setting = st.selectbox(
            "🏞️ Setting",
            ["Modern City", "Small Town", "Fantasy Realm", "Space Station", 
             "Medieval Castle", "Haunted House", "Desert Island", 
             "Underground Bunker", "Ancient Forest", "Mountain Village",
             "Post-Apocalyptic World", "Victorian London", "Wild West Town"]
        )
    
    with col_mood:
        mood = st.selectbox(
            "🎭 Mood & Tone",
            ["Dark & Mysterious", "Light & Hopeful", "Intense & Thrilling", 
             "Melancholic", "Humorous", "Romantic", "Eerie", "Inspirational",
             "Nostalgic", "Dramatic", "Whimsical"]
        )

# Sidebar with Settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Model Selection
    st.markdown("**🤖 AI Model**")
    model_name = st.selectbox(
        "Choose Model",
        list(MODEL_OPTIONS.keys()),
        help="Different models have different strengths"
    )
    
    model_info = MODEL_OPTIONS[model_name]
    
    st.markdown(f"""
    <div class="model-status">
    {model_info['status']}<br>
    {model_info['description']}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Story Settings
    story_type = st.selectbox(
        "📚 Genre",
        ["Adventure", "Mystery", "Fantasy", "Drama", "Suspense", "Horror", 
         "Romance", "Science Fiction", "Thriller", "Comedy"]
    )
    
    writing_style = st.selectbox(
        "✍️ Writing Style", 
        ["Narrative", "Descriptive", "Dialogue-Heavy", "Action-Packed", 
         "Literary", "Conversational", "Dramatic", "Poetic"]
    )
    
    length_category = st.selectbox(
        "📏 Story Length",
        ["Short (300-500 words)", "Medium (500-800 words)", "Long (800-1200 words)"]
    )
    
    # Enhanced length mapping
    length_tokens = {
        "Short (300-500 words)": 600,
        "Medium (500-800 words)": 900,
        "Long (800-1200 words)": 1200
    }
    max_tokens = length_tokens[length_category]
    
    temperature = st.slider(
        "🎨 Creativity Level", 
        0.1, 1.5, 0.8, 0.1,
        help="Lower = more focused, Higher = more creative"
    )
    
    # Tips Section
    with st.expander("💡 Tips"):
        st.markdown("""
        **📝 Context Tips:**
        - Include specific conflicts or challenges
        - Mention the desired ending
        - Add character motivations
        - Describe key plot points
        
        **🎯 Best Practices:**
        - Use clear, descriptive language
        - Choose appropriate mood for genre
        - Test different models for varying styles
        """)

with col2:
    st.markdown("### 🎯 Actions")
    
    # API Status Check
    if CREDENTIALS["provider"] != "none" and CREDENTIALS["api_key"]:
        st.success(f"✅ {CREDENTIALS['provider'].title()} API Ready")
    else:
        st.error("❌ API Key Required")
        st.info("Add your OpenAI or Hugging Face API key to secrets.")
    
    # Generation Button
    if st.button("🚀 Generate Story", type="primary", use_container_width=True):
        if not character_name.strip():
            st.error("Please enter a character name!")
        elif not story_context.strip():
            st.error("Please provide story context!")
        elif CREDENTIALS["provider"] == "none":
            st.error("Please configure your API credentials!")
        else:
            with st.spinner(f"🤖 {model_name} is crafting your story..."):
                prompt = create_enhanced_story_prompt(
                    character_name, story_type, story_context, 
                    writing_style, length_category, mood, setting
                )
                
                story = generate_story_enhanced(prompt, model_name, max_tokens, temperature)
                
                if not story.startswith("Error"):
                    st.session_state.generated_story = story
                    st.session_state.story_stats = get_story_stats_enhanced(story)
                    st.success("✅ Story generated!")
                    st.rerun()
                else:
                    st.error(story)

# -------------------------------
# Story Display and Controls
# -------------------------------
if st.session_state.generated_story and not st.session_state.generated_story.startswith("Error"):
    st.markdown("---")
    
    # Story Stats
    if st.session_state.story_stats:
        stats = st.session_state.story_stats
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            st.metric("📝 Words", stats['words'])
        with col_stats2:
            st.metric("📖 Reading Time", f"{stats['reading_time']} min")
        with col_stats3:
            st.metric("📊 Paragraphs", stats['paragraphs'])
        with col_stats4:
            st.metric("📏 Avg Sentence", f"{stats['average_sentence_length']} words")
    
    # Story Container
    st.markdown("""
    <div class="story-container">
        <h3 style="color: #2c3e50; margin-bottom: 1rem;">📚 Your Generated Story</h3>
        <div class="story-text">
    """, unsafe_allow_html=True)
    
    st.markdown(st.session_state.generated_story)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Enhanced Controls
    st.markdown("### 🎮 Story Controls")
    
    control_cols = st.columns([1, 1, 1, 1])
    
    with control_cols[0]:
        # Download as Text
        story_filename = f"{character_name}_{story_type}_Story.txt"
        st.download_button(
            "💾 Download",
            st.session_state.generated_story,
            file_name=story_filename,
            mime="text/plain",
            use_container_width=True
        )
    
    with control_cols[1]:
        # Copy to Clipboard
        if st.button("📋 Copy", use_container_width=True):
            st.code(st.session_state.generated_story)
            st.info("📋 Story displayed above - select and copy!")
    
    with control_cols[2]:
        # Regenerate
        if st.button("🔄 Regenerate", use_container_width=True):
            if story_context.strip() and character_name.strip():
                with st.spinner("🤖 Regenerating..."):
                    prompt = create_enhanced_story_prompt(
                        character_name, story_type, story_context,
                        writing_style, length_category, mood, setting
                    )
                    story = generate_story_enhanced(prompt, model_name, max_tokens, temperature)
                    
                    if not story.startswith("Error"):
                        st.session_state.generated_story = story
                        st.session_state.story_stats = get_story_stats_enhanced(story)
                        st.rerun()
                    else:
                        st.error(story)
    
    with control_cols[3]:
        # Clear Story
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.generated_story = ""
            st.session_state.story_stats = {}
            st.rerun()

# -------------------------------
# Story Templates
# -------------------------------
with st.expander("📋 Story Templates"):
    st.markdown("### 🚀 Quick Templates")
    
    templates = {
        "🗝️ The Mysterious Letter": {
            "context": "{name} finds an old letter hidden in a library book that contains a cryptic message about a treasure hidden in their town. Following the clues leads them on an adventure through historical landmarks, but they're not the only one searching for the treasure.",
            "setting": "Small Town",
            "genre": "Mystery",
            "mood": "Dark & Mysterious"
        },
        "🚀 Space Station Crisis": {
            "context": "{name} is a maintenance engineer on a space station when all communication with Earth suddenly stops. Strange readings appear on the sensors, and {name} must investigate what's happening while keeping the station operational.",
            "setting": "Space Station",
            "genre": "Science Fiction",
            "mood": "Intense & Thrilling"
        },
        "🏰 The Magic Academy": {
            "context": "{name} receives an unexpected invitation to a hidden academy of magic. On their first day, they discover they have a rare and dangerous magical ability that others fear. They must learn to control their power while uncovering the truth about their heritage.",
            "setting": "Fantasy Realm",
            "genre": "Fantasy",
            "mood": "Light & Hopeful"
        },
        "🌊 Desert Island Survival": {
            "context": "{name} wakes up alone on a deserted island after a shipwreck. They must find fresh water, build shelter, and signal for rescue, but they discover they're not alone on the island and someone doesn't want them to leave.",
            "setting": "Desert Island",
            "genre": "Adventure",
            "mood": "Intense & Thrilling"
        }
    }
    
    template_cols = st.columns(2)
    
    for i, (template_name, template_data) in enumerate(templates.items()):
        col = template_cols[i % 2]
        with col:
            if st.button(template_name, key=f"template_{i}"):
                template_context = template_data["context"].replace("{name}", character_name if character_name else "[Character Name]")
                st.info("📋 **Template loaded!** Copy this context:")
                st.code(template_context, language=None)

# -------------------------------
# API Setup Guide
# -------------------------------
with st.expander("🔧 API Setup Guide"):
    st.markdown("### 🚀 Getting Started")
    
    setup_cols = st.columns(2)
    
    with setup_cols[0]:
        st.markdown("""
        **🤖 OpenAI Setup:**
        1. Go to [OpenAI API](https://platform.openai.com/api-keys)
        2. Create an API key
        3. Add to Streamlit secrets as `OPENAI_API_KEY`
        4. Models: GPT-3.5-turbo, GPT-4
        
        **Cost:** ~$0.002 per story (GPT-3.5)
        """)
    
    with setup_cols[1]:
        st.markdown("""
        **🤗 Hugging Face Setup:**
        1. Go to [Hugging Face](https://huggingface.co/settings/tokens)
        2. Create a token
        3. Add to secrets as `HF_API_KEY`  
        4. Models: Llama 2, Mistral (Free!)
        
        **Cost:** Free tier available
        """)

# -------------------------------
# Footer
# -------------------------------
st.markdown("""
<div class="footer">
    <p>🤖 <strong>GenAI Story Generator v2.0</strong></p>
    <p>Enhanced Edition by <strong>Abi Karimireddy</strong></p>
    <p>Supports OpenAI & Hugging Face Models • Built with Streamlit</p>
    
    <div style="margin-top: 1rem; font-size: 12px; color: #888;">
        ✨ Features: Advanced prompting • Better story structure • Multiple model support<br>
        📊 Story analytics • Quick templates • Easy export options
    </div>
</div>
""", unsafe_allow_html=True)
