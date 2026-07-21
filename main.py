import streamlit as st
from supabase import create_client
import random

#Initialize supabase client
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url,key)




def generate_unique_id(supabase):
    """ Generates unique id for paticipants. Query annotators table to make sure id is not assigned to someone else. Returns id if not found in annotators table."""
    animals = ["CAT", "DOG", "OWL", "FOX", "RAM", "HEN", "COW", "JAY", "BEE", "ANT", "BAT", "BUG", "CUB", "RAY", "FLY", "DAM"]
    while True:
        animal = random.choice(animals)
        number = random.randint(1, 999)
        user_id = f"ANN-{animal}-{number:03d}"
        found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_id).execute()
        if len(found_in_annotators.data) == 0:
            return user_id

def id_exists(supabase, user_id) :
  """checks if the id exists in the annotators table. returns true if id exists."""
  found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", user_id).execute()
  if len(found_in_annotators.data) > 0:
    return True
  else:
    return False

def add_user_to_table(supabase, user_id):
  """user id gets recorded to the annotators table. I use this function in the record_annotations function. if user_id already exists in the table I pass."""
  if not id_exists(supabase, user_id):
    supabase.table("annotators").insert({"annotator_id": user_id}).execute()
 
    
def record_annotation(supabase,user_responses):
   for s_id, response in user_responses.items():
    supabase.table("annotations").insert({"annotator_id": st.session_state.user_id, "sentence_id": s_id, "emotion_label":response["emotion"], "confidence_score": response["confidence"]}).execute()
    current = supabase.table("sentences").select("label_count").eq("sentence_id", s_id).execute()
    current_count = current.data[0]["label_count"]
    new_count = current_count +1
    supabase.table("sentences").update({"label_count" : new_count}).eq("sentence_id", s_id).execute()
    labeled_sentences = supabase.table("labeled_sentences").select("sentence_id").eq("sentence_id", s_id).execute()
    if len(labeled_sentences.data) ==0:
      supabase.table("labeled_sentences").insert({"sentence_id":s_id,f"label_{new_count}": response["emotion"], f"confidence_{new_count}": response["confidence"]}).execute()
    else:
      supabase.table("labeled_sentences").update({f"label_{new_count}":response["emotion"], f"confidence_{new_count}":response["confidence"]}).eq("sentence_id", s_id).execute()

def english_information_consent():
  """Information page and consent statements shown to user in English. The user cannot move to the next page/press the "Start Labeling" button if they have not given consent. """
  if st.session_state.page == "english_information_and_consent":   
    st.title("Evaluating Pseudo-labeling for Setswana Emotion Classification")
    st.subheader("Information about the study")
    st.write("give info...(detailed)")
    st.markdown("---")
    
    st.subheader("Consent")
    consent_statements = [
      "The research study was explained to me. I understand what this study is about." ,
      "I understand that my participation is voluntary, I can skip any sentences I don’t want to label, and I can stop at any time without penalty.",
      "I confirm that I am a native Setswana speaker between the ages of 18 and 65.",
      "I agree that my participation will remain anonymous, my name or other identifying data will not be collected and used by the researcher in their research report.",
      "I agree to the emotion labels and confidence scores I provide to be included in an anonymized dataset and to be released publicly after completion of the researchers MSc study, and no later than 3 years after the data is collected. ",
      "I agree that other researchers may use the information I provide in the sentence emotion labeling activity, but my name and any personal information will not be used or passed on."
    ]
    all_checked = True
    for item in consent_statements:
      checked = st.checkbox(item)
      if not checked:
        all_checked = False
    if st.button("Start labeling", disabled= not all_checked):
      st.session_state.page = "english_login_page"
      st.rerun()

