import streamlit as st
import pandas as pd
import random
from supabase import create_client
import time
import json
from datetime import datetime

# Initialize Supabase client
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def generate_unique_id(supabase):
    animals = ["CAT", "DOG", "OWL", "FOX", "RAM", "HEN", "COW"]
    while True:
        animal = random.choice(animals)
        number = random.randint(1, 999)
        new_id = f"ANN-{animal}-{number:03d}"

        found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", new_id).execute()
        found_in_annotations = supabase.table("annotations").select("annotator_id").eq("annotator_id", new_id).execute()

        if len(found_in_annotators.data) == 0 and len(found_in_annotations.data) == 0:
            return new_id

def load_existing_annotation(annotator_id, sentence_id):
    """Load existing annotation for a given sentence and annotator"""
    try:
        result = supabase.table("annotations").select("*").eq("annotator_id", annotator_id).eq("sentence_id", sentence_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Error loading annotation: {str(e)}")
        return None

def update_annotation(annotation_id, emotion_label, confidence_score):
    """Update an existing annotation"""
    try:
        supabase.table("annotations").update({
            "emotion_label": emotion_label,
            "confidence_score": confidence_score
        }).eq("id", annotation_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating annotation: {str(e)}")
        return False

def save_annotation(annotator_id, sentence_id, emotion_label, confidence_score):
    """Save a new annotation"""
    try:
        result = supabase.table("annotations").insert({
            "annotator_id": annotator_id,
            "sentence_id": int(sentence_id),
            "emotion_label": emotion_label,
            "confidence_score": confidence_score
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error saving annotation: {str(e)}")
        return None

# Function to save state to URL query parameters
def save_state_to_url():
    """Save current session state to URL query parameters"""
    try:
        state = {
            "annotator_id": st.session_state.get("annotator_id", ""),
            "current": st.session_state.get("current", 0),
            "page": st.session_state.get("page", "login"),
            "num_sentences": st.session_state.get("num_sentences", ""),
            "labeled_count": st.session_state.get("labeled_count", 0),
            "skipped_count": st.session_state.get("skipped_count", 0),
            "consent_given": st.session_state.get("consent_given", False),
            "completed": st.session_state.get("completed", False),
        }
        
        state_json = json.dumps(state)
        st.query_params["app_state"] = state_json
        return True
    except Exception as e:
        return False

# Function to load state from URL query parameters
def load_state_from_url():
    """Load session state from URL query parameters"""
    try:
        if "app_state" in st.query_params:
            state_json = st.query_params["app_state"]
            state = json.loads(state_json)
            
            for key, value in state.items():
                st.session_state[key] = value
            return True
        return False
    except Exception as e:
        return False

# Initialize session state variables
def init_session_state():
    defaults = {
        "annotator_id": None,
        "is_new_annotator": False,
        "labeled_count": 0,
        "skipped_count": 0,
        "num_sentences": None,
        "sentences": None,
        "current": 0,
        "completed": False,
        "annotated_sentences": set(),
        "existing_annotations": {},
        "consent_given": False,
        "page": "login",
        "state_loaded": False,
        "skipped_sentences": set(),
        "show_skip_confirmation": False,
        "show_save_confirmation": False,
        "pending_action": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Try to load state from URL on first run
if not st.session_state.state_loaded:
    state_loaded = load_state_from_url()
    if state_loaded and st.session_state.annotator_id:
        st.success(f"✅ Session restored! Welcome back!")
    st.session_state.state_loaded = True

# Function to display user ID at top right
def display_user_id():
    """Display the user ID at the top right corner"""
    if st.session_state.annotator_id:
        st.markdown(
            f"""
            <div style="
                position: fixed;
                top: 10px;
                right: 20px;
                z-index: 999;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 8px 20px;
                border-radius: 25px;
                font-size: 15px;
                font-weight: 600;
                color: white;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(5px);
                display: inline-block;
                letter-spacing: 0.5px;
            ">
                👤 {st.session_state.annotator_id}
            </div>
            """,
            unsafe_allow_html=True,
        )

# Display user ID at the top right of every page
display_user_id()

# ==================== LOGIN PAGE ====================
if st.session_state.annotator_id is None:
    st.title("👋 Welcome to Emotion Annotation Task!")
    st.write("Please enter your user ID or get a new one")
    
    user_input = st.text_input("Enter your user ID here", placeholder="e.g., ANN-CAT-123")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔑 Log In", use_container_width=True):
            if user_input:
                try:
                    existing = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_input).execute()
                    if len(existing.data) == 0:
                        st.error("❌ ID not found. Please make sure you entered the correct user ID")
                    else:
                        st.session_state.annotator_id = user_input
                        st.session_state.page = "consent"
                        save_state_to_url()
                        st.rerun()
                except Exception as e:
                    st.error(f"Login error: {str(e)}")
            else:
                st.warning("⚠️ Please enter your user ID first")
    
    with col2:
        if st.button("🆕 I don't have a user ID", use_container_width=True):
            try:
                new_id = generate_unique_id(supabase)
                st.session_state.annotator_id = new_id
                st.session_state.is_new_annotator = True
                st.session_state.page = "consent"
                st.success(f"✅ Your new USER_ID is: **{new_id}**. Please save this for future use.")
                save_state_to_url()
                st.rerun()
            except Exception as e:
                st.error(f"Error generating ID: {str(e)}")
    
    st.stop()

# ==================== CONSENT PAGE ====================
if st.session_state.page == "consent":
    st.title("📋 Informed Consent Form")
    
    st.markdown("---")
    
    st.subheader("Study Information")
    st.write("""
    **Title:** Emotion Annotation Task
    
    **Purpose:** You are being asked to participate in a research study to annotate sentences with emotion labels. 
    Your contributions will help improve emotion recognition systems.
    
    **Procedure:** You will be presented with sentences and asked to:
    - Select an emotion label (Joy, Sadness, Anger, Fear, Disgust, Surprise, or Neutral)
    - Rate your confidence in the label (0.0 to 1.0)
    - Complete approximately 15-100 sentences
    """)
    
    st.markdown("---")
    
    st.subheader("Consent Details")
    
    consent_items = [
        "I confirm that I have read and understand the information provided above.",
        "I understand that my participation is voluntary and I can withdraw at any time.",
        "I agree to the use of my annotations for research purposes.",
        "I understand that my data will be anonymized and stored securely.",
        "I confirm that I am 18 years or older.",
        "I agree to perform the annotation task to the best of my ability."
    ]
    
    all_checked = True
    for i, item in enumerate(consent_items):
        checked = st.checkbox(item, key=f"consent_{i}")
        if not checked:
            all_checked = False
    
    st.markdown("---")
    
    with st.expander("🔒 Data Privacy and Security"):
        st.write("""
        **How we protect your data:**
        - All annotations are stored securely in a database
        - Your user ID is randomly generated and does not contain personal information
        - Your data will only be used for research purposes
        - You can request to have your data removed at any time
        - No personally identifiable information is collected
        """)
    
    with st.expander("📧 Contact Information"):
        st.write("""
        If you have any questions or concerns about this study, please contact:
        
        **Researcher:** [Your Name]
        **Email:** [your.email@example.com]
        **Institution:** [Your Institution]
        """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ I Consent to Participate", use_container_width=True, disabled=not all_checked):
            st.session_state.consent_given = True
            st.session_state.page = "select_sentences"
            try:
                supabase.table("consent_logs").insert({
                    "annotator_id": st.session_state.annotator_id,
                    "consent_given": True,
                    "timestamp": datetime.now().isoformat()
                }).execute()
            except:
                pass
            save_state_to_url()
            st.rerun()
    
    if not all_checked:
        st.warning("⚠️ Please check all boxes above to give your consent.")
    
    st.stop()

# ==================== SELECT SENTENCES PAGE ====================
if st.session_state.page == "select_sentences":
    st.title("📊 How many sentences do you want to annotate?")
    
    st.info("ℹ️ You have already given consent. Now, choose how many sentences you would like to annotate.")
    
    choice = st.selectbox(
        "Select number of sentences",
        [15, 25, 50, 75, 100],
        index=0
    )
    
    if st.button("🚀 Start Labeling", use_container_width=True):
        st.session_state.num_sentences = choice
        st.session_state.page = "annotate"
        save_state_to_url()
        st.rerun()
    st.stop()

# ==================== LOAD SENTENCES ====================
if st.session_state.page == "annotate" and st.session_state.sentences is None:
    with st.spinner("Loading sentences..."):
        annotator_id = st.session_state.annotator_id
        limit = st.session_state.num_sentences
        
        try:
            all_sentences = supabase.table("sentences").select("*").order("sentence_id").execute().data
            
            if not all_sentences:
                st.error("No sentences found in the database.")
                st.stop()
            
            eligible = []
            for s in all_sentences:
                sid = s["sentence_id"]
                
                count_response = supabase.table("annotations").select("*", count="exact").eq("sentence_id", sid).execute()
                count = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
                
                if count >= 3:
                    continue
                
                already = supabase.table("annotations").select("sentence_id").eq("sentence_id", sid).eq("annotator_id", annotator_id).execute()
                if not already.data:
                    eligible.append(s)
                    if len(eligible) == limit:
                        break
            
            if not eligible:
                st.warning("No eligible sentences found. All sentences have been annotated 3 times or by you already.")
                st.stop()
            
            st.session_state.sentences = pd.DataFrame(eligible)
            st.session_state.completed = False
            
            # Reset tracking sets
            st.session_state.skipped_sentences = set()
            st.session_state.annotated_sentences = set()
            st.session_state.existing_annotations = {}
            
            # Pre-load existing annotations for all sentences
            for idx, row in enumerate(st.session_state.sentences.iterrows()):
                sentence_id = row[1]["sentence_id"]
                existing = load_existing_annotation(annotator_id, sentence_id)
                if existing:
                    st.session_state.existing_annotations[sentence_id] = existing
                    st.session_state.annotated_sentences.add(sentence_id)
                    st.session_state.labeled_count += 1
            
            save_state_to_url()
            
        except Exception as e:
            st.error(f"Error loading sentences: {str(e)}")
            st.stop()

# ==================== ANNOTATION PAGE ====================
if st.session_state.page == "annotate":
    df = st.session_state.sentences
    idx = st.session_state.current
    total = len(df)

    if total == 0:
        st.warning("No sentences to annotate.")
        st.stop()

    # Check if all sentences are completed (annotated or skipped)
    all_processed = all(
        df.iloc[i]["sentence_id"] in st.session_state.annotated_sentences or 
        df.iloc[i]["sentence_id"] in st.session_state.skipped_sentences 
        for i in range(total)
    )
    
    if all_processed and idx >= total:
        st.session_state.completed = True
        st.session_state.page = "complete"

    if st.session_state.page == "complete":
        st.balloons()
        st.title("🎉 Thank You for Your Participation!")
        
        st.markdown("""
        ### 🙏 We Appreciate Your Contribution!
        
        Your annotations will help advance emotion recognition research. 
        Your time and effort are greatly valued.
        """)
        
        st.subheader("📊 Your Annotation Summary")
        
        try:
            result = supabase.table("annotations").select("*").eq("annotator_id", st.session_state.annotator_id).execute()
            df_review = pd.DataFrame(result.data)
            
            if not df_review.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Annotations", len(df_review))
                with col2:
                    st.metric("Skipped", st.session_state.skipped_count)
                with col3:
                    avg_conf = df_review["confidence_score"].mean()
                    st.metric("Avg Confidence", f"{avg_conf:.2f}")
                
                st.subheader("📈 Emotion Distribution")
                emotion_counts = df_review["emotion_label"].value_counts()
                st.bar_chart(emotion_counts)
            
            st.info("💡 You can close this tab or start a new session if you'd like to continue annotating.")
            
            # Option to start over
            if st.button("🔄 Start New Annotation Session", use_container_width=True):
                st.session_state.sentences = None
                st.session_state.num_sentences = None
                st.session_state.labeled_count = 0
                st.session_state.skipped_count = 0
                st.session_state.current = 0
                st.session_state.completed = False
                st.session_state.annotated_sentences = set()
                st.session_state.existing_annotations = {}
                st.session_state.skipped_sentences = set()
                st.session_state.page = "select_sentences"
                save_state_to_url()
                st.rerun()
            
        except Exception as e:
            st.error(f"Error retrieving annotations: {str(e)}")
            st.info("Your annotations have been saved successfully!")
        
        st.stop()

    # Get current sentence data
    sentence_data = df.iloc[idx]
    sentence_id = int(sentence_data["sentence_id"])
    sentence = sentence_data["sentence"]

    # Check if this sentence has an existing annotation
    existing_annotation = st.session_state.existing_annotations.get(sentence_id)
    is_skipped = sentence_id in st.session_state.skipped_sentences
    is_annotated = sentence_id in st.session_state.annotated_sentences

    # ==================== MAIN CONTENT ====================
    st.markdown(f"### 📝 Sentence {idx + 1} of {total}")
    if existing_annotation:
        st.info(f"🔄 You already annotated this sentence with **{existing_annotation['emotion_label']}** (confidence: {existing_annotation['confidence_score']:.2f}). You can update it below.")
    elif is_skipped:
        st.warning(f"⏭️ You skipped this sentence previously.")
    
    # Make the sentence more visible with a styled box
    st.markdown(
        f"""
        <div style="
            background: #f8f9fa;
            padding: 25px;
            border-radius: 12px;
            border-left: 6px solid #667eea;
            font-size: 20px;
            font-weight: 500;
            margin: 15px 0 25px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            line-height: 1.6;
        ">
            {sentence}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Emotion selection
    st.subheader("🏷️ Select Emotion")
    col1, col2 = st.columns(2)

    default_emotion = existing_annotation.get("emotion_label") if existing_annotation else None

    with col1:
        left_label = st.radio(
            "",
            ["Joy", "Sadness", "Anger", "Fear"],
            index=["Joy", "Sadness", "Anger", "Fear"].index(default_emotion) if default_emotion in ["Joy", "Sadness", "Anger", "Fear"] else None,
            key=f"left_{idx}"
        )

    with col2:
        right_label = st.radio(
            "",
            ["Disgust", "Surprise", "Neutral"],
            index=["Disgust", "Surprise", "Neutral"].index(default_emotion) if default_emotion in ["Disgust", "Surprise", "Neutral"] else None,
            key=f"right_{idx}"
        )

    label = left_label or right_label

    # Confidence slider - starts at 0.0
    st.subheader("🎯 Confidence Level")
    default_confidence = existing_annotation.get("confidence_score") if existing_annotation else 0.0
    confidence = st.slider(
        "",
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        value=default_confidence,
        key=f"conf_{idx}"
    )

    if label:
        st.success(f"✅ Selected: **{label}** with confidence **{confidence:.2f}**")

    # ==================== COMPACT PROGRESS BAR ====================
    st.markdown("---")
    
    # Calculate remaining correctly - only count unprocessed sentences
    remaining = sum(1 for i in range(total) 
                   if df.iloc[i]["sentence_id"] not in st.session_state.annotated_sentences 
                   and df.iloc[i]["sentence_id"] not in st.session_state.skipped_sentences)
    
    progress = (total - remaining) / total if total > 0 else 0
    st.progress(progress, text=f"Progress: {int(progress * 100)}%")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ Labeled", st.session_state.labeled_count)
    with col2:
        st.metric("⏭️ Skipped", st.session_state.skipped_count)
    with col3:
        st.metric("📝 Remaining", remaining)
    with col4:
        st.metric("📊 Total", total)

    st.caption(f"📍 Sentence {idx + 1} of {total}")

    # ==================== ACTION BUTTONS ====================
    col_prev, col_next, col_skip = st.columns([2, 4, 2])

    with col_prev:
        if st.button("⬅️ Previous", use_container_width=True, disabled=(idx == 0)):
            if idx > 0:
                st.session_state.current -= 1
                save_state_to_url()
                st.rerun()

    with col_next:
        if st.button("💾 Save & Next", use_container_width=True, type="primary"):
            if not label:
                st.warning("⚠️ Please select an emotion.")
            elif confidence == 0.0:
                # Show confirmation for confidence = 0
                st.warning("⚠️ You've selected confidence level 0.0. Are you sure?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Yes, proceed", use_container_width=True):
                        # Proceed with saving
                        process_save = True
                        if process_save:
                            try:
                                if st.session_state.is_new_annotator:
                                    supabase.table("annotators").insert({
                                        "annotator_id": st.session_state.annotator_id
                                    }).execute()
                                    st.session_state.is_new_annotator = False
                                
                                if sentence_id in st.session_state.skipped_sentences:
                                    st.session_state.skipped_sentences.remove(sentence_id)
                                    st.session_state.skipped_count -= 1
                                
                                if existing_annotation and 'id' in existing_annotation:
                                    annotation_id = existing_annotation['id']
                                    if update_annotation(annotation_id, label, confidence):
                                        st.session_state.existing_annotations[sentence_id] = {
                                            **existing_annotation,
                                            "emotion_label": label,
                                            "confidence_score": confidence
                                        }
                                        st.success(f"✅ Annotation updated successfully!")
                                        
                                        if idx + 1 < total:
                                            st.session_state.current += 1
                                            save_state_to_url()
                                            st.rerun()
                                        else:
                                            st.session_state.completed = True
                                            st.session_state.page = "complete"
                                            save_state_to_url()
                                            st.rerun()
                                else:
                                    new_annotation = save_annotation(st.session_state.annotator_id, sentence_id, label, confidence)
                                    if new_annotation:
                                        st.session_state.existing_annotations[sentence_id] = new_annotation
                                        st.session_state.annotated_sentences.add(sentence_id)
                                        st.session_state.labeled_count += 1
                                        
                                        if idx + 1 < total:
                                            st.session_state.current += 1
                                            save_state_to_url()
                                            st.rerun()
                                        else:
                                            st.session_state.completed = True
                                            st.session_state.page = "complete"
                                            save_state_to_url()
                                            st.rerun()
                            except Exception as e:
                                st.error(f"Error saving annotation: {str(e)}")
                with col_no:
                    if st.button("❌ No, adjust", use_container_width=True):
                        st.rerun()
            else:
                # Normal save flow
                try:
                    if st.session_state.is_new_annotator:
                        supabase.table("annotators").insert({
                            "annotator_id": st.session_state.annotator_id
                        }).execute()
                        st.session_state.is_new_annotator = False
                    
                    if sentence_id in st.session_state.skipped_sentences:
                        st.session_state.skipped_sentences.remove(sentence_id)
                        st.session_state.skipped_count -= 1
                    
                    if existing_annotation and 'id' in existing_annotation:
                        annotation_id = existing_annotation['id']
                        if update_annotation(annotation_id, label, confidence):
                            st.session_state.existing_annotations[sentence_id] = {
                                **existing_annotation,
                                "emotion_label": label,
                                "confidence_score": confidence
                            }
                            st.success(f"✅ Annotation updated successfully!")
                            
                            if idx + 1 < total:
                                st.session_state.current += 1
                                save_state_to_url()
                                st.rerun()
                            else:
                                st.session_state.completed = True
                                st.session_state.page = "complete"
                                save_state_to_url()
                                st.rerun()
                    else:
                        new_annotation = save_annotation(st.session_state.annotator_id, sentence_id, label, confidence)
                        if new_annotation:
                            st.session_state.existing_annotations[sentence_id] = new_annotation
                            st.session_state.annotated_sentences.add(sentence_id)
                            st.session_state.labeled_count += 1
                            
                            if idx + 1 < total:
                                st.session_state.current += 1
                                save_state_to_url()
                                st.rerun()
                            else:
                                st.session_state.completed = True
                                st.session_state.page = "complete"
                                save_state_to_url()
                                st.rerun()
                except Exception as e:
                    st.error(f"Error saving annotation: {str(e)}")

    with col_skip:
        if st.button("⏭️ Skip", use_container_width=True):
            # Show confirmation dialog for skip
            st.warning("⚠️ Are you sure you want to skip this sentence?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Yes, skip", use_container_width=True):
                    # Only increment skip counter if not already annotated or skipped
                    if sentence_id not in st.session_state.annotated_sentences and sentence_id not in st.session_state.skipped_sentences:
                        st.session_state.skipped_count += 1
                        st.session_state.skipped_sentences.add(sentence_id)
                    elif sentence_id in st.session_state.annotated_sentences:
                        st.warning("⚠️ This sentence was already annotated. You can't skip it now.")
                        st.stop()
                    
                    if idx + 1 < total:
                        st.session_state.current += 1
                        save_state_to_url()
                        st.rerun()
                    else:
                        st.session_state.completed = True
                        st.session_state.page = "complete"
                        save_state_to_url()
                        st.rerun()
            with col_no:
                if st.button("❌ No, cancel", use_container_width=True):
                    st.rerun()

    st.caption(f"👤 Logged in as: **{st.session_state.annotator_id}**")
