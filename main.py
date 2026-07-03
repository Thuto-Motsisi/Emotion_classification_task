import streamlit as st


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
    st.session_state.page = "choosing_num_sentences"
    
if st.session_state.page == "choosing_num_sentence"
  st.write("choose the number of sentences you would love to label")