def setswana_information_consent():
  """Information page and consent statements shown to user in Setswana. The user cannot move to the next page/press the "Start Labeling" button if they have not given consent. """
  if st.session_state.page == "setswana_information_and_consent":   
    st.title("Evaluating Pseudo-labeling for Setswana Emotion Classification")
    st.subheader("Information about the study")
    st.write("give info...(detailed)")
    st.markdown("---")
    
    st.subheader("Tumalano")
    consent_statements = [
     "Ke tlhaloseditswe ka patlisiso e. Ke tlhaloganya se thuto eno e leng ka sone.",
      "Ke a tlhaloganya gore go nna le seabe ga me ke boithaopo, nka kgona go tlogela dipolelo dipe fela tse ke sa batleng go di tshwaya, mme nka kgona go emisa nako nngwe le nngwe ntle le go otlhaiwa.",
      "Ke a netefatsa gore ke mmueledi wa Setswana wa dingwaga tse di fa gare ga 18 le 65. ",
      "Ke dumela gore go nna le seabe go tla nna go sa itsiwe, leina la me kgotsa tshedimosetso e nngwe e e supang gore ke mang ga e kitla e kokoanngwa e be e dirisiwa ke mmatlisisi mo pegong ya gagwe ya dipatlisiso.", 
      "Ke dumela gore matshwao a maikutlo le selekanyo sa tshepo tse ke di neelang di tsenngwe mo setlhopong sa tshedimosetso se se sa itsiweng gore ke mang, mme di gololwe mo setšhabeng morago ga thuto ya MSc ya mmatlisisi, mme e seng morago ga dingwanga tse tharo fa go sena go kokoanngwa tshedimosetso. ",
      "Ke dumela  gore babatlisisi ba bangwe ba ka dirisa tshedimosetso e ke e neelang mo tirong ya go kwala maikutlo a polelo, mme leina la me le tshedimosetso epe fela ya me ga e kitla e dirisiwa kgotsa e fetisiwa."
    ]
    all_checked = True
    for item in consent_statements:
      checked = st.checkbox(item)
      if not checked:
        all_checked = False
    if st.button("Simolola go tshwaya", disabled= not all_checked):
      st.session_state.page = "setswana_login_page"
      st.rerun()

#Login Page. The user inserts their user_id / create a new id. 
#Also checking that the user_id they have filled in exists in the annotators table

def english_login_page(): 
  """User inputs their user id or they create a new one. Get rid of whitespace and convert id to uppercase (Generate id function above and whats stored in DB is uppercase)
  validate that the entered id exists in the database or it's a newly generated one. """
  if st.session_state.page == "english_login_page":
    st.title("Login Page")
    user_id = st.text_input(label= "User ID", placeholder = "Please enter your user id here")
    if st.button("Get a user id"):
        if "new_id" not in session_state:
            st.session_state.new_id = generate_unique_id(supabase)
    if "new_id" in st.session_state:
      st.write(f"Your new user id is: {st.session_state.new_id}, Please store it somewhere safely so that you can use it next time.")
    if st.button("Log in"):
      entered_id = user_id.strip().upper()
      new_id = st.session_state.get("new_id")
      found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", entered_id).execute()
      id_is_valid = len(found_in_annotators.data) > 0 or (new_id is not None and entered_id == new_id)
      if entered_id and id_is_valid :
        if "user_id" not in session_state:
            st.session_state.user_id = entered_id
        st.session_state.page ="english_labeling_sentences"
        st.rerun()
      else:
        st.write("The user id is invalid, please get a new one")


def setswana_login_page(): 
  """User inputs their user id or they create a new one. Get rid of whitespace and convert id to uppercase (Generate id function above and whats stored in DB is uppercase)
  validate that the entered id exists in the database or it's a newly generated one. """
  if st.session_state.page == "setswana_login_page":
    st.title("Lefelo la go ikitsise")
    user_id = st.text_input(label= "Letshwao la boitshupo", placeholder = "Ka kopo, tsenya nomoro ya gago ya boitshupo fano")
    if st.button("Kopa letshwao la boitshupo"):
      st.session_state.new_id = generate_unique_id(supabase)
    if "new_id" in st.session_state:
      st.write(f"Letshwao la gago la palo ya boitshupo ke: {st.session_state.new_id}, Kopa o le boloke mo lefelong le e babalesegileng gore o kgone go le dirisa mo nakong e e tlang.")
    if st.button("Tsena"):
      entered_id = user_id.strip().upper()
      new_id = st.session_state.get("new_id")
      found_in_annotators = supabase.table("annotators").select("annotator_id").eq("annotator_id", entered_id).execute()
      id_is_valid = len(found_in_annotators.data) > 0 or (new_id is not None and entered_id == new_id)
      if entered_id and id_is_valid :
        if "user_id" not in session_state:  
            st.session_state.user_id = entered_id
        st.session_state.page ="setswana_choosing_num_sentences"
        st.rerun()
      else:
        st.write("Letshwao la boitshupo ga le a nepagala, ka kopo kopa le lesha")




