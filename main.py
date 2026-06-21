# import streamlit as st
# import pandas as pd
# import random
# from supabase import create_client

# url = st.secrets["SUPABASE_URL"]
# key = st.secrets["SUPABASE_KEY"]
# supabase = create_client(url,key)

# def generate_unique_id(supabase):
#     animals = ["CAT", "DOG", "OWL", "FOX", "RAM", "HEN", "COW"]
#     while True:
#         animal = random.choice(animals)
#         number = random.randint(1,999)
#         new_id = f"ANN-{animal}-{number:03d}"

#         found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", new_id).execute()
#         found_in_annotations = supabase.table("annotations").select("annotator_id").eq("annotator_id", new_id).execute()

#         if len(found_in_annotators.data) == 0 and len(found_in_annotations.data)==0:
#             return new_id

# #Log in Page 
# if "annotator_id" not in st.session_state:
#     st.title("Welcome!")
#     st.write("Please enter your user ID or get a new one")
#     user_input = st.text_input("Enter your user ID here", placeholder="eg. ANN-RAT-984")

#     col1, col2 = st.columns(2)

#     with col1 :
#         if st.button("Log In") :
#             if user_input:
#                 existing = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_input).execute()
#                 if len(existing.data) == 0:
#                     st.warning("ID not found. Please make sure you entered the correct user ID")
#                 else: 
#                     st.session_state.annotator_id = user_input
#                     st.rerun()
#             else :
#                 st.warning("Please Enter your user ID first")
    
#     with col2 :
#         if st.button("I dont have a user ID"):
#             new_id = generate_unique_id(supabase)
#             st.session_state.annotator_id = new_id
#             st.session_state.is_new_annotator = True
#             st.success(f"Your new USER_ID is : **{new_id}**. Please make sure you save this for future use. ")
#     st.stop()

# #Initializng counter for labeled sentences and skipped sentences.
# if "labeled_count" not in st.session_state:
#     st.session_state.labeled_count = 0

# if "skipped_count" not in st.session_state:
#     st.session_state.skipped_count = 0

# #Show User ID at top right corner of every page 
# col_1, col_2 = st.columns([8, 2])

# with col_2:
#     st.markdown(
#         f"""
#         <div style="
#             background:#f0f2f6;
#             padding:6px 12px;
#             border-radius:8px;
#             font-size:14px;
#             font-weight:600;
#             text-align:center;
#             box-shadow:0 2px 6px rgba(0,0,0,0.1);
#         ">
#              {st.session_state.annotator_id}
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )
    
# #user selects how many sentences they will annotate    
# if "num_sentences" not in st.session_state:
#     st.title("How many sentences do you want to annotate?")
#     choice = st.selectbox(
#         "Select number of sentences",
#         [15, 25, 50, 75, 100]
#     )
#     if st.button("Start Labeling"):
#         st.session_state.num_sentences = choice
#         st.rerun()
#     st.stop()

# # Load Sentences from database
# if "sentences" not in st.session_state:
#     annotator_id = st.session_state.annotator_id
#     limit = st.session_state.num_sentences

#     # Get all sentences in order
#     all_sentences = (supabase.table("sentences").select("*").order("sentence_id").execute().data)
#     eligible = []
#     for s in all_sentences:
#         sid = s["sentence_id"]

#         # Count existing annotations for this sentence
#         count = (supabase.table("annotations").select("sentence_id", count="exact").eq("sentence_id", sid).execute().count)
#         if count >= 3:
#             continue

#         # Check if this user already annotated it
#         already = (supabase.table("annotations").select("sentence_id").eq("sentence_id", sid).eq("annotator_id", annotator_id).execute())
#         if not already.data:
#             eligible.append(s)
#         if len(eligible) == limit:
#             break

#     st.session_state.sentences = pd.DataFrame(eligible)
#     st.session_state.current = 0


# df = st.session_state.sentences
# idx = st.session_state.current
# total = len(df)
# remaining = total - idx - 1
# sentence = df.iloc[idx]["sentence"]

# st.write(sentence)

# col1, col2 = st.columns(2)

