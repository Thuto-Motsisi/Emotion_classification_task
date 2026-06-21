# import streamlit as st
# import pandas as pd
# from openpyxl import load_workbook

# df = pd.read_excel("emotional_sentences.xlsx", sheet_name='emotion_sentences')
# st.title("Emotion Labeling")
# # st.write(df)

# # Pick 10 unlabelled sentences at the start
# if "sentences" not in st.session_state:
#     unlabelled = df[df["Emotion Label"].isna()].head(10)
#     st.session_state.sentences = unlabelled
#     st.session_state.current = 0

# sentences = st.session_state.sentences
# idx = st.session_state.current
# total = len(sentences)
# remaining = total - idx - 1

# # Get the current sentence
# row = sentences.iloc[idx]
# sentence = row["Sentence"]
# excel_row = row.name + 2  # +2 because Excel rows start at 1 and row 1 is header

# st.write(sentence)

# col1, col2 = st.columns(2)

# with col1:
#     left_label = st.radio("What emotion is this?", ["Joy", "Sadness", "Anger", "Fear"], index=None)

# with col2:
#     right_label = st.radio("", ["Disgust", "Surprise", "Neutral"], index=None)

# label = left_label or right_label

# confidence = st.slider("Confidence level", min_value=0.0, max_value=1.0, step=0.05)

# if label:
#     st.write(f"You picked **{label}** with confidence **{confidence}**")


# if st.button("Save Label"):
#     wb = load_workbook("emotional_sentences.xlsx")
#     ws = wb["emotion_sentences"]
#     ws["C2"] = label
#     ws["D2"] = confidence
#     wb.save("emotional_sentences.xlsx")
#     st.success("Saved!")

# if st.button("Save & Next"):
#     wb = load_workbook("emotional_sentences.xlsx")
#     ws = wb["emotion_sentences"]
#     ws.cell(row=excel_row, column=3, value=label)
#     ws.cell(row=excel_row, column=4, value=confidence)
#     wb.save("emotional_sentences.xlsx")

#     if idx + 1 < total:
#         st.session_state.current += 1
#         st.rerun()
#     else:
#         st.success("All 10 sentences labelled!")

# st.write(f"{remaining} more sentences to go")

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
            st.success(f"Your new USER_ID is : **{new_id}** - Please make sure to save this for future use. ")
    st.stop()
    
#Show User ID 
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
            👤 {st.session_state.annotator_id}
        </div>
        """,
        unsafe_allow_html=True,
    )

# Pick 10 unlabelled sentences at the start
if "sentences" not in st.session_state:
    data = supabase.table("sentences").select("*").limit(10).execute()
    df = pd.DataFrame(data.data)
    st.session_state.sentences = df
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


# if st.button("Save Label"):
#     wb = load_workbook("emotional_sentences.xlsx")
#     ws = wb["emotion_sentences"]
#     ws["C2"] = label
#     ws["D2"] = confidence
#     wb.save("emotional_sentences.xlsx")
#     st.success("Saved!")

if st.button("Save & Next"):
    if not label:
        st.warning("Please select an emotion before continuing!")
    elif confidence == 0.0:
        st.warning("Please set a confidence level before continuing!")
    else:
        if st.session_state.get("is_new_annotator") :
            supabase.table("annotators").insert({"annotator_id" : st.session_state.annotator_id}).execute()
            st.session_state.is_new_annotator = False

        sentence_id = int(df.iloc[idx]["sentence_id"])
        supabase.table("annotations").insert({
            "annotator_id" : st.session_state.annotator_id,
            "sentence_id" : sentence_id,
            "emotion_label" : label,
            "confidence_score" : confidence
        }).execute()

        if idx + 1 < total:
            st.session_state.current += 1
            st.rerun()
        else:
            st.success("All Sentences labelled!")

st.write(f"{remaining} more sentences to go")





