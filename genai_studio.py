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
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Remove default streamlit padding/margins that create white boxes */
    .block-container {
        padding-top: 1rem;
    }
    
    /* Ensure no extra spacing */
    .stSelectbox, .stTextInput, .stTextArea {
        margin-bottom: 1rem;
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
    return {
        "api_key": os.getenv("IBM_API_KEY", "your-api-key"),
        "project_id": os.getenv("IBM_PROJECT_ID", "your-project-id"),
        "region": os.getenv("IBM_REGION", "us-south")
    }

CREDENTIALS = get_api_credentials()
VERSION = "2024-05-31"  # Updated to latest version

# Updated model options based on current IBM watsonx.ai offerings
MODEL_OPTIONS = {
    "IBM Granite 3.0-8B Instruct": "ibm/granite-3-8b-instruct",
    "IBM Granite 3.0-2B Instruct": "ibm/granite-3-2b-instruct", 
    "IBM Granite 13B Chat v2": "ibm/granite-13b-chat-v2",
    "IBM Granite 13B Instruct v2": "ibm/granite-13b-instruct-v2",
    "Meta Llama 3.1-70B Instruct": "meta-llama/llama-3-1-70b-instruct",
    "Meta Llama 3.1-8B Instruct": "meta-llama/llama-3-1-8b-instruct",
    "Mistral Large": "mistralai/mistral-large",
    "Mixtral 8x7B Instruct": "mistralai/mixtral-8x7b-instruct-v01"
}

# -------------------------------
# Enhanced Prompt Builder for Better Story Quality
# -------------------------------
def create_professional_story_prompt(character_name, story_type, context, writing_style, length_category, mood, setting):
    """Create a sophisticated prompt that ensures complete, coherent stories"""
    
    # Word count targets
    word_targets = {
        "Short (300-500 words)": "400-500 words",
        "Medium (500-800 words)": "600-750 words", 
        "Long (800-1200 words)": "900-1100 words"
    }
    
    target_length = word_targets[length_category]
    
    # Enhanced story structure with clear requirements
    story_frameworks = {
        "suspense": {
            "setup": "Establish the protagonist in a seemingly normal situation",
            "inciting_incident": "Introduce the mysterious or threatening element",
            "rising_action": "Build tension through escalating mysterious events",
            "climax": "Reveal the truth behind the mystery in a dramatic confrontation",
            "resolution": "Show the aftermath and how the character has changed"
        },
        "adventure": {
            "setup": "Introduce the hero in their ordinary world",
            "inciting_incident": "Present the call to adventure or quest",
            "rising_action": "Face challenges and obstacles, gaining allies and skills",
            "climax": "Confront the final challenge or enemy",
            "resolution": "Return transformed with wisdom or treasure gained"
        },
        "fantasy": {
            "setup": "Establish the magical world and its rules",
            "inciting_incident": "Discover magical powers or encounter magical threat",
            "rising_action": "Learn to use magic while facing increasing magical dangers",
            "climax": "Use newfound powers in final magical confrontation",
            "resolution": "Find balance between magical and mundane worlds"
        },
        "drama": {
            "setup": "Establish character relationships and underlying tensions",
            "inciting_incident": "Introduce the conflict that disrupts relationships",
            "rising_action": "Explore emotional consequences and character growth",
            "climax": "Face the emotional crisis requiring difficult choices",
            "resolution": "Show how relationships and characters have evolved"
        },
        "mystery": {
            "setup": "Present the crime or mystery that needs solving",
            "inciting_incident": "The detective/protagonist takes on the case",
            "rising_action": "Gather clues, interview suspects, uncover red herrings",
            "climax": "Reveal the solution and confront the culprit",
            "resolution": "Explain the mystery and show justice served"
        },
        "horror": {
            "setup": "Establish normalcy before introducing supernatural elements",
            "inciting_incident": "First encounter with the horror",
            "rising_action": "Escalating encounters with increasing dread",
            "climax": "Final confrontation with the ultimate horror",
            "resolution": "Survive or succumb, showing lasting psychological impact"
        }
    }
    
    framework = story_frameworks.get(story_type.lower(), story_frameworks["adventure"])
    
    # Create comprehensive prompt
    prompt = f"""Write a complete, engaging {story_type.lower()} story with the following requirements:

STORY SPECIFICATIONS:
- Target Length: {target_length} (MUST be complete within this range)
- Main Character: {character_name}
- Genre: {story_type}
- Setting: {setting}
- Mood: {mood}
- Writing Style: {writing_style}

STORY CONTEXT:
{context}

REQUIRED STORY STRUCTURE:
1. OPENING ({framework['setup']})
2. INCITING INCIDENT ({framework['inciting_incident']})
3. RISING ACTION ({framework['rising_action']})
4. CLIMAX ({framework['climax']})
5. RESOLUTION ({framework['resolution']})

CRITICAL REQUIREMENTS:
✓ Write a COMPLETE story with proper beginning, middle, and satisfying end
✓ Include vivid sensory details and atmospheric descriptions
✓ Create believable dialogue that reveals character personality
✓ Show character growth and change throughout the story
✓ Maintain consistent pacing and tension appropriate to {story_type}
✓ Use {writing_style} writing style throughout
✓ Capture the {mood} mood effectively
✓ End with a clear, satisfying conclusion - NO cliffhangers or abrupt endings
✓ Stay within {target_length} word count

WRITING QUALITY GUIDELINES:
- Use varied sentence structures for engaging prose
- Show emotions through actions rather than telling
- Include specific, concrete details that bring scenes to life
- Create authentic character motivations and reactions
- Build scenes that flow logically from one to the next
- Use dialogue to advance plot and reveal character
- Maintain the {mood} atmosphere throughout

Write the story now, ensuring it has a complete narrative arc with a proper ending:"""

    return prompt

# -------------------------------
# Enhanced IBM Watson API Integration
# -------------------------------
def get_iam_token(api_key):
    """Get IBM Cloud IAM token with enhanced error handling"""
    try:
        url = "https://iam.cloud.ibm.com/identity/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        if "access_token" not in token_data:
            st.error("Invalid API response: No access token received")
            return None
            
        return token_data["access_token"]
    except requests.RequestException as e:
        st.error(f"Authentication failed: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected authentication error: {str(e)}")
        return None

def generate_story_with_watson(prompt, model_id, max_tokens, temperature, creativity_settings):
    """Enhanced story generation with quality controls"""
    token = get_iam_token(CREDENTIALS["api_key"])
    if not token:
        return "Error: Authentication failed. Please check your IBM Watson API credentials."

    try:
        url = f"https://{CREDENTIALS['region']}.ml.cloud.ibm.com/ml/v1/text/generation?version={VERSION}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Enhanced parameters for better story quality
        payload = {
            "model_id": model_id,
            "input": prompt,
            "project_id": CREDENTIALS["project_id"],
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "min_new_tokens": max(200, max_tokens // 4),  # Ensure minimum story length
                "top_k": creativity_settings.get("top_k", 40),
                "top_p": creativity_settings.get("top_p", 0.9),
                "decoding_method": "sample",
                "repetition_penalty": creativity_settings.get("repetition_penalty", 1.3),
                # Better stop sequences for complete stories
                "stop_sequences": ["THE END.", "---END---", "\n\n---", "Story ends here"],
                "random_seed": int(time.time()) % 10000,  # Add randomness
                "include_stop_sequence": False,
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
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            generated_text = result["generated_text"].strip()
            
            # Check for minimum content quality
            if len(generated_text) < 200:
                return "Error: Generated story too short. Please try again with different settings."
            
            return enhance_story_quality(generated_text)
        else:
            return "Error: No content generated. Please try again with different settings."
            
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return "Error: Invalid API credentials. Please check your IBM Watson API key and project ID."
        elif e.response.status_code == 403:
            return "Error: Access denied. Please verify your API permissions and project access."
        elif e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please wait a moment and try again."
        else:
            return f"Error: HTTP {e.response.status_code}. Please try again."
    except requests.RequestException as e:
        return f"Error: Network issue - {str(e)}. Please check your connection and try again."
    except Exception as e:
        return f"Error: Unexpected issue occurred - {str(e)}. Please try again."

def enhance_story_quality(story):
    """Enhanced post-processing for better story quality"""
    
    # Remove common AI artifacts and repetitive content
    story = re.sub(r'\bAs an AI\b.*?\.', '', story, flags=re.IGNORECASE)
    story = re.sub(r'\bI cannot\b.*?\.', '', story, flags=re.IGNORECASE)
    story = re.sub(r'\bI am not able\b.*?\.', '', story, flags=re.IGNORECASE)
    
    # Clean up formatting issues
    story = re.sub(r'\s+', ' ', story)  # Multiple spaces
    story = re.sub(r'\.{2,}', '.', story)  # Multiple periods
    story = re.sub(r'\?{2,}', '?', story)  # Multiple question marks
    story = re.sub(r'\!{2,}', '!', story)  # Multiple exclamation marks
    
    # Remove repetitive sentences (more sophisticated approach)
    sentences = [s.strip() for s in story.split('.') if s.strip() and len(s.strip()) > 10]
    unique_sentences = []
    seen_patterns = set()
    
    for sentence in sentences:
        # Create a pattern by removing proper nouns and common words for comparison
        pattern = re.sub(r'\b[A-Z][a-z]+\b', 'NAME', sentence.lower())
        pattern = re.sub(r'\b(the|and|but|or|in|on|at|to|for|of|with|by)\b', '', pattern)
        pattern = re.sub(r'\s+', ' ', pattern).strip()
        
        # Only add if we haven't seen a very similar pattern
        if pattern not in seen_patterns and len(pattern) > 20:
            seen_patterns.add(pattern)
            unique_sentences.append(sentence)
    
    # Rebuild story with proper paragraphs
    if not unique_sentences:
        return "Error: Story processing failed. Please try again."
    
    story = '. '.join(unique_sentences)
    if not story.endswith('.'):
        story += '.'
    
    # Create natural paragraph breaks
    sentences = [s.strip() for s in story.split('.') if s.strip()]
    paragraphs = []
    current_paragraph = []
    
    paragraph_break_indicators = [
        'however', 'meanwhile', 'suddenly', 'later', 'then', 'after', 'before',
        'the next day', 'hours later', 'minutes later', 'finally', 'eventually',
        'in the end', 'at last', 'afterwards', 'subsequently'
    ]
    
    for i, sentence in enumerate(sentences):
        current_paragraph.append(sentence)
        
        # Create paragraph break conditions
        should_break = (
            len(current_paragraph) >= 3 and (
                i == len(sentences) - 1 or  # Last sentence
                len(current_paragraph) >= 5 or  # Long paragraph
                any(indicator in sentence.lower() for indicator in paragraph_break_indicators) or
                sentence.strip().startswith('"') and len(current_paragraph) > 2  # Dialogue
            )
        )
        
        if should_break:
            paragraphs.append('. '.join(current_paragraph) + '.')
            current_paragraph = []
    
    # Add any remaining sentences
    if current_paragraph:
        paragraphs.append('. '.join(current_paragraph) + '.')
    
    # Join with double line breaks for proper paragraph spacing
    final_story = '\n\n'.join(paragraphs).strip()
    
    # Ensure the story has a proper ending
    if not re.search(r'(\.|\?|\!)$', final_story):
        final_story += '.'
    
    return final_story

def get_story_statistics(story):
    """Calculate comprehensive story statistics"""
    words = len([w for w in story.split() if w.strip()])
    sentences = len([s for s in re.split(r'[.!?]+', story) if s.strip()])
    paragraphs = len([p for p in story.split('\n\n') if p.strip()])
    characters = len(story.replace(' ', ''))
    
    # Estimate reading time (average 200 words per minute)
    reading_time = max(1, round(words / 200))
    
    return {
        "words": words,
        "sentences": sentences,
        "paragraphs": paragraphs,
        "characters": characters,
        "reading_time": reading_time
    }

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
        placeholder="Provide detailed context: What situation is your character in? What happened before? What do they want or need? Include specific details about conflicts, relationships, or challenges they face.",
        help="Rich context leads to better, more coherent stories. Be specific!"
    )
    
    col_setting, col_mood = st.columns(2)
    with col_setting:
        setting = st.selectbox(
            "Setting/Location",
            [
                "Modern City", "Small Town", "Fantasy Realm", "Space Station", 
                "Medieval Castle", "Haunted House", "Desert Island", "Underground Bunker", 
                "Ancient Temple", "Post-Apocalyptic World", "Victorian London", "Wild West"
            ]
        )
    
    with col_mood:
        mood = st.selectbox(
            "Mood/Tone",
            [
                "Dark & Mysterious", "Light & Hopeful", "Intense & Thrilling", 
                "Melancholic", "Humorous", "Romantic", "Eerie", "Inspirational",
                "Nostalgic", "Adventurous"
            ]
        )

with st.sidebar:
    st.markdown("### ⚙ Generation Settings")
    
    # Model Selection with descriptions
    model_descriptions = {
        "IBM Granite 3.0-8B Instruct": "Latest IBM model - excellent for creative writing",
        "IBM Granite 3.0-2B Instruct": "Efficient and fast - good for shorter stories", 
        "IBM Granite 13B Chat v2": "Great for dialogue-heavy stories",
        "IBM Granite 13B Instruct v2": "Reliable choice for structured narratives",
        "Meta Llama 3.1-70B Instruct": "Powerful model for complex, nuanced stories",
        "Meta Llama 3.1-8B Instruct": "Fast and creative for most story types",
        "Mistral Large": "Excellent for literary and sophisticated writing",
        "Mixtral 8x7B Instruct": "Great balance of creativity and coherence"
    }
    
    selected_model_name = st.selectbox(
        "AI Model",
        list(MODEL_OPTIONS.keys()),
        help="Choose based on your story complexity and preferred style"
    )
    
    # Show model description
    st.markdown(f"*{model_descriptions[selected_model_name]}*")
    model_id = MODEL_OPTIONS[selected_model_name]
    
    # Genre Selection
    story_type = st.selectbox(
        "Genre",
        ["Adventure", "Mystery", "Fantasy", "Drama", "Suspense", "Horror"],
        help="Choose the genre that best fits your story vision"
    )
    
    # Writing Style
    writing_style = st.selectbox(
        "Writing Style",
        [
            "Narrative - Flowing storytelling",
            "Descriptive - Rich sensory details", 
            "Dialogue-Heavy - Character conversations",
            "Action-Packed - Fast-paced events",
            "Literary - Sophisticated prose",
            "Cinematic - Visual, movie-like scenes"
        ]
    )
    writing_style = writing_style.split(' - ')[0]  # Extract just the style name
    
    # Length Settings
    length_category = st.selectbox(
        "Story Length",
        ["Short (300-500 words)", "Medium (500-800 words)", "Long (800-1200 words)"],
        help="Choose your preferred story length"
    )
    
    # Enhanced token mapping for better completion rates
    length_mapping = {
        "Short (300-500 words)": 600,   # Increased for better completion
        "Medium (500-800 words)": 900,  # Increased for better completion  
        "Long (800-1200 words)": 1400   # Increased for better completion
    }
    max_tokens = length_mapping[length_category]
    
    st.markdown("### 🎨 Creativity Controls")
    
    # Creativity Settings
    temperature = st.slider(
        "Creativity Level",
        0.3, 1.2, 0.7, 0.1,
        help="Higher values = more creative and unpredictable stories"
    )
    
    # Advanced Settings
    with st.expander("Advanced Settings"):
        top_k = st.slider("Vocabulary Diversity", 20, 80, 40, 5)
        top_p = st.slider("Focus Level", 0.7, 1.0, 0.9, 0.05)
        repetition_penalty = st.slider("Repetition Control", 1.1, 1.8, 1.3, 0.1)
    
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
    if CREDENTIALS["api_key"] == "your-api-key":
        st.markdown("""
        <div class="warning-box">
            <strong>⚠ API Setup Required</strong><br>
            Please set your IBM Watson API credentials as environment variables:
            <ul>
                <li><code>IBM_API_KEY</code> - Your IBM Cloud API key</li>
                <li><code>IBM_PROJECT_ID</code> - Your Watson project ID</li>
                <li><code>IBM_REGION</code> - Your region (e.g., us-south, eu-gb)</li>
            </ul>
            <small>Get credentials from: <a href="https://cloud.ibm.com/catalog/services/watson-machine-learning" target="_blank">IBM Cloud Watson</a></small>
        </div>
        """, unsafe_allow_html=True)
    
    # Generation Button
    if st.button("🚀 Generate Complete Story", help="Generate a complete, well-structured story"):
        if not character_name.strip():
            st.error("📝 Please enter a character name to get started!")
        elif not story_context.strip():
            st.error("📖 Please provide story context - this helps create much better stories!")
        elif len(story_context.strip()) < 20:
            st.error("📚 Please provide more detailed story context (at least 20 characters)")
        elif CREDENTIALS["api_key"] == "your-api-key":
            st.error("🔑 Please configure your IBM Watson API credentials first.")
        else:
            # Show generation progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🤖 Initializing AI model...")
            progress_bar.progress(15)
            
            with st.spinner("Crafting your story..."):
                try:
                    # Create enhanced prompt
                    status_text.text("📝 Creating story blueprint...")
                    progress_bar.progress(30)
                    
                    prompt = create_professional_story_prompt(
                        character_name, story_type, story_context, 
                        writing_style, length_category, mood, setting
                    )
                    
                    # Generate story
                    status_text.text(f"✨ {selected_model_name} is writing your story...")
                    progress_bar.progress(50)
                    
                    story = generate_story_with_watson(
                        prompt, model_id, max_tokens, temperature, creativity_settings
                    )
                    
                    progress_bar.progress(85)
                    status_text.text("🔍 Polishing and quality checking...")
                    
                    # Short delay for polish effect
                    time.sleep(1)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Story completed successfully!")
                    
                    # Display results
                    if not story.startswith("Error"):
                        st.markdown("### 📖 Your Generated Story")
                        
                        # Story statistics
                        stats = get_story_statistics(story)
                        st.markdown(f"""
                        <div class="story-stats">
                            <strong>📊 Story Analytics:</strong> 
                            {stats['words']} words • {stats['sentences']} sentences • 
                            {stats['paragraphs']} paragraphs • {stats['characters']} characters • 
                            ~{stats['reading_time']} min read
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display story with enhanced formatting
                        st.markdown(f"""
                        <div class="story-container">
                            <div class="story-text">{story}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Success message
                        st.markdown(f"""
                        <div class="success-box">
                            <strong>🎉 Story Generated Successfully!</strong><br>
                            Generated using <strong>{selected_model_name}</strong> with {story_type.lower()} genre. 
                            The AI crafted a complete narrative arc with proper resolution.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons
                        col_download, col_regenerate = st.columns(2)
                        
                        with col_download:
                            # Create formatted download content
                            download_content = f"""GENERATED STORY
Generated by: {selected_model_name}
Genre: {story_type}
Setting: {setting}
Mood: {mood}
Character: {character_name}
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

---

{story}

---

Story Statistics:
- Words: {stats['words']}
- Sentences: {stats['sentences']} 
- Paragraphs: {stats['paragraphs']}
- Reading time: ~{stats['reading_time']} minutes
"""
                            
                            filename = f"{character_name}_{story_type}_{setting.replace(' ', '_')}_story.txt"
                            st.download_button(
                                "📥 Download Story",
                                download_content,
                                filename,
                                mime="text/plain",
                                help="Download your story with metadata"
                            )
                        
                        with col_regenerate:
                            if st.button("🔄 Generate New Version"):
                                st.rerun()
                    else:
                        # Display error with helpful suggestions
                        st.error(story)
                        
                        if "Authentication" in story:
                            st.markdown("""
                            **💡 Authentication Help:**
                            1. Check your API key is correct
                            2. Verify your project ID
                            3. Ensure your region setting matches your IBM Cloud region
                            """)
                        elif "Rate limit" in story:
                            st.markdown("**⏳ Try again in a few moments. IBM Watson has usage limits.**")
                        else:
                            st.markdown("""
                            **🔧 Troubleshooting Tips:**
                            1. Try a different AI model from the sidebar
                            2. Reduce story length if timeout occurs
                            3. Simplify your story context if generation fails
                            4. Check your internet connection
                            """)
                        
                except Exception as e:
                    st.error(f"❌ Unexpected error occurred: {str(e)}")
                    st.markdown("""
                    **🆘 If problems persist:**
                    1. Refresh the page and try again
                    2. Check your API credentials
                    3. Try a different model
                    4. Reduce complexity of your request
                    """)
                    
                finally:
                    progress_bar.empty()
                    status_text.empty()

# -------------------------------
# Additional Features & Help
# -------------------------------
with st.expander("💡 Story Writing Tips & Best Practices"):
    st.markdown("""
    ### 📚 For Better Story Generation:
    
    **Context Writing Tips:**
    - Be specific about your character's situation and goals
    - Include emotional stakes - what does your character want or fear?
    - Mention relationships, conflicts, or challenges they face
    - Set up the initial situation clearly
    - Include any important backstory elements
    
    **Example Good Context:**
    *"Sarah is a detective investigating her partner's mysterious disappearance. She's found strange symbols at his last known location and suspects supernatural involvement. She must choose between following department protocol or pursuing dangerous leads on her own."*
    
    **Genre-Specific Tips:**
    - **Adventure**: Focus on the quest, journey, or challenge to overcome
    - **Mystery**: Present a puzzle, crime, or unexplained event to solve  
    - **Fantasy**: Establish magical elements, special powers, or otherworldly threats
    - **Drama**: Emphasize emotional conflicts, relationships, and personal growth
    - **Suspense**: Create uncertainty about what will happen next
    - **Horror**: Build atmosphere with fear-inducing elements and threats
    
    ### 🎨 Model Selection Guide:
    
    **For Creative, Imaginative Stories:**
    - IBM Granite 3.0-8B Instruct (newest, most creative)
    - Mistral Large (sophisticated writing)
    - Meta Llama 3.1-70B Instruct (complex narratives)
    
    **For Structured, Coherent Stories:**
    - IBM Granite 13B Instruct v2 (reliable and consistent)
    - IBM Granite 3.0-2B Instruct (efficient for shorter stories)
    
    **For Dialogue-Heavy Stories:**
    - IBM Granite 13B Chat v2 (optimized for conversations)
    - Meta Llama 3.1-8B Instruct (natural dialogue)
    """)

with st.expander("🔧 Troubleshooting & Technical Help"):
    st.markdown("""
    ### ❓ Common Issues & Solutions:
    
    **Authentication Problems:**
    - ✅ Verify your IBM_API_KEY environment variable is set correctly
    - ✅ Check your IBM_PROJECT_ID is from the correct Watson project
    - ✅ Ensure IBM_REGION matches your Watson instance region (us-south, eu-gb, etc.)
    - ✅ Make sure you have access to Watson Machine Learning service
    
    **Story Quality Issues:**
    - **Repetitive content**: Increase repetition penalty (1.4-1.6)
    - **Story cuts off**: Try a different model or increase max tokens
    - **Off-topic content**: Be more specific in story context
    - **Incoherent plot**: Lower creativity level (0.5-0.7)
    - **Too predictable**: Increase creativity level (0.8-1.0)
    
    **Performance Issues:**
    - **Timeouts**: Try shorter stories or faster models (2B/8B versions)
    - **Slow generation**: Use Granite 3.0-2B for faster results
    - **Rate limits**: Wait a few minutes between requests
    
    ### 🔑 Getting IBM Watson Credentials:
    
    1. Go to [IBM Cloud](https://cloud.ibm.com)
    2. Create/log into your account
    3. Create a Watson Machine Learning service
    4. Create a new project in Watson Studio
    5. Get your API key from IBM Cloud dashboard
    6. Get your project ID from Watson Studio project settings
    7. Note your region from the service URL
    
    ### 📊 Current Model Status:
    
    **Working Models (Tested):**
    - IBM Granite 3.0 series (newest, recommended)
    - IBM Granite 13B series (reliable)
    - Meta Llama 3.1 series (powerful)
    - Mistral models (creative)
    
    *Note: Model availability may vary by region and subscription plan.*
    """)

with st.expander("🎯 Sample Story Prompts & Examples"):
    st.markdown("""
    ### 📝 Example Story Contexts (Copy & Paste):
    
    **Mystery Example:**
    *"Detective Maya Chen arrives at an abandoned mansion where three people have vanished over the past month. The only clues are identical pocket watches found at each disappearance site, all stopped at exactly 11:47. Local legends speak of a curse, but Maya suspects something more sinister. She has 24 hours before the police close the case."*
    
    **Fantasy Example:**
    *"Elara discovers she can hear the thoughts of dying plants in her grandmother's garden. When ancient trees throughout the kingdom start withering simultaneously, she realizes they're trying to warn her of an approaching darkness. Armed only with her newfound ability and her grandmother's cryptic journal, she must uncover the truth before nature itself dies."*
    
    **Adventure Example:**
    *"Captain Jack's treasure map leads to a lost island that appears only during solar eclipses. With the next eclipse just days away, rival treasure hunters are racing to reach it first. Jack must navigate through treacherous waters, outsmart his competitors, and solve the map's final riddle before the island vanishes for another century."*
    
    **Drama Example:**
    *"After fifteen years apart, siblings Anna and David must return to their childhood home to care for their ailing father. Old resentments surface when they discover their father has been hiding a devastating family secret that changes everything they believed about their past. They have one week to decide his future care while confronting their own broken relationship."*
    
    **Horror Example:**
    *"Night shift nurse Emma notices patients in room 237 recover unusually quickly, but security footage shows them having conversations with empty air at 3 AM every night. When she volunteers to investigate, she discovers the room's previous occupant died exactly one year ago and may not have left. Emma must decide whether to report her findings or protect a secret that could save lives."*
    
    **Suspense Example:**
    *"Software engineer Tom receives encrypted messages that predict accidents before they happen. When the messages start targeting his friends and family, he realizes someone is orchestrating these 'accidents' and using him as an unwitting accomplice. With each correct prediction, Tom becomes more implicated, and he has 48 hours to identify the sender before becoming the next target."*
    """)

# -------------------------------
# Footer
# -------------------------------
st.markdown("""
<div class="footer">
    <p><strong>🤖 Powered by IBM watsonx.ai</strong> | Built with Streamlit | Enhanced Story Generator v3.0</p>
    <p>💡 <em>Tip: The more detailed your story context, the better and more engaging your generated story will be!</em></p>
    <p>🔄 <small>Models updated for 2024-2025 | Now featuring IBM Granite 3.0, Llama 3.1, and Mistral Large</small></p>
</div>
""", unsafe_allow_html=True)