# with col1:
#     left_label = st.radio("What emotion is this?", ["Joy", "Sadness", "Anger", "Fear"], index=None, key = f"left_{idx}")

# with col2:
#     right_label = st.radio("", ["Disgust", "Surprise", "Neutral"], index=None, key = f"right_{idx}")

# label = left_label or right_label

# confidence = st.slider("Confidence level", min_value=0.0, max_value=1.0, step=0.05, key = f"conf_{idx}")

# if label:
#     st.write(f"You picked **{label}** with confidence **{confidence}**")



# col_next, col_skip = st.columns([4, 1])

# with col_next:
#     if st.button("Save & Next"):
#         if not label:
#             st.warning("Please select an emotion.")
#         elif confidence == 0.0:
#             st.warning("Please set a confidence level.")
#         else:
#             if st.session_state.get("is_new_annotator"):
#                 supabase.table("annotators").insert({
#                     "annotator_id": st.session_state.annotator_id
#                 }).execute()
#                 st.session_state.is_new_annotator = False

#             supabase.table("annotations").insert({
#                 "annotator_id": st.session_state.annotator_id,
#                 "sentence_id": int(df.iloc[idx]["sentence_id"]),
#                 "emotion_label": label,
#                 "confidence_score": confidence
#             }).execute()
#             st.session_state.labeled_count += 1
#             if idx + 1 < total:
#                 st.session_state.current += 1
#                 st.rerun()
#             else:
#                 st.balloons()
#                 st.success("✅ You have completed all sentences!")
#                 st.subheader("Review Your Annotations")
#                 result = (supabase.table("annotations").select("*").eq("annotator_id", st.session_state.annotator_id).order("created_at", desc=False).execute())
#                 df_review = pd.DataFrame(result.data)
#                 if not df_review.empty:
#                     st.dataframe(df_review[["sentence_id", "emotion_label", "confidence_score"]],use_container_width=True)
#                 if st.button("🔁 Start Correcting Mistakes"):
#                     st.session_state.current = 0
#                     st.rerun()    

# with col_skip:
#     if st.button("Skip"):
#         if idx + 1 < total:
#             st.session_state.skipped_count += 1
#             st.session_state.current += 1
#             st.rerun()
#         else:
#             st.success("Thank you for labeling all the sentences!")



# labeled = st.session_state.labeled_count
# skipped = st.session_state.skipped_count
# total = st.session_state.num_sentences
# remaining = total - labeled - skipped


# st.write(f"You have labeled {labeled}/{total} sentence")
# st.write(f"{skipped} skipped sentences")
# st.write(f"{remaining} more sentences to go")




import streamlit as st
import pandas as pd
import random
from supabase import create_client
import time

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