def get_eligible_sentence_ids(supabase, user_id):
  """Extract sentences for the user to label. Look at sentences table for sentences which have been labeled less than 3 times. 
  Get sentence_ids of sentences already labeled by the user. If user already labeled a sentence then exclude it.
  Basically eligible sentences we can ask the user to label are those : 1. they have been labeled < 3 times. 2. they havent been labeled by user. """
  sentences_to_label = supabase.table("sentences").select("sentence_id").lt("label_count", 3).execute()
  sentences_to_label = sentences_to_label.data
  labeled_by_user = supabase.table("annotations").select("sentence_id").eq("annotator_id",st.session_state.user_id).execute()
  labeled_by_user = labeled_by_user.data
  excluded_ids = {item["sentence_id"] for item in labeled_by_user}
  eligible_sentence_ids = [item["sentence_id"] for item in sentences_to_label if item["sentence_id"] not in excluded_ids]
  return eligible_sentence_ids



def labeling(supabase, user_id):
    emotions = ["Select an emotion", "Joy", "Anger", "Sadness", "Fear", "Disgust", "Neutral", "Surprise"]
    confidence_scale = list(range(0,101,5))
    confidence_placeholder = "Select confidence"
    confidence = [confidence_placeholder] + confidence_scale
    #choosing sentences for the user to label (from the eligible sentences, choosing the number they selected)
    if "chosen_ids" not in st.session_state:
      eligible_sentence_ids = get_eligible_sentence_ids(supabase, st.session_state.user_id)
      st.session_state.chosen_ids = sorted(random.sample(eligible_sentence_ids, 10))
    if "user_responses" not in st.session_state:
      st.session_state.user_responses = {}
  
    #storing their responses
    if st.session_state.chosen_ids:
      response = supabase.table("sentences").select("sentence_id", "sentence").in_("sentence_id",st.session_state.chosen_ids).execute()
      for idx, row in enumerate(response.data, start=1):
        s_id = row["sentence_id"]
        s_text = row["sentence"]

        col_sentence, col_emotion, col_confidence = st.columns([60,20,20])

        with col_sentence:
          st.write(f"{idx}. {s_text}")
        with col_emotion:   
          chosen_emotion = st.selectbox("Emotion:", options = emotions, key = f"Emotion_for_{s_id}")
          emotion_chosen = chosen_emotion != emotions[0]
        with col_confidence:
          chosen_confidence = st.selectbox("Confidence:", options = confidence, index = 0, key = f"confidence_for_{s_id}", disabled = not emotion_chosen)
        if emotion_chosen:
          st.session_state.user_responses.setdefault(s_id, {})
          st.session_state.user_responses[s_id]["emotion"] = chosen_emotion
          if chosen_confidence != confidence_placeholder:
            st.session_state.user_responses[s_id]["confidence"] = chosen_confidence
          else:
            st.warning(f"Please set a confidence score for sentence {idx}. If you don't, it will be assumed to be 0.")
            st.session_state.user_responses[s_id]["confidence"] = 0
        else:
          st.session_state.user_responses.pop(s_id, None)
        st.divider()
          



def english_labeling_sentences(supabase, user_id):
  """Show the eligible sentences to the user. (showing number of sentences the user has chosen on previous page).
  record user input. restrict user from choosing confidence if they havent chosen an emotion label. """
    
  if st.session_state.page == "english_labeling_sentences":
    st.write("Give some info about the meanings/definitions of emotions.")  
    st.divider()
   
  labeling(supabase, user_id)
  while st.button("next"):
      try:
          add_user_to_table(supabase, st.session_state.user_id)
          record_annotation(supabase, st.session_state.user_responses)
          labeling(supabase, user_id)
      except Exception as e:
          st.error(f"Something went wrong: {e}")          
             
  if st.button("stop"): 
      try:
          add_user_to_table(supabase, st.session_state.user_id)
          record_annotation(supabase, st.session_state.user_responses)
      except Exception as e:
          st.error(f"Go nnile le phoso: {e}")
      else: 
          st.session_state.page = "english_end_page"
          st.rerun()
        
                 
                 



