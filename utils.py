def parse_json(assistant_response):
    # Call the extract_json function and capture its return values
    differential_diagnosis, critical_actions, modified_text = extract_json(assistant_response)

    # Check if the extracted values indicate no JSON content
    if not differential_diagnosis and not critical_actions:
        print("No JSON content found in assistant response.")
        st.session_state.assistant_response = modified_text
        return
    
    # Add debugging print statements
    print("Debug: assistant response: ", assistant_response)
    print("Debug: differential_diagnosis:", differential_diagnosis)
    print("Debug: critical_actions:", critical_actions)
    print("Debug: modified_text:", modified_text)
    
    # Assign the return values to the session state
    st.session_state.differential_diagnosis = differential_diagnosis
    st.session_state.critical_actions = critical_actions
    st.session_state.assistant_response = modified_text

# Sidebar display
def display_sidebar():
    with st.sidebar:
        st.markdown("<h1 style='margin-top: -60px;text-align: center;'>DA🤖</h1>", unsafe_allow_html=True)
        
        
        tab1, tab2, tab3, tab4 = st.tabs(["Functions", "Specialists", "Note Analysis", "Update Variables"])
        
        with tab1:
                    # Actions and DDX
            if st.session_state.critical_actions:
                
                st.subheader(":orange[Critical Actions]")
                for action in st.session_state.critical_actions.get('critical_actions', []):
                    st.markdown(f"- :orange[{action}]")
                

            
            
            if st.session_state.differential_diagnosis:
                st.subheader("Differential Diagnosis")
                for diagnosis_obj in st.session_state.differential_diagnosis.get("differential_diagnosis", []):
                    diagnosis = diagnosis_obj.get("diagnosis")
                    probability = diagnosis_obj.get("probability")
                    st.markdown(f"- {diagnosis} {probability}%")
                st.divider()
            display_functions_tab()
        with tab2:
                                # Actions and DDX
            if st.session_state.critical_actions:
                
                st.subheader(":orange[Critical Actions]")
                for action in st.session_state.critical_actions.get('critical_actions', []):
                    st.markdown(f"- :orange[{action}]")
                

            
            
            if st.session_state.differential_diagnosis:
                st.subheader("Differential Diagnosis")
                for diagnosis_obj in st.session_state.differential_diagnosis.get("differential_diagnosis", []):
                    diagnosis = diagnosis_obj.get("diagnosis")
                    probability = diagnosis_obj.get("probability")
                    st.markdown(f"- {diagnosis} {probability}%")
                st.divider()
            choose_specialist_radio()
            
            st.subheader(':orange[Consult Recommnedations]')
            button1 = st.button("General Reccommendations")
            button2 = st.button("Diagnosis")
            button3 = st.button("Treatment Plan")
            button4 = st.button("Disposition Plan")

            # process buttons
            # "General Rec"
            if button1: 
                # consult specialist, use prompts from prompts.py
                specialist = st.session_state.specialist
                prompt = consult_specialist
                button_input(specialist, prompt)


                # switch to EM agent
                specialist = "Emergency Medicine"
                st.session_state.specialist = specialist
                st.session_state.assistant_id = specialist_id_caption[specialist]["assistant_id"]

                # have EM agent update ddx and plan with new information only. 
                prompt = integrate_consultation
                button_input(specialist, prompt)
            
                        # process buttons
            # "Diagnosis consult"
            if button2: 
                # consult specialist, use prompts from prompts.py
                specialist = st.session_state.specialist
                prompt = consult_diagnosis
                button_input(specialist, prompt)


                # switch to EM agent
                specialist = "Emergency Medicine"
                st.session_state.specialist = specialist
                st.session_state.assistant_id = specialist_id_caption[specialist]["assistant_id"]

                # have EM agent update ddx and plan with new information only. 
                prompt = integrate_consultation
                button_input(specialist, prompt)

                        # process buttons
            # "Treatment consult"
            if button3: 
                # consult specialist, use prompts from prompts.py
                specialist = st.session_state.specialist
                prompt = consult_treatment
                button_input(specialist, prompt)


                # switch to EM agent
                specialist = "Emergency Medicine"
                st.session_state.specialist = specialist
                st.session_state.assistant_id = specialist_id_caption[specialist]["assistant_id"]

                # have EM agent update ddx and plan with new information only. 
                prompt = integrate_consultation
                button_input(specialist, prompt)
            
                        
            # "Disposition consult"
            if button4: 
                # consult specialist, use prompts from prompts.py
                specialist = st.session_state.specialist
                prompt = consult_disposition
                button_input(specialist, prompt)


                # switch to EM agent
                specialist = "Emergency Medicine"
                st.session_state.specialist = specialist
                st.session_state.assistant_id = specialist_id_caption[specialist]["assistant_id"]

                # have EM agent update ddx and plan with new information only. 
                prompt = integrate_consultation
                button_input(specialist, prompt)
            
        with tab3:
            display_note_analysis_tab()
            