def delete_annotation(annotation_id):
    """Delete an existing annotation"""
    try:
        supabase.table("annotations").delete().eq("id", annotation_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting annotation: {str(e)}")
        return False

def save_annotation(annotator_id, sentence_id, emotion_label, confidence_score):
    """Save a new annotation"""
    try:
        supabase.table("annotations").insert({
            "annotator_id": annotator_id,
            "sentence_id": int(sentence_id),
            "emotion_label": emotion_label,
            "confidence_score": confidence_score
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error saving annotation: {str(e)}")
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
        "annotated_sentences": set(),  # Track which sentences have been annotated
        "existing_annotations": {}  # Cache for existing annotations
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Login Page
if st.session_state.annotator_id is None:
    st.title("Welcome to Emotion Annotation Task!")
    st.write("Please enter your user ID or get a new one")
    
    user_input = st.text_input("Enter your user ID here", placeholder="e.g., ANN-CAT-123")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Log In", use_container_width=True):
            if user_input:
                try:
                    existing = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_input).execute()
                    if len(existing.data) == 0:
                        st.error("❌ ID not found. Please make sure you entered the correct user ID")
                    else:
                        st.session_state.annotator_id = user_input
                        st.rerun()
                except Exception as e:
                    st.error(f"Login error: {str(e)}")
            else:
                st.warning("⚠️ Please enter your user ID first")
    
    with col2:
        if st.button("I don't have a user ID", use_container_width=True):
            try:
                new_id = generate_unique_id(supabase)
                st.session_state.annotator_id = new_id
                st.session_state.is_new_annotator = True
                st.success(f"✅ Your new USER_ID is: **{new_id}**. Please save this for future use.")
                st.rerun()
            except Exception as e:
                st.error(f"Error generating ID: {str(e)}")
    
    st.stop()

# Display User ID
st.markdown(
    f"""
    <div style="position: fixed; top: 10px; right: 20px; z-index: 999; 
                background: #f0f2f6; padding: 8px 16px; border-radius: 20px; 
                font-size: 14px; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        👤 {st.session_state.annotator_id}
    </div>
    """,
    unsafe_allow_html=True,
)

# Select number of sentences
if st.session_state.num_sentences is None:
    st.title("How many sentences do you want to annotate?")
    
    choice = st.selectbox(
        "Select number of sentences",
        [15, 25, 50, 75, 100],
        index=0
    )
    
    if st.button("Start Labeling", use_container_width=True):
        st.session_state.num_sentences = choice
        st.rerun()
    st.stop()

# Load sentences from database
if st.session_state.sentences is None:
    with st.spinner("Loading sentences..."):
        annotator_id = st.session_state.annotator_id
        limit = st.session_state.num_sentences
        
        try:
            # Get all sentences in order
            all_sentences = supabase.table("sentences").select("*").order("sentence_id").execute().data
            
            if not all_sentences:
                st.error("No sentences found in the database.")
                st.stop()
            
            eligible = []
            for s in all_sentences:
                sid = s["sentence_id"]
                
                # Count existing annotations for this sentence
                count_response = supabase.table("annotations").select("*", count="exact").eq("sentence_id", sid).execute()
                count = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
                
                if count >= 3:
                    continue
                
                # Check if this user already annotated it
                already = supabase.table("annotations").select("sentence_id").eq("sentence_id", sid).eq("annotator_id", annotator_id).execute()
                if not already.data:
                    eligible.append(s)
                    if len(eligible) == limit:
                        break
            
            if not eligible:
                st.warning("No eligible sentences found. All sentences have been annotated 3 times or by you already.")
                st.stop()
            
            st.session_state.sentences = pd.DataFrame(eligible)
            st.session_state.current = 0
            st.session_state.completed = False
            
            # Pre-load existing annotations for all sentences
            for idx, row in enumerate(st.session_state.sentences.iterrows()):
                sentence_id = row[1]["sentence_id"]
                existing = load_existing_annotation(annotator_id, sentence_id)
                if existing:
                    st.session_state.existing_annotations[sentence_id] = existing
                    st.session_state.annotated_sentences.add(sentence_id)
            
        except Exception as e:
            st.error(f"Error loading sentences: {str(e)}")
            st.stop()

# Main annotation interface
df = st.session_state.sentences
idx = st.session_state.current
total = len(df)

if total == 0:
    st.warning("No sentences to annotate.")
    st.stop()

# Check if all sentences are completed
if idx >= total:
    st.session_state.completed = True

if st.session_state.completed:
    st.balloons()
    st.success("🎉 You have completed all sentences!")
    
    st.subheader("📊 Review Your Annotations")
    
    try:
        # Try ordering by a column that definitely exists
        result = supabase.table("annotations").select("*").eq("annotator_id", st.session_state.annotator_id).execute()
        df_review = pd.DataFrame(result.data)
        
        if not df_review.empty:
            # Display columns that exist
            display_cols = [col for col in ["sentence_id", "emotion_label", "confidence_score", "created_at"] if col in df_review.columns]
            st.dataframe(df_review[display_cols], use_container_width=True)
        
        # Option to start over or go back
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Start Over", use_container_width=True):
                st.session_state.sentences = None
                st.session_state.num_sentences = None
                st.session_state.labeled_count = 0
                st.session_state.skipped_count = 0
                st.session_state.current = 0
                st.session_state.completed = False
                st.session_state.annotated_sentences = set()
                st.session_state.existing_annotations = {}
                st.rerun()
        
        with col2:
            if st.button("📊 View Statistics", use_container_width=True):
                # Show statistics
                if not df_review.empty:
                    st.subheader("📈 Annotation Statistics")
                    emotion_counts = df_review["emotion_label"].value_counts()
                    st.bar_chart(emotion_counts)
                    
                    avg_confidence = df_review["confidence_score"].mean()
                    st.metric("Average Confidence", f"{avg_confidence:.2f}")
        
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

# Display current sentence
st.markdown(f"### 📝 Sentence {idx + 1} of {total}")
if existing_annotation:
    st.info(f"🔄 You already annotated this sentence. You can update it below.")
st.markdown(f"> {sentence}")

# Emotion selection - set default values if existing annotation exists
col1, col2 = st.columns(2)

# Determine default emotion
default_emotion = existing_annotation.get("emotion_label") if existing_annotation else None

with col1:
    left_label = st.radio(
        "Select emotion:",
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

# Confidence slider - set default if existing annotation exists
default_confidence = existing_annotation.get("confidence_score") if existing_annotation else 0.5
confidence = st.slider(
    "Confidence level (0 = not confident, 1 = very confident)",
    min_value=0.0,
    max_value=1.0,
    step=0.05,
    value=default_confidence,
    key=f"conf_{idx}"
)

# Display selected emotion
if label:
    st.info(f"Selected: **{label}** with confidence **{confidence:.2f}**")

# Progress indicators
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Labeled", st.session_state.labeled_count)
with col2:
    st.metric("Skipped", st.session_state.skipped_count)
with col3:
    st.metric("Remaining", total - idx - 1)

# Action buttons - Three columns for Previous, Save, Skip
col_prev, col_next, col_skip = st.columns([2, 4, 2])

with col_prev:
    if st.button("⬅️ Previous", use_container_width=True, disabled=(idx == 0)):
        if idx > 0:
            st.session_state.current -= 1
            st.rerun()

with col_next:
    if st.button("✅ Save & Next", use_container_width=True):
        if not label:
            st.warning("⚠️ Please select an emotion.")
        elif confidence == 0.0:
            st.warning("⚠️ Please set a confidence level greater than 0.")
        else:
            try:
                # Register new annotator if needed
                if st.session_state.is_new_annotator:
                    supabase.table("annotators").insert({
                        "annotator_id": st.session_state.annotator_id
                    }).execute()
                    st.session_state.is_new_annotator = False
                
                # Check if annotation already exists
                if existing_annotation:
                    # Delete existing annotation
                    annotation_id = existing_annotation.get("id")
                    if annotation_id and delete_annotation(annotation_id):
                        # Remove from session state
                        if sentence_id in st.session_state.existing_annotations:
                            del st.session_state.existing_annotations[sentence_id]
                        if sentence_id in st.session_state.annotated_sentences:
                            st.session_state.annotated_sentences.remove(sentence_id)
                        st.session_state.labeled_count -= 1
                
                # Save new annotation
                if save_annotation(st.session_state.annotator_id, sentence_id, label, confidence):
                    # Update session state
                    st.session_state.existing_annotations[sentence_id] = {
                        "id": None,  # We don't have the ID yet, but we'll fetch it if needed
                        "sentence_id": sentence_id,
                        "emotion_label": label,
                        "confidence_score": confidence
                    }
                    st.session_state.annotated_sentences.add(sentence_id)
                    st.session_state.labeled_count += 1
                    
                    # Move to next sentence
                    if idx + 1 < total:
                        st.session_state.current += 1
                        st.rerun()
                    else:
                        st.session_state.completed = True
                        st.rerun()
                    
            except Exception as e:
                st.error(f"Error saving annotation: {str(e)}")

with col_skip:
    if st.button("⏭️ Skip", use_container_width=True):
        # If there's an existing annotation, keep it but move on
        if idx + 1 < total:
            st.session_state.skipped_count += 1
            st.session_state.current += 1
            st.rerun()
        else:
            st.session_state.completed = True
            st.rerun()

# Progress bar
progress = (idx + 1) / total if total > 0 else 0
st.progress(progress)

# Navigation info
st.caption(f"📍 You are on sentence {idx + 1} of {total}")
if existing_annotation:
    st.caption("🔄 This sentence has been annotated. You can update your annotation.")

