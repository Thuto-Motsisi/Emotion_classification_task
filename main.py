import streamlit as st
from supabase import create_client
import random

#Initialize supabase client
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url,key)


def id_exists(supabase, user_id) :
  """checks if the id exists in the stored data"""
  found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_id).execute()
  found_in_annotations = supabase.table("annotations").select("annotator_id").eq("annotator_id", user_id).execute()
  if not (len(found_in_annotators.data) == 0 and len(found_in_annotations.data) == 0):
    return True
  else:
    return False


def generate_unique_id(supabase):
    """ Generates unique id for paticipants. conditions: id is not found in the annotations table and the annotators table """
    
    animals = ["CAT", "DOG", "OWL", "FOX", "RAM", "HEN", "COW"]
    while True:
        animal = random.choice(animals)
        number = random.randint(1, 999)
        user_id = f"ANN-{animal}-{number:03d}"
        found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_id).execute()
        if len(found_in_annotators.data) == 0:
            return user_id

      
        # found_in_ds = id_exists(supabase,user_id)
        # found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", new_id).execute()
        # found_in_annotations = supabase.table("annotations").select("annotator_id").eq("annotator_id", new_id).execute()

        # if len(found_in_annotators.data) == 0 and len(found_in_annotations.data) == 0:
        #     return new_id


if "page" not in st.session_state:
  st.session_state.page ="information_and_consent"

if st.session_state.page == "information_and_consent":   
  st.title("Evaluating Pseudo-labeling for Setswana Emotion Classification")
  st.subheader("Information about the study")
  st.write("give info...(detailed)")
  st.markdown("---")
  
  st.subheader("Consent")
  consent_statements = [
    "I have read and understood the information sheet.",
    "I understand that my participation in voluntary, I can skip any sentence I find uncomfortable and I can stop at any time without penalty.",
    "I understand that no personally identifiable information about me will be collected.",
    "I confirm that I am a native Setswana speaker between the ages of 18 and 65.",
    "I consent to the emotion labels and confidence scores I provide to be included in an anonymized dataset and to be released after completion of the researchers MSc study, and no later than 3 years after the data has been collected.",
    "I consent to participate in this research study."
  ]
  
  all_checked = True
  for item in consent_statements:
    checked = st.checkbox(item)
    if not checked:
      all_checked = False
  
  if st.button("Start labeling", disabled= not all_checked):
    st.session_state.page = "login_page"
    st.rerun()

#Login Page
if st.session_state.page == "login_page":
  st.title("Login Page")
  user_id = st.text_input(label= "User ID", placeholder = "Please enter your user id here")
  if st.button("Get a user id"):
    new_id = generate_unique_id(supabase)
    st.write(f"Your new user id is: {new_id}, Please store it somewhere safely so that you can use it next time.")
  if st.button("Log in"):
    found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_id).execute()
    if found_in_annotators.data !=0 or user_id==new_id:
      st.session_state.user_id = user_id
      st.session_state.page ="choosing_num_sentences"
      st.rerun()
    else:
      st.write("The user id is invalid, please create a new one")
      
#Participant choosing number of sentences they would like to label     
if st.session_state.page == "choosing_num_sentences":
  num_sentences_choices = [15,25,30,50,75,100]
  num_sentences_selected = st.selectbox("Please choose the number of sentences you would love to label", num_sentences_choices)

  
  sentences_to_label = supabase.table("sentences").select("sentence_id").lt("label_count", 3).execute()
  sentences_to_label = sentences_to_label.data
  
 
  
  labeled_by_user = supabase.table("annotations").select("sentence_id").eq("annotator_id",st.session_state.user_id).execute()
  labeled_by_user = labeled_by_user.data
  ids_excluded_to_user = [item["sentence_id"] for item in labeled_by_user]
  eligible_sentences = [item for item in sentences_to_label if item["sentence_id"] not in ids_excluded_to_user]
  eligible_sentence_ids = [item["sentence_id"] for item in eligible_sentences]
  # chosen_ids = sorted(random.sample(eligible_sentence_ids, num_sentences_selected))
  emotions = ["Select an emotion", "Joy", "Anger", "Sadness", "Fear", "Disgust", "Neutral", "Surprise"]
  confidence_scale = list(range(0,101,5))
  if "chosen_ids" not in st.session_state:
    st.session_state.chosen_ids = sorted(random.sample(eligible_sentence_ids, num_sentences_selected))
  if "user_responses" not in st.session_state:
    st.session_state.user_responses = {}
    
  if st.session_state.chosen_ids:
    response = supabase.table("sentences").select("sentence_id", "sentence").in_("sentence_id",st.session_state.chosen_ids).execute()
    for row in response.data:
      s_id = row["sentence_id"]
      s_text = row["sentence"]
      st.write(f"{s_text}")
      chosen_emotion = st.selectbox("Select the emotion", options = emotions, key = f"Emotion_for_{s_id}")
      if chosen_emotion != "Select an emotion":
        if s_id not in st.session_state.user_responses:
          st.session_state.user_responses[s_id] = {}
        st.session_state.user_responses[s_id]["emotion"] = chosen_emotion
        chosen_confidence = st.selectbox("Select how confident you are", options = confidence_scale, index=0, key = f"confidence_for_{s_id}")
        st.session_state.user_responses[s_id]["confidence"] = chosen_confidence
      else: 
        st.session_state.user_responses.pop(s_id, None)
    st.divider()
    st.write(st.session_state.user_responses)


    
  #   sentences = [row["sentence"] for row in response.data]
  # else:
  #   sentences= []
  
  # chosen_



  
  # st.write(f"{eligible_sentences}")
  # st.write(f"{eligible_sentence_ids}")
  # st.write(f"{chosen_ids}")
  # st.write(f"{sentences}")
  # st.session_state.chosen_ids = chosen_ids
  # st.session_state.page = "showing_sentences"
  # st.rerun()

# if st.session_state.page =="showing_sentences":
#   st.write("Please label the sentences")
#   sentences = []
#   for i in st.session_state.chosen_ids:
#     chosen_sentence = supabase.table("sentences").eq("sentence_id", i).execute()
#     sentences = sentences.append()
  



#   sent_length = (supabase.table("sentences").select("sentence", count = "exact", head = True).execute()).count
#   for i = 0 to num_sentences_selected
#   st.write("choose the number of sentences you would love to label")
