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
# API Configuration - FIXED
# -------------------------------
def get_api_credentials():
    return {
        "api_key": os.getenv("IBM_API_KEY", "your-api-key"),
        "project_id": os.getenv("IBM_PROJECT_ID", "your-project-id"),
        "region": os.getenv("IBM_REGION", "us-south")
    }

CREDENTIALS = get_api_credentials()
VERSION = "2023-05-29"  # Keep original version

# Your original models - they ARE supported!
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
    """Create a sophisticated prompt for better story generation"""
    
    # Define story structure templates
    story_structures = {
        "suspense": {
            "opening": "Create an atmosphere of tension and uncertainty",
            "development": "Build suspense through pacing, foreshadowing, and mystery",
            "climax": "Reveal the truth with maximum impact",
            "resolution": "Provide a satisfying conclusion that ties up loose ends"
        },
        "adventure": {
            "opening": "Establish the quest or journey",
            "development": "Present challenges and obstacles to overcome",
            "climax": "Face the greatest challenge or enemy",
            "resolution": "Achieve the goal and show character growth"
        },
        "fantasy": {
            "opening": "Introduce the magical world and its rules",
            "development": "Explore magical elements and their consequences",
            "climax": "Confront the magical threat or complete the quest",
            "resolution": "Restore balance to the magical world"
        },
        "drama": {
            "opening": "Establish character relationships and conflicts",
            "development": "Deepen emotional conflicts and character development",
            "climax": "Face the emotional crisis or life-changing moment",
            "resolution": "Show character growth and resolution of conflicts"
        },
        "mystery": {
            "opening": "Present the mystery or crime to be solved",
            "development": "Gather clues and red herrings, build intrigue",
            "climax": "Reveal the solution and confront the perpetrator",
            "resolution": "Explain the mystery and show justice served"
        },
        "horror": {
            "opening": "Establish normalcy before introducing the supernatural threat",
            "development": "Escalate fear through psychological and physical terror",
            "climax": "Confront the ultimate horror",
            "resolution": "Survive or succumb to the horror with lasting impact"
        }
    }
    
    structure = story_structures.get(story_type.lower(), story_structures["adventure"])
    
    # Enhanced prompt with better instructions
    prompt = f"""Write a compelling {story_type.lower()} story with the following specifications:

STORY REQUIREMENTS:
- Main Character: {character_name}
- Genre: {story_type}
- Setting: {setting}
- Mood/Tone: {mood}
- Writing Style: {writing_style}
- Length: {length_category}

STORY CONTEXT:
{context}

STRUCTURE:
- Opening: {structure['opening']}
- Development: {structure['development']}
- Climax: {structure['climax']}
- Resolution: {structure['resolution']}

Write a complete, engaging story with vivid descriptions, compelling characters, and natural dialogue. Create clear paragraphs and maintain consistent pacing throughout.

Story:"""

    return prompt

