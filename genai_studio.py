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
    .block-container { padding-top: 1rem; }
    .stSelectbox, .stTextInput, .stTextArea { margin-bottom: 1rem; }
</style>
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
VERSION = "2023-05-29"

MODEL_OPTIONS = {
    "Google Flan-UL2": "google/flan-ul2",
    "IBM Granite-13B": "ibm/granite-13b-instruct-v2",
    "Meta Llama-2-70B": "meta-llama/llama-2-70b-chat",
    "Google Flan-T5-XXL": "google/flan-t5-xxl"
}

# -------------------------------
# Model Availability Check
# -------------------------------
def get_iam_token(api_key):
    try:
        url = "https://iam.cloud.ibm.com/identity/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        return response.json().get("access_token")
    except:
        return None

def get_available_models():
    token = get_iam_token(CREDENTIALS["api_key"])
    if not token:
        return []
    try:
        url = f"https://{CREDENTIALS['region']}.ml.cloud.ibm.com/ml/v1/foundation_models?version={VERSION}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        models_data = response.json()
        return [m["model_id"] for m in models_data.get("resources", [])]
    except:
        return []

# -------------------------------
# Prompt Builder
# -------------------------------
def create_enhanced_story_prompt(character_name, story_type, context, writing_style, length_category, mood, setting):
    story_structures = {
        "suspense": {"opening": "Create tension", "development": "Build suspense", "climax": "Reveal truth", "resolution": "Tie loose ends"},
        "adventure": {"opening": "Establish quest", "development": "Show challenges", "climax": "Face greatest danger", "resolution": "Achieve goal"},
        "fantasy": {"opening": "Introduce magical world", "development": "Explore magic", "climax": "Confront magical threat", "resolution": "Restore balance"},
        "drama": {"opening": "Show relationships", "development": "Deepen conflicts", "climax": "Emotional crisis", "resolution": "Resolve conflicts"},
        "mystery": {"opening": "Present mystery", "development": "Gather clues", "climax": "Reveal solution", "resolution": "Explain mystery"},
        "horror": {"opening": "Normal life", "development": "Escalate fear", "climax": "Face horror", "resolution": "Survive or succumb"}
    }
    structure = story_structures.get(story_type.lower(), story_structures["adventure"])
    return f"""You are a creative writer. Write a {story_type.lower()} story.

Character: {character_name}
Setting: {setting}
Mood: {mood}
Style: {writing_style}
Length: {length_category}

Context:
{context}

Follow this structure:
Opening: {structure['opening']}
Development: {structure['development']}
Climax: {structure['climax']}
Resolution: {structure['resolution']}

Make it vivid, engaging, and satisfying.
Story:"""

# -------------------------------
# Story Generation
# -------------------------------
def generate_story_with_watson(prompt, model_id, max_tokens, temperature, creativity_settings):
    token = get_iam_token(CREDENTIALS["api_key"])
    if not token:
        return "Error: Could not authenticate with IBM Watson."
    try:
        url = f"https://{CREDENTIALS['region']}.ml.cloud.ibm.com/ml/v1/text/generation?version={VERSION}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "model_id": model_id,
            "input": prompt,
            "project_id": CREDENTIALS["project_id"],
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "min_new_tokens": max(300, max_tokens // 3),
                "top_k": creativity_settings.get("top_k", 50),
                "top_p": creativity_settings.get("top_p", 0.9),
                "decoding_method": "sample",
                "repetition_penalty": creativity_settings.get("repetition_penalty", 1.3)
            }
        }
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        if "results" in data and data["results"]:
            return data["results"][0]["generated_text"].strip()
        return "Error: No story generated."
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# UI
# -------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Story Details")
    character_name = st.text_input("Main Character Name", value="Alex")
    story_context = st.text_area("Story Context", height=120)
    setting = st.selectbox("Setting/Location", ["Modern City", "Small Town", "Fantasy Realm"])
    mood = st.selectbox("Mood/Tone", ["Dark & Mysterious", "Light & Hopeful", "Intense & Thrilling"])

with st.sidebar:
    selected_model_name = st.selectbox("AI Model", list(MODEL_OPTIONS.keys()))
    model_id = MODEL_OPTIONS[selected_model_name]
    story_type = st.selectbox("Genre", ["Suspense", "Adventure", "Fantasy", "Drama", "Mystery", "Horror"])
    writing_style = st.selectbox("Writing Style", ["Narrative", "Descriptive", "Dialogue-Heavy"])
    length_category = st.selectbox("Story Length", ["Short (300-500 words)", "Medium (500-800 words)", "Long (800-1200 words)"])
    length_mapping = {"Short (300-500 words)": 400, "Medium (500-800 words)": 650, "Long (800-1200 words)": 1000}
    max_tokens = length_mapping[length_category]
    temperature = st.slider("Creativity Level", 0.1, 1.5, 0.8, 0.1)
    top_k = st.slider("Vocabulary Diversity", 10, 100, 50, 5)
    top_p = st.slider("Focus Level", 0.1, 1.0, 0.9, 0.05)
    repetition_penalty = st.slider("Repetition Control", 1.0, 2.0, 1.3, 0.1)
    creativity_settings = {"top_k": top_k, "top_p": top_p, "repetition_penalty": repetition_penalty}

# -------------------------------
# Generate Button
# -------------------------------
if st.button("🚀 Generate Story"):
    if CREDENTIALS["api_key"] == "your-api-key":
        st.error("Please configure your IBM Watson API credentials.")
    else:
        available_models = get_available_models()
        if model_id not in available_models:
            st.error(f"❌ Model '{selected_model_name}' is not available in IBM.\n"
                     f"Available models: {', '.join(available_models) if available_models else 'None'}")
        else:
            prompt = create_enhanced_story_prompt(character_name, story_type, story_context, writing_style, length_category, mood, setting)
            story = generate_story_with_watson(prompt, model_id, max_tokens, temperature, creativity_settings)
            if not story.startswith("Error"):
                st.markdown("### 📖 Your Generated Story")
                st.markdown(f"<div class='story-container'><div class='story-text'>{story}</div></div>", unsafe_allow_html=True)
            else:
                st.error(story)
