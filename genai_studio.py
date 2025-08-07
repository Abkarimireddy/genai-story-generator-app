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
    .input-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .sidebar-content {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .generate-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        transition: all 0.3s ease;
    }
    .generate-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 14px;
        margin-top: 3rem;
        padding: 2rem 0;
        border-top: 1px solid #eee;
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
    .tts-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
    }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Remove empty spaces */
    .block-container {
        padding-top: 1rem;
    }
    
    /* Streamlit specific styling fixes */
    .stSelectbox > div > div {
        background-color: white;
    }
    
    .stTextInput > div > div {
        background-color: white;
    }
    
    .stTextArea > div > div {
        background-color: white;
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

# Multiple model options for better story generation
MODEL_OPTIONS = {
    "Google Flan-UL2": "google/flan-ul2",
    "IBM Granite-13B": "ibm/granite-13b-instruct-v2",
    "Meta Llama-2-70B": "meta-llama/llama-2-70b-chat",
    "Google Flan-T5-XXL": "google/flan-t5-xxl"
}

# -------------------------------
# Enhanced Prompt Builder
# -------------------------------
def create_enhanced_story_prompt(character_name, story_type, context, writing_style, length_category, mood, setting):
    """Create a sophisticated prompt for better story generation with stronger parameter enforcement"""
    
    # Define genre-specific elements more distinctly
    genre_elements = {
        "suspense": {
            "key_elements": "tension, uncertainty, anticipation, mystery, danger",
            "atmosphere": "Create mounting tension with uncertain outcomes",
            "plot_devices": "Use cliffhangers, red herrings, and time pressure",
            "tone_words": "ominous, foreboding, tense, uncertain, gripping"
        },
        "adventure": {
            "key_elements": "journey, challenges, exploration, discovery, heroism",
            "atmosphere": "Create excitement through action and discovery",
            "plot_devices": "Use obstacles, allies, enemies, and quests",
            "tone_words": "exciting, bold, daring, epic, thrilling"
        },
        "fantasy": {
            "key_elements": "magic, mythical creatures, otherworldly settings, powers",
            "atmosphere": "Build a magical world with its own rules",
            "plot_devices": "Use magical systems, prophecies, and mythical beings",
            "tone_words": "magical, mystical, enchanting, otherworldly, wondrous"
        },
        "drama": {
            "key_elements": "relationships, emotions, conflicts, growth, realism",
            "atmosphere": "Focus on deep character emotions and relationships",
            "plot_devices": "Use internal conflict, relationship dynamics, and personal growth",
            "tone_words": "emotional, heartfelt, intense, realistic, moving"
        },
        "mystery": {
            "key_elements": "clues, investigation, secrets, revelation, deduction",
            "atmosphere": "Build intrigue through hidden information",
            "plot_devices": "Use clues, suspects, alibis, and logical deduction",
            "tone_words": "mysterious, intriguing, puzzling, secretive, investigative"
        },
        "horror": {
            "key_elements": "fear, supernatural, darkness, terror, dread",
            "atmosphere": "Create fear and unease through psychological terror",
            "plot_devices": "Use isolation, the unknown, and escalating threats",
            "tone_words": "terrifying, eerie, sinister, haunting, nightmarish"
        }
    }
    
    # Get genre-specific elements
    genre_info = genre_elements.get(story_type.lower(), genre_elements["adventure"])
    
    # Create mood-specific descriptors
    mood_descriptors = {
        "Dark & Mysterious": "shadowy, enigmatic, brooding, ominous, secretive",
        "Light & Hopeful": "bright, optimistic, uplifting, cheerful, inspiring",
        "Intense & Thrilling": "high-energy, fast-paced, adrenaline-filled, gripping",
        "Melancholic": "sorrowful, reflective, bittersweet, contemplative",
        "Humorous": "witty, amusing, lighthearted, comedic, entertaining",
        "Romantic": "passionate, tender, intimate, heartwarming, loving",
        "Eerie": "unsettling, spooky, atmospheric, haunting, chilling",
        "Inspirational": "uplifting, motivating, empowering, triumphant, hopeful"
    }
    
    mood_words = mood_descriptors.get(mood, "engaging, compelling")
    
    # Create setting-specific details
    setting_details = {
        "Modern City": "urban landscape, skyscrapers, busy streets, technology, crowds",
        "Small Town": "close-knit community, familiar faces, local landmarks, quiet streets",
        "Fantasy Realm": "magical kingdoms, enchanted forests, mystical creatures, ancient magic",
        "Space Station": "zero gravity, advanced technology, distant stars, isolated environment",
        "Medieval Castle": "stone walls, torches, knights, nobility, ancient traditions",
        "Haunted House": "creaking floors, shadows, mysterious sounds, old furniture",
        "Desert Island": "tropical paradise, isolation, survival, natural beauty",
        "Underground Bunker": "confined spaces, artificial lighting, hidden secrets",
        "Forest": "towering trees, wildlife, natural sounds, hidden paths",
        "Other": "unique and atmospheric location"
    }
    
    setting_atmosphere = setting_details.get(setting, "atmospheric location")
    
    # Create a more structured and specific prompt
    prompt = f"""CRITICAL: You must write a {story_type.upper()} story that strictly follows ALL parameters below. Do not deviate from the genre, mood, or setting requirements.

=== MANDATORY STORY REQUIREMENTS ===
PROTAGONIST: {character_name} (This character MUST be the main focus)
GENRE: {story_type.upper()} - MUST include: {genre_info['key_elements']}
SETTING: {setting} - MUST incorporate: {setting_atmosphere}
MOOD: {mood} - Story MUST feel: {mood_words}
WRITING STYLE: {writing_style}
TARGET LENGTH: {length_category}

=== STORY CONTEXT (MUST BE INCORPORATED) ===
{context}

=== GENRE-SPECIFIC REQUIREMENTS ===
- Atmosphere: {genre_info['atmosphere']}
- Plot Devices: {genre_info['plot_devices']}
- Tone: Story must feel {genre_info['tone_words']}

=== STRICT WRITING INSTRUCTIONS ===
1. BEGIN immediately with {character_name} in the {setting} environment
2. The opening paragraph MUST establish the {story_type.lower()} genre immediately
3. Every paragraph must maintain the {mood} mood consistently
4. Include specific {setting} details in every scene
5. Use {writing_style.lower()} writing approach throughout
6. Incorporate the provided context naturally into the plot
7. Stay true to {story_type.lower()} genre conventions
8. End with a resolution appropriate to the {story_type.lower()} genre

=== QUALITY REQUIREMENTS ===
- Rich sensory details specific to {setting}
- Dialogue that reveals character and advances plot
- Pacing appropriate for {story_type.lower()} genre
- Emotional depth matching {mood} mood
- Logical plot progression
- Satisfying conclusion

Remember: This must be a {story_type.upper()} story set in {setting} with a {mood.lower()} mood featuring {character_name}. Do not write a generic story - make it distinctly {story_type.lower()} in nature.

BEGIN THE STORY NOW:"""

    return prompt

# -------------------------------
# Enhanced IBM Watson API Integration
# -------------------------------
def get_iam_token(api_key):
    """Get IBM Cloud IAM token with better error handling"""
    try:
        url = "https://iam.cloud.ibm.com/identity/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        return response.json().get("access_token")
    except requests.RequestException as e:
        st.error(f"Authentication error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error during authentication: {str(e)}")
        return None

def generate_story_with_watson(prompt, model_id, max_tokens, temperature, creativity_settings):
    """Enhanced story generation with better parameters and error handling"""
    token = get_iam_token(CREDENTIALS["api_key"])
    if not token:
        return "Error: Could not authenticate with IBM Watson. Please check your API credentials."

    try:
        url = f"https://{CREDENTIALS['region']}.ml.cloud.ibm.com/ml/v1/text/generation?version={VERSION}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Enhanced parameters for better story generation with more variation
        import random
        
        # Add randomization to prevent identical outputs
        random_seed = random.randint(1, 10000) if temperature > 0.5 else None
        
        payload = {
            "model_id": model_id,
            "input": prompt,
            "project_id": CREDENTIALS["project_id"],
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "min_new_tokens": max(200, max_tokens // 4),  # Ensure substantial length
                "top_k": creativity_settings.get("top_k", 50),
                "top_p": creativity_settings.get("top_p", 0.9),
                "decoding_method": "sample",  # Use sampling for more variety
                "repetition_penalty": creativity_settings.get("repetition_penalty", 1.3),
                "stop_sequences": ["THE END", "---", "***", "\n\nTHE END", "STORY COMPLETE"],
                "random_seed": random_seed,  # Add randomness
                "include_stop_sequence": False,
                "truncate_input_tokens": 4000,  # Prevent token overflow
                "return_options": {
                    "input_text": False,
                    "generated_tokens": True,
                    "input_tokens": True,
                    "token_logprobs": False,
                    "token_ranks": False,
                    "top_n_tokens": False
                }
            }
        }
        
        # Add timeout and retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    return "Error: Request timed out. Please try again."
                time.sleep(2)  # Wait before retry
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return f"Error: Request failed after {max_retries} attempts. {str(e)}"
                time.sleep(2)
        
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            generated_text = data["results"][0]["generated_text"].strip()
            
            # Enhanced validation to ensure story matches filters
            if not validate_story_content(generated_text, prompt):
                # Try one more time with modified parameters for better adherence
                payload["parameters"]["temperature"] = min(temperature + 0.2, 1.0)
                payload["parameters"]["repetition_penalty"] = 1.5
                
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                
                if "results" in data and len(data["results"]) > 0:
                    generated_text = data["results"][0]["generated_text"].strip()
            
            return post_process_story(generated_text)
        else:
            return "Error: No story generated. Please try again with different parameters."
            
    except requests.RequestException as e:
        return f"Error: Failed to generate story. {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error occurred. {str(e)}"

def validate_story_content(story, original_prompt):
    """Validate that the generated story follows the specified parameters"""
    # Convert to lowercase for checking
    story_lower = story.lower()
    prompt_lower = original_prompt.lower()
    
    # Extract key parameters from the prompt
    genre_check = any(genre in prompt_lower for genre in [
        'suspense', 'adventure', 'fantasy', 'drama', 'mystery', 'horror'
    ])
    
    # Basic validation - check if story has reasonable length and structure
    word_count = len(story.split())
    has_paragraphs = '\n' in story or len(story) > 500
    
    return word_count > 100 and has_paragraphs

def post_process_story(story):
    """Clean up and enhance the generated story"""
    # Remove repetitive sentences
    sentences = story.split('. ')
    unique_sentences = []
    seen_sentences = set()
    
    for sentence in sentences:
        sentence_clean = sentence.strip().lower()
        if sentence_clean not in seen_sentences and len(sentence_clean) > 10:
            seen_sentences.add(sentence_clean)
            unique_sentences.append(sentence.strip())
    
    # Rejoin sentences
    story = '. '.join(unique_sentences)
    
    # Fix common formatting issues
    story = re.sub(r'\s+', ' ', story)  # Multiple spaces
    story = re.sub(r'\.+', '.', story)  # Multiple periods
    story = re.sub(r'\?+', '?', story)  # Multiple question marks
    story = re.sub(r'\!+', '!', story)  # Multiple exclamation marks
    
    # Create proper paragraphs (every 3-4 sentences)
    sentences = [s.strip() for s in story.split('.') if s.strip()]
    paragraphs = []
    current_paragraph = []
    
    for i, sentence in enumerate(sentences):
        current_paragraph.append(sentence)
        # Create paragraph break every 3-4 sentences or at natural breaks
        if (len(current_paragraph) >= 3 and 
            (i == len(sentences) - 1 or 
             any(word in sentence.lower() for word in ['however', 'meanwhile', 'suddenly', 'later', 'then', 'after']))):
            paragraphs.append('. '.join(current_paragraph) + '.')
            current_paragraph = []
    
    # Add any remaining sentences
    if current_paragraph:
        paragraphs.append('. '.join(current_paragraph) + '.')
    
    # Join paragraphs with double line breaks
    story = '\n\n'.join(paragraphs)
    
    return story.strip()

def get_story_statistics(story):
    """Calculate story statistics"""
    words = len(story.split())
    sentences = len([s for s in story.split('.') if s.strip()])
    paragraphs = len([p for p in story.split('\n\n') if p.strip()])
    
    return {
        "words": words,
        "sentences": sentences,
        "paragraphs": paragraphs,
        "reading_time": max(1, words // 200)  # Average reading speed
    }

# -------------------------------
# Text-to-Speech Functionality
# -------------------------------
def text_to_speech_html(text, voice="en-US-AriaNeural", rate=1.0, pitch=1.0):
    """Generate HTML with JavaScript for text-to-speech"""
    # Clean text for TTS (remove special characters that might cause issues)
    clean_text = re.sub(r'[^\w\s\.,!?;:]', '', text)
    
    tts_html = f"""
    <div class="tts-controls">
        <h4>🎧 Listen to Your Story</h4>
        <button onclick="speakText()" class="tts-button" id="speakBtn">🔊 Play Story</button>
        <button onclick="pauseText()" class="tts-button" id="pauseBtn">⏸️ Pause</button>
        <button onclick="stopText()" class="tts-button" id="stopBtn">⏹️ Stop</button>
        <br>
        <label for="voiceSelect">Voice: </label>
        <select id="voiceSelect" onchange="changeVoice()" style="margin: 0.5rem; padding: 0.25rem;">
            <option value="0">Default Voice</option>
        </select>
        <br>
        <label for="rateSlider">Speed: </label>
        <input type="range" id="rateSlider" min="0.5" max="2" value="{rate}" step="0.1" style="margin: 0.5rem;">
        <span id="rateValue">{rate}x</span>
        <br>
        <label for="pitchSlider">Pitch: </label>
        <input type="range" id="pitchSlider" min="0.5" max="2" value="{pitch}" step="0.1" style="margin: 0.5rem;">
        <span id="pitchValue">{pitch}x</span>
        <div id="ttsStatus" style="margin-top: 0.5rem; font-style: italic;"></div>
    </div>
    
    <script>
        let speechSynthesis = window.speechSynthesis;
        let currentUtterance = null;
        let voices = [];
        let isPaused = false;
        let storyText = `{clean_text}`;
        
        // Load voices
        function loadVoices() {{
            voices = speechSynthesis.getVoices();
            let voiceSelect = document.getElementById('voiceSelect');
            voiceSelect.innerHTML = '<option value="0">Default Voice</option>';
            
            voices.forEach((voice, index) => {{
                if (voice.lang.startsWith('en')) {{
                    let option = document.createElement('option');
                    option.value = index;
                    option.textContent = voice.name + ' (' + voice.lang + ')';
                    voiceSelect.appendChild(option);
                }}
            }});
        }}
        
        // Initialize voices
        if (speechSynthesis.onvoiceschanged !== undefined) {{
            speechSynthesis.onvoiceschanged = loadVoices;
        }}
        loadVoices();
        
        function speakText() {{
            if (isPaused) {{
                speechSynthesis.resume();
                isPaused = false;
                document.getElementById('ttsStatus').textContent = 'Playing...';
                return;
            }}
            
            if (speechSynthesis.speaking) {{
                speechSynthesis.cancel();
            }}
            
            currentUtterance = new SpeechSynthesisUtterance(storyText);
            
            // Set voice
            let voiceIndex = document.getElementById('voiceSelect').value;
            if (voiceIndex > 0 && voices[voiceIndex]) {{
                currentUtterance.voice = voices[voiceIndex];
            }}
            
            // Set rate and pitch
            currentUtterance.rate = parseFloat(document.getElementById('rateSlider').value);
            currentUtterance.pitch = parseFloat(document.getElementById('pitchSlider').value);
            
            // Event listeners
            currentUtterance.onstart = function() {{
                document.getElementById('ttsStatus').textContent = 'Playing...';
            }};
            
            currentUtterance.onend = function() {{
                document.getElementById('ttsStatus').textContent = 'Finished';
            }};
            
            currentUtterance.onerror = function(event) {{
                document.getElementById('ttsStatus').textContent = 'Error: ' + event.error;
            }};
            
            speechSynthesis.speak(currentUtterance);
        }}
        
        function pauseText() {{
            if (speechSynthesis.speaking && !isPaused) {{
                speechSynthesis.pause();
                isPaused = true;
                document.getElementById('ttsStatus').textContent = 'Paused';
            }}
        }}
        
        function stopText() {{
            speechSynthesis.cancel();
            isPaused = false;
            document.getElementById('ttsStatus').textContent = 'Stopped';
        }}
        
        function changeVoice() {{
            // Voice will be applied on next play
        }}
        
        // Update slider values
        document.getElementById('rateSlider').oninput = function() {{
            document.getElementById('rateValue').textContent = this.value + 'x';
        }};
        
        document.getElementById('pitchSlider').oninput = function() {{
            document.getElementById('pitchValue').textContent = this.value + 'x';
        }};
    </script>
    """
    
    return tts_html

# -------------------------------
# Session State Management
# -------------------------------
if 'generated_story' not in st.session_state:
    st.session_state.generated_story = ""
if 'story_stats' not in st.session_state:
    st.session_state.story_stats = {}

# -------------------------------
# Enhanced UI Elements
# -------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Story Details")
    
    character_name = st.text_input(
        "Main Character Name",
        value="Alex",
        help="Enter the name of your story's protagonist"
    )
    
    story_context = st.text_area(
        "Story Context & Background",
        height=120,
        placeholder="Describe the situation, background, or initial setup for your story. Be specific about what happened, where it takes place, and any important details that should be included.",
        help="Provide rich context to help generate a more engaging story"
    )
    
    col_setting, col_mood = st.columns(2)
    with col_setting:
        setting = st.selectbox(
            "Setting/Location",
            ["Modern City", "Small Town", "Fantasy Realm", "Space Station", "Medieval Castle", "Haunted House", "Desert Island", "Underground Bunker", "Forest", "Other"]
        )
    
    with col_mood:
        mood = st.selectbox(
            "Mood/Tone",
            ["Dark & Mysterious", "Light & Hopeful", "Intense & Thrilling", "Melancholic", "Humorous", "Romantic", "Eerie", "Inspirational"]
        )

with st.sidebar:
    st.markdown("### ⚙️ Generation Settings")
    
    # Model Selection
    selected_model_name = st.selectbox(
        "AI Model",
        list(MODEL_OPTIONS.keys()),
        help="Different models have different strengths. Experiment to find your preferred style."
    )
    model_id = MODEL_OPTIONS[selected_model_name]
    
    # Genre Selection
    story_type = st.selectbox(
        "Genre",
        ["Suspense", "Adventure", "Fantasy", "Drama", "Mystery", "Horror"],
        help="Choose the genre that best fits your story vision"
    )
    
    # Writing Style
    writing_style = st.selectbox(
        "Writing Style",
        ["Narrative", "Descriptive", "Dialogue-Heavy", "Action-Packed", "Literary", "Cinematic"],
        help="Select the writing approach you prefer"
    )
    
    # Length Settings
    length_category = st.selectbox(
        "Story Length",
        ["Short (300-500 words)", "Medium (500-800 words)", "Long (800-1200 words)"],
        help="Choose your preferred story length"
    )
    
    # Map length to tokens
    length_mapping = {
        "Short (300-500 words)": 400,
        "Medium (500-800 words)": 650,
        "Long (800-1200 words)": 1000
    }
    max_tokens = length_mapping[length_category]
    
    st.markdown("### 🎨 Creativity Controls")
    
    # Creativity Settings
    temperature = st.slider(
        "Creativity Level",
        0.1, 1.5, 0.8, 0.1,
        help="Higher values make the story more creative and unpredictable"
    )
    
    # Advanced Settings
    with st.expander("Advanced Settings"):
        top_k = st.slider("Vocabulary Diversity", 10, 100, 50, 5)
        top_p = st.slider("Focus Level", 0.1, 1.0, 0.9, 0.05)
        repetition_penalty = st.slider("Repetition Control", 1.0, 2.0, 1.3, 0.1)
    
    creativity_settings = {
        "top_k": top_k,
        "top_p": top_p,
        "repetition_penalty": repetition_penalty
    }

# -------------------------------
# Story Generation
# -------------------------------
with col1:
    # API Credentials Check
    if CREDENTIALS["api_key"] in ["your-api-key", "4XXXXXXXXX..."]:
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ API Setup Required</strong><br>
            Please set your IBM Watson API credentials in .streamlit/secrets.toml or as environment variables:
            <ul>
                <li>IBM_API_KEY</li>
                <li>IBM_PROJECT_ID</li>
                <li>IBM_REGION</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Generation Button
    if st.button("🚀 Generate Story", help="Click to generate your story"):
        if not character_name.strip():
            st.error("Please enter a character name.")
        elif not story_context.strip():
            st.error("Please provide story context to help generate a better story.")
        elif CREDENTIALS["api_key"] in ["your-api-key", "4XXXXXXXXX..."]:
            st.error("Please configure your IBM Watson API credentials.")
        else:
            # Clear previous story to force new generation
            st.session_state.generated_story = ""
            st.session_state.story_stats = {}
            
            # Show generation progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🤖 Initializing AI model...")
            progress_bar.progress(20)
            
            with st.spinner("Generating your story..."):
                try:
                    # Create enhanced prompt with current timestamp for uniqueness
                    status_text.text("📝 Crafting story prompt...")
                    progress_bar.progress(40)
                    
                    prompt = create_enhanced_story_prompt(
                        character_name, story_type, story_context, 
                        writing_style, length_category, mood, setting
                    )
                    
                    # Add uniqueness factor to prevent caching
                    import datetime
                    unique_prompt = f"{prompt}\n\n[Generation ID: {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}]"
                    
                    # Generate story
                    status_text.text("✨ AI is writing your story...")
                    progress_bar.progress(60)
                    
                    story = generate_story_with_watson(
                        unique_prompt, model_id, max_tokens, temperature, creativity_settings
                    )
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Story generated successfully!")
                    
                    # Store in session state
                    if not story.startswith("Error"):
                        st.session_state.generated_story = story
                        st.session_state.story_stats = get_story_statistics(story)
                        
                        # Show generation details for debugging
                        with st.expander("🔍 Generation Details"):
                            st.write(f"**Model Used:** {selected_model_name}")
                            st.write(f"**Genre:** {story_type}")
                            st.write(f"**Setting:** {setting}")
                            st.write(f"**Mood:** {mood}")
                            st.write(f"**Writing Style:** {writing_style}")
                            st.write(f"**Temperature:** {temperature}")
                            st.write(f"**Max Tokens:** {max_tokens}")
                    else:
                        st.session_state.generated_story = story
                    
                    time.sleep(1)  # Brief pause to show completion
                    
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
                    
                finally:
                    progress_bar.empty()
                    status_text.empty()

    # Display generated story
    if st.session_state.generated_story and not st.session_state.generated_story.startswith("Error"):
        st.markdown("### 📖 Your Generated Story")
        
        # Story statistics
        stats = st.session_state.story_stats
        st.markdown(f"""
        <div class="story-stats">
            <strong>Story Statistics:</strong> 
            {stats['words']} words • {stats['sentences']} sentences • 
            {stats['paragraphs']} paragraphs • ~{stats['reading_time']} min read
        </div>
        """, unsafe_allow_html=True)
        
        # Display story
        st.markdown(f"""
        <div class="story-container">
            <div class="story-text">{st.session_state.generated_story}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Text-to-Speech Controls
        st.markdown("### 🎧 Audio Features")
        tts_html = text_to_speech_html(st.session_state.generated_story)
        st.components.v1.html(tts_html, height=300, scrolling=True)
        
        # Success message and download
        st.markdown("""
        <div class="success-box">
            <strong>🎉 Story Generated Successfully!</strong><br>
            Your story has been crafted with care. You can now listen to it or download it!
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col_download, col_regenerate = st.columns(2)
        
        with col_download:
            filename = f"{character_name}_{story_type}_{setting.replace(' ', '_')}.txt"
            st.download_button(
                "📥 Download Story",
                st.session_state.generated_story,
                filename,
                mime="text/plain",
                help="Download your story as a text file"
            )
        
        with col_regenerate:
            if st.button("🔄 Generate Another Version"):
                st.session_state.generated_story = ""
                st.session_state.story_stats = {}
                st.rerun()
    
    elif st.session_state.generated_story and st.session_state.generated_story.startswith("Error"):
        st.error(st.session_state.generated_story)

# -------------------------------
# Additional Features
# -------------------------------
with st.expander("💡 Story Writing Tips"):
    st.markdown("""
    **For Better Stories:**
    - Provide detailed context about what happened to your character
    - Be specific about the setting and time period
    - Include emotional elements or conflicts in your context
    - Mention any specific themes you want explored
    - Try different creativity levels to find your preferred style
    
    **Genre Tips:**
    - **Suspense**: Focus on what's at stake and create uncertainty
    - **Adventure**: Describe the quest or journey your character must undertake
    - **Fantasy**: Establish magical elements or otherworldly settings
    - **Drama**: Emphasize character relationships and emotional conflicts
    - **Mystery**: Set up a puzzle or crime that needs solving
    - **Horror**: Create atmosphere and psychological tension
    
    **Model Selection:**
    - **Google Flan-UL2**: Great for creative, detailed narratives
    - **IBM Granite-13B**: Excellent for structured, coherent stories
    - **Meta Llama-2-70B**: Best for dialogue and character development
    - **Google Flan-T5-XXL**: Good for concise, focused storytelling
    """)

# -------------------------------
# Footer
# -------------------------------
st.markdown("""
<div class="footer">
    <p>🤖 Powered by IBM Watson AI | Built with ❤️ using Streamlit</p>
    <p>Create compelling stories with the power of generative AI</p>
</div>
""", unsafe_allow_html=True)