# -------------------------------
# Fixed IBM Watson API Integration
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
    """Fixed story generation with correct watsonx.ai API endpoint"""
    token = get_iam_token(CREDENTIALS["api_key"])
    if not token:
        return "Error: Could not authenticate with IBM Watson. Please check your API credentials."

    try:
        # Fixed: Use correct watsonx.ai endpoint
        url = f"https://{CREDENTIALS['region']}.ml.cloud.ibm.com/ml/v1/text/generation?version={VERSION}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Enhanced parameters for better story generation
        payload = {
            "model_id": model_id,
            "input": prompt,
            "project_id": CREDENTIALS["project_id"],
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "min_new_tokens": max(300, max_tokens // 3),  # Ensure longer stories
                "top_k": creativity_settings.get("top_k", 50),
                "top_p": creativity_settings.get("top_p", 0.9),
                "decoding_method": "sample",
                "repetition_penalty": creativity_settings.get("repetition_penalty", 1.3),
                "stop_sequences": ["THE END", "---", "***", "\n\nTHE END"],
                "random_seed": None,  # Allow for randomness
                "include_stop_sequence": False
            }
        }
        
        # Debug: Show detailed request info
        st.info(f"🔍 Debug Info:")
        st.info(f"Model: {model_id}")
        st.info(f"Region: {CREDENTIALS['region']}")
        st.info(f"API Version: {VERSION}")
        st.info(f"Full URL: {url}")
        
        # Try the request
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        # Better error handling
        if response.status_code == 404:
            return f"Error: API endpoint not found. Please verify your IBM Watson configuration and model availability. Model: {model_id}"
        elif response.status_code == 401:
            return "Error: Authentication failed. Please check your API key and project ID."
        elif response.status_code == 403:
            return "Error: Access denied. Please verify your project permissions and instance ID."
        
        response.raise_for_status()
        
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            generated_text = data["results"][0]["generated_text"].strip()
            return post_process_story(generated_text)
        else:
            return f"Error: No story generated. API Response: {data}"
            
    except requests.RequestException as e:
        return f"Error: Failed to generate story. Status: {response.status_code if 'response' in locals() else 'Unknown'}, Details: {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error occurred. {str(e)}"

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
# Fallback Local Story Generation
# -------------------------------
def generate_local_story(character_name, story_type, context, setting, mood):
    """Fallback story generation when API is not available"""
    story_templates = {
        "adventure": f"""The morning sun cast long shadows across {setting.lower()} as {character_name} prepared for what would become the most challenging day of their life. {context}

The air was {mood.lower().split()[0]} as {character_name} stepped forward, heart pounding with anticipation. Every instinct told them to turn back, but something deeper—a calling they couldn't ignore—urged them onward.

As the hours passed, obstacles seemed to emerge from nowhere. Each challenge tested not just {character_name}'s physical abilities, but their resolve and determination. The path ahead grew increasingly treacherous, yet with each step, they discovered inner strength they never knew existed.

The final confrontation came suddenly. Standing at the precipice of their greatest fear, {character_name} realized that the journey had changed them fundamentally. The person who had started this adventure was gone, replaced by someone stronger, wiser, and more capable than they had ever imagined possible.

As the dust settled and the immediate danger passed, {character_name} looked back on their journey with a mixture of exhaustion and pride. They had not only survived but had emerged victorious, carrying with them lessons that would last a lifetime.""",
        
        "mystery": f"""The first clue appeared in {setting.lower()} on a {mood.lower()} Tuesday morning. {character_name} had seen enough puzzles in their career to know when something didn't add up, and this case was full of contradictions. {context}

As {character_name} began to investigate, a pattern slowly emerged from the chaos. Each piece of evidence seemed to point in a different direction, creating a web of confusion that would challenge even the most experienced investigator.

Red herrings appeared at every turn, deliberately placed to mislead and confuse. But {character_name} had learned to look beyond the obvious, to see connections that others might miss. The breakthrough came when they realized they had been asking the wrong questions entirely.

The truth, when it finally revealed itself, was both shocking and inevitable. All the pieces fell into place with startling clarity, showing how carefully orchestrated the entire scheme had been from the beginning.

In the end, justice was served, but {character_name} couldn't shake the feeling that some mysteries are better left unsolved. The case was closed, but the questions it raised would linger for years to come."""
    }
    
    template = story_templates.get(story_type.lower(), story_templates["adventure"])
    return template

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
    
    # Fallback option
    use_fallback = st.checkbox("Use Local Fallback if API fails", help="Generate a basic story locally if the IBM Watson API is unavailable")