# Sidebar tabs and functions
def display_functions_tab():
    
    st.subheader('Process Management')
    col1, col2 = st.columns(2)
    with col1:
        button1 = st.button("🛌Disposition Analysis")
    with col2:
        button2 = st.button("💉Which Procedure")

    st.subheader('📝Note Writer')
    col1, col2 = st.columns(2)
    with col1:
        button3 = st.button('Full Medical Note')
        button4 = st.button("Pt Education Note")
    with col2:
        button11 = st.button('HPI only')
        button12 = st.button('A&P only')
        button13 = st.button('PT Plan')
        

    st.subheader('🏃‍♂️Flow')
    col1, col2 = st.columns(2)
    with col1:
        button5 = st.button("➡️Next Step Recommendation")
        button7 = st.button("📞Consult specialist🧑‍⚕️")
    with col2:
        button6 = st.button('➡️➡️I did that, now what?')

    st.divider()
    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        button9 = st.button('NEW THREAD', type="primary")

    # Process button actions
    process_buttons(button1, button2, button3, button4, button5, button6, button7, button9, button11, button12, button13)

# Process the buttons
def process_buttons(button1, button2, button3, button4, button5, button6, button7, button9, button11, button12, button13):
    if button1:
        st.session_state["user_question"] = disposition_analysis
    if button2:
        st.session_state["user_question"] = procedure_checklist
    if button3:
        specialist = 'Note Writer'
        prompt = "Write a full medical note on this patient"
        button_input(specialist, prompt)
    if button4:
        st.session_state["user_question"] = pt_education + f"\n the patient's instructions needs to be in {st.session_state.patient_language}"
    if button5:
        st.session_state["user_question"] = "What should i do next here in the emergency department?"
    if button6:
        st.session_state["user_question"] = "Ok i did that. Now what?"
    if button7:
        specialist = st.session_state.specialist
        prompt = consult_specialist
        button_input(specialist, prompt)
    if button9:
        new_thread()
    if button11:
        specialist = 'Note Writer'
        prompt = create_hpi
        button_input(specialist, prompt)
    if button12:
        specialist = 'Note Writer'
        prompt = create_ap
        button_input(specialist, prompt)
    if button13:
        specialist = 'Musculoskeletal Systems'
        prompt = pt_plan
        button_input(specialist, prompt)
    
# Choosing the specialty group
def choose_specialist_radio():
    # Extract the list of specialities
    specialities = list(specialist_id_caption.keys())
    
    # Extract the list of captions
    captions = [specialist_id_caption[speciality]["caption"] for speciality in specialities]

    # Display the radio button with specialities and captions
    specialist = st.radio("**:red[Choose Your Specialty Group]**", specialities, captions = captions)
    
    if specialist and specialist != st.session_state.specialist:
        st.session_state.specialist = specialist
        st.session_state.assistant_id = specialist_id_caption[specialist]["assistant_id"]
        st.session_state['should_rerun'] = True
        st.rerun()
    
    return specialist

# process button inputs for quick bot responses
def button_input(specialist, prompt):
    st.session_state.specialist = specialist    
    st.session_state.assistant_id = specialist_id_caption[specialist]["assistant_id"]
    handle_userinput(prompt)
