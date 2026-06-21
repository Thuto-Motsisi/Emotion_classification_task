import streamlit as st
import pandas as pd
import random
from supabase import create_client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url,key)

def generate_unique_id(supabase):
    animals = ["CAT", "DOG", "OWL", "FOX", "RAM", "HEN", "COW"]
    while True:
        animal = random.choice(animals)
        number = random.randint(1,999)
        new_id = f"ANN-{animal}-{number:03d}"

        found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", new_id).execute()
        found_in_annotations = supabase.table("annotations").select("annotator_id").eq("annotator_id", new_id).execute()

        if len(found_in_annotators.data) == 0 and len(found_in_annotations.data)==0:
            return new_id

#Log in Page 
if "annotator_id" not in st.session_state:
    st.title("Welcome!")
    st.write("Please enter your user ID or get a new one")
    user_input = st.text_input("Enter your user ID here", placeholder="eg. ANN-RAT-984")

    col1, col2 = st.columns(2)

    with col1 :
        if st.button("Log In") :
            if user_input:
                existing = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_input).execute()
                if len(existing.data) == 0:
                    st.warning("ID not found. Please make sure you entered the correct user ID")
                else: 
                    st.session_state.annotator_id = user_input
                    st.rerun()
            else :
                st.warning("Please Enter your user ID first")
    
    with col2 :
        if st.button("I dont have a user ID"):
            new_id = generate_unique_id(supabase)
            st.session_state.annotator_id = new_id
            st.session_state.is_new_annotator = True
            st.success(f"Your new USER_ID is : **{new_id}**. Please make sure you save this for future use. ")
    st.stop()

#Initializng counter for labeled sentences and skipped sentences.
if "labeled_count" not in st.session_state:
    st.session_state.labeled_count = 0

if "skipped_count" not in st.session_state:
    st.session_state.skipped_count = 0

#Show User ID at top right corner of every page 
col_1, col_2 = st.columns([8, 2])

with col_2:
    st.markdown(
        f"""
        <div style="
            background:#f0f2f6;
            padding:6px 12px;
            border-radius:8px;
            font-size:14px;
            font-weight:600;
            text-align:center;
            box-shadow:0 2px 6px rgba(0,0,0,0.1);
        ">
             {st.session_state.annotator_id}
        </div>
        """,
        unsafe_allow_html=True,
    )
    
#user selects how many sentences they will annotate    
if "num_sentences" not in st.session_state:
    st.title("How many sentences do you want to annotate?")
    choice = st.selectbox(
        "Select number of sentences",
        [15, 25, 50, 75, 100]
    )
    if st.button("Start Labeling"):
        st.session_state.num_sentences = choice
        st.rerun()
    st.stop()

# Load Sentences from database
if "sentences" not in st.session_state:
    annotator_id = st.session_state.annotator_id
    limit = st.session_state.num_sentences

    # Get all sentences in order
    all_sentences = (supabase.table("sentences").select("*").order("sentence_id").execute().data)
    eligible = []
    for s in all_sentences:
        sid = s["sentence_id"]

        # Count existing annotations for this sentence
        count = (supabase.table("annotations").select("sentence_id", count="exact").eq("sentence_id", sid).execute().count)
        if count >= 3:
            continue

        # Check if this user already annotated it
        already = (supabase.table("annotations").select("sentence_id").eq("sentence_id", sid).eq("annotator_id", annotator_id).execute())
        if not already.data:
            eligible.append(s)
        if len(eligible) == limit:
            break

    st.session_state.sentences = pd.DataFrame(eligible)
    st.session_state.current = 0


df = st.session_state.sentences
idx = st.session_state.current
total = len(df)
remaining = total - idx - 1
sentence = df.iloc[idx]["sentence"]

st.write(sentence)

col1, col2 = st.columns(2)

with col1:
    left_label = st.radio("What emotion is this?", ["Joy", "Sadness", "Anger", "Fear"], index=None, key = f"left_{idx}")

with col2:
    right_label = st.radio("", ["Disgust", "Surprise", "Neutral"], index=None, key = f"right_{idx}")

label = left_label or right_label

confidence = st.slider("Confidence level", min_value=0.0, max_value=1.0, step=0.05, key = f"conf_{idx}")

if label:
    st.write(f"You picked **{label}** with confidence **{confidence}**")



col_next, col_skip = st.columns([4, 1])

with col_next:
    if st.button("Save & Next"):
        if not label:
            st.warning("Please select an emotion.")
        elif confidence == 0.0:
            st.warning("Please set a confidence level.")
        else:
            if st.session_state.get("is_new_annotator"):
                supabase.table("annotators").insert({
                    "annotator_id": st.session_state.annotator_id
                }).execute()
                st.session_state.is_new_annotator = False

            supabase.table("annotations").insert({
                "annotator_id": st.session_state.annotator_id,
                "sentence_id": int(df.iloc[idx]["sentence_id"]),
                "emotion_label": label,
                "confidence_score": confidence
            }).execute()
            st.session_state.labeled_count += 1
            if idx + 1 < total:
                st.session_state.current += 1
                st.rerun()
            else:
                
            st.balloons()
            st.success("✅ You have completed all sentences!")

            st.subheader("Review Your Annotations")

            result = (supabase.table("annotations").select("*").eq("annotator_id", st.session_state.annotator_id).order("created_at", desc=False).execute())

            df_review = pd.DataFrame(result.data)
        
            if not df_review.empty:
                st.dataframe(df_review[["sentence_id", "emotion_label", "confidence_score"]],use_container_width=True)
        
            if st.button("🔁 Start Correcting Mistakes"):
                st.session_state.current = 0
                st.rerun()    

with col_skip:
    if st.button("Skip"):
        if idx + 1 < total:
            st.session_state.skipped_count += 1
            st.session_state.current += 1
            st.rerun()
        else:
            st.success("Thank you for labeling all the sentences!")



labeled = st.session_state.labeled_count
skipped = st.session_state.skipped_count
total = st.session_state.num_sentences
remaining = total - labeled - skipped


st.write(f"You have labeled {labeled}/{total} sentence")
st.write(f"{skipped} skipped sentences")
st.write(f"{remaining} more sentences to go")