# -------------------------------
# Story Generation
# -------------------------------
with col1:
    # API Credentials Check
    if CREDENTIALS["api_key"] == "your-api-key":
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ API Setup Required</strong><br>
            Please set your IBM Watson API credentials as environment variables:
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
        else:
            # Show generation progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🤖 Initializing AI model...")
            progress_bar.progress(20)
            
            with st.spinner("Generating your story..."):
                try:
                    story = None
                    
                    # Try IBM Watson API if credentials are configured
                    if CREDENTIALS["api_key"] != "your-api-key":
                        # Create enhanced prompt
                        status_text.text("📝 Crafting story prompt...")
                        progress_bar.progress(40)
                        
                        prompt = create_enhanced_story_prompt(
                            character_name, story_type, story_context, 
                            writing_style, length_category, mood, setting
                        )
                        
                        # Generate story
                        status_text.text("✨ AI is writing your story...")
                        progress_bar.progress(60)
                        
                        story = generate_story_with_watson(
                            prompt, model_id, max_tokens, temperature, creativity_settings
                        )
                        
                        # If API fails and fallback is enabled, use local generation
                        if story.startswith("Error") and use_fallback:
                            status_text.text("🔄 Using fallback story generation...")
                            story = generate_local_story(character_name, story_type, story_context, setting, mood)
                    
                    # Use local generation if no API credentials or if enabled
                    elif use_fallback or CREDENTIALS["api_key"] == "your-api-key":
                        status_text.text("📖 Generating story locally...")
                        progress_bar.progress(80)
                        story = generate_local_story(character_name, story_type, story_context, setting, mood)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Story generated successfully!")
                    
                    # Display results
                    if story and not story.startswith("Error"):
                        st.markdown("### 📖 Your Generated Story")
                        
                        # Story statistics
                        stats = get_story_statistics(story)
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
                            <div class="story-text">{story}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Success message and download
                        st.markdown("""
                        <div class="success-box">
                            <strong>🎉 Story Generated Successfully!</strong><br>
                            Your story has been crafted with care. Feel free to generate variations or try different settings.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Download button
                        filename = f"{character_name}_{story_type}_{setting.replace(' ', '_')}.txt"
                        st.download_button(
                            "📥 Download Story",
                            story,
                            filename,
                            mime="text/plain",
                            help="Download your story as a text file"
                        )
                        
                        # Regeneration option
                        if st.button("🔄 Generate Another Version"):
                            st.rerun()
                            
                    else:
                        st.error(story or "Failed to generate story. Please check your configuration.")
                        
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
                    
                finally:
                    progress_bar.empty()
                    status_text.empty()

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
    - **Drama**: Emphasize emotional conflicts and relationships
    - **Mystery**: Present a puzzle or crime that needs solving
    - **Horror**: Create atmosphere with fear-inducing elements
    """)

with st.expander("🔧 Troubleshooting"):
    st.markdown("""
    **Common Issues & Solutions:**
    - **404 Error**: Check your IBM Watson endpoint URL and model availability
    - **401 Error**: Verify your API key and authentication
    - **403 Error**: Ensure your project ID and instance ID are correct
    - **Repetitive text**: Increase repetition penalty or try a different model
    - **Story too short**: Increase max tokens or provide more context
    - **Off-topic content**: Be more specific in your story context
    
    **IBM Watson Setup:**
    1. Create a Watson Machine Learning service instance
    2. Create a watsonx.ai project
    3. Get your API key from IBM Cloud IAM
    4. Copy your project ID from the project settings
    5. Note your service region and instance ID
    
    **Model Recommendations:**
    - **IBM Granite 13B Instruct**: Great for structured, instructional stories
    - **IBM Granite 13B Chat**: Excellent for dialogue-heavy narratives
    - **Meta Llama 2 70B**: Superior for complex, nuanced stories
    - **IBM Granite 20B Code**: Good for technical or sci-fi stories
    """)

# -------------------------------
# Footer
# -------------------------------
st.markdown("""
<div class="footer">
    <p>Powered by IBM WatsonX AI | Created with Streamlit | Enhanced Story Generation v2.1</p>
    <p>💡 Tip: Experiment with different models and settings to discover your perfect story style!</p>
</div>
""", unsafe_allow_html=True)