def setswana_labeling_sentences():
  """Show the eligible sentences to the user. (showing number of sentences the user has chosen on previous page).
  record user input. restrict user from choosing confidence if they havent chosen an emotion label. """
  if st.session_state.page == "setswana_labeling_sentences":
    emotions = ["Tlhopa Maikutlo", "Boitumelo", "Kgalefo", "Khutsafalo", "Poifo", "Go sisimoga", "Ga gona maikutlo", "Go makala"]
    confidence_scale = list(range(0,101,5))
    confidence_placeholder = "Tlhopa selekanyo sa tshepo"
    confidence = [confidence_placeholder] + confidence_scale
    
    #choosing sentences for the user to label (from the eligible sentences, choosing the number they selected)
    if "chosen_ids" not in st.session_state:
      eligible_sentence_ids = get_eligible_sentence_ids(supabase, st.session_state.user_id)
      st.session_state.chosen_ids = sorted(random.sample(eligible_sentence_ids, st.session_state.num_sentences_selected))
    if "user_responses" not in st.session_state:
      st.session_state.user_responses = {}
  
    #storing their their responses
    if st.session_state.chosen_ids:
      response = supabase.table("sentences").select("sentence_id", "sentence").in_("sentence_id",st.session_state.chosen_ids).execute()
      for idx, row in enumerate(response.data, start=1):
        s_id = row["sentence_id"]
        s_text = row["sentence"]

        col_sentence, col_emotion, col_confidence = st.columns([60,20,20])

        with col_sentence:
          st.write(f"{idx}. {s_text}")
        with col_emotion:   
          chosen_emotion = st.selectbox("Maikutlo:", options = emotions, key = f"Emotion_for_{s_id}")
          emotion_chosen = chosen_emotion != emotions[0]
        with col_confidence:
          chosen_confidence = st.selectbox("Selekanyo sa tshepo:", options = confidence, index = 0, key = f"confidence_for_{s_id}", disabled = not emotion_chosen)
        if emotion_chosen:
          st.session_state.user_responses.setdefault(s_id, {})
          st.session_state.user_responses[s_id]["emotion"] = chosen_emotion
          if chosen_confidence != confidence_placeholder:
            st.session_state.user_responses[s_id]["confidence"] = chosen_confidence
          else:
            st.warning(f"Kopa o tlhope selekanyo sa tshepo sa maikutlo a polelo {idx}. Fa o sa dire jalo, go tla tsewa gore ke 0.")
            st.session_state.user_responses[s_id]["confidence"] = 0
        else:
          st.session_state.user_responses.pop(s_id, None)
        st.divider()
  
      #saving their responses to the tables on supabase
      if st.button("Romela"):
          try:
              add_user_to_table(supabase, st.session_state.user_id)
              record_annotation(supabase, st.session_state.user_responses)
          except Exception as e:
              st.error(f"Go nnile le phoso: {e}")
          else: 
            st.session_state.page = "setswana_end_page"
            st.rerun()

def english_end_page():
  if st.session_state.page == "english_end_page":
    st.success("Thank you for participating, please share the link to this labeling task with other Tswana people you know.")
def setswana_end_page():
  if st.session_state.page == "setswana_end_page":
    st.success("Re lebogela go nna le karolo ga gago , kopa o abelane kgolagano ya tiro eno ya go tshwaya maikutlo le Batswana ba bangwe ba o ba itseng.")

















#first page the participant sees. This is where they choose which language they are comfortable participating in.
if "page" not in st.session_state:
  st.session_state.page ="Welcome_page"
if st.session_state.page =="Welcome_page":
  st.write("Welcome to the Setswana Emotion labeling task, your contibution is highly appreciated. Please choose the language you are most comfortable with:" )
  st.write("O amogelesegile mo tirong ya go tshwaya maikutlo a Setswana, re lebogela go nna le seabe ga gago. Ka kopo, tlhopa loleme le o gololesegileng ka lone. " )
  if st.button("English"):
    st.session_state.page = "english_information_and_consent"
    st.rerun()
  if st.button("Setswana"):
    st.session_state.page = "setswana_information_and_consent"
    st.rerun()
english_information_consent()
# setswana_information_consent()
english_login_page()
# setswana_login_page()
user_id = st.session_state.get("user_id")
# user_responses = st.session_state.get("user_id")
english_labeling_sentences(supabase, st.session_state.user_id)
# setswana_labeling_sentences()
english_end_page()
# setswana_end_page()











