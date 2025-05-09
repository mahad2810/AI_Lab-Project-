from flask import Blueprint, request, jsonify
from disease_predict import DiseasePredictionModel
from gemini_api import create_nurse_chat, continue_nurse_chat, get_precautions_from_gemini, get_routine_from_gemini
import spacy
import re

chatbot_blueprint = Blueprint('chatbot', __name__)
user_sessions = {}
disease_model = DiseasePredictionModel()

# Load spaCy model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_md")
print("Model loaded.\n")

# Symptom list
symptoms = [
    "sweating", "chest_pain", "itching", "skin_rash", "nodal_skin_eruptions",
    "continuous_sneezing", "shivering", "chills", "joint_pain", "stomach_pain",
    "acidity", "ulcers_on_tongue", "muscle_wasting", "vomiting", "burning_micturition",
    "spotting_urination", "fatigue", "weight_gain", "anxiety", "cold_hands_and_feets",
    "mood_swings", "weight_loss", "restlessness", "lethargy", "patches_in_throat",
    "irregular_sugar_level", "cough", "high_fever", "sunken_eyes", "breathlessness",
    "dehydration", "indigestion", "headache", "yellowish_skin", "dark_urine", "nausea",
    "loss_of_appetite", "pain_behind_the_eyes", "back_pain", "constipation",
    "abdominal_pain", "diarrhoea", "mild_fever", "yellow_urine", "yellowing_of_eyes",
    "fluid_overload", "swelling_of_stomach", "swelled_lymph_nodes", "malaise",
    "blurred_and_distorted_vision", "phlegm", "throat_irritation", "redness_of_eyes",
    "sinus_pressure", "runny_nose", "congestion", "weakness_in_limbs", "fast_heart_rate",
    "pain_during_bowel_movements", "pain_in_anal_region", "bloody_stool",
    "irritation_in_anus", "neck_pain", "dizziness", "cramps", "bruising", "obesity",
    "swollen_legs", "swollen_blood_vessels", "puffy_face_and_eyes", "enlarged_thyroid",
    "brittle_nails", "swollen_extremeties", "excessive_hunger", "drying_and_tingling_lips",
    "slurred_speech", "knee_pain", "hip_joint_pain", "muscle_weakness", "stiff_neck",
    "swelling_joints", "movement_stiffness", "spinning_movements", "loss_of_balance",
    "unsteadiness", "weakness_of_one_body_side", "loss_of_smell", "bladder_discomfort",
    "foul_smell_of_urine", "continuous_feel_of_urine", "passage_of_gases",
    "internal_itching", "toxic_look_(typhos)", "depression", "irritability", "muscle_pain",
    "altered_sensorium", "red_spots_over_body", "belly_pain", "abnormal_menstruation",
    "dischromic_patches", "watering_from_eyes", "increased_appetite", "polyuria",
    "family_history", "mucoid_sputum", "rusty_sputum", "lack_of_concentration",
    "visual_disturbances", "receiving_blood_transfusion", "receiving_unsterile_injections",
    "coma", "stomach_bleeding", "distention_of_abdomen", "history_of_alcohol_consumption",
    "blood_in_sputum", "prominent_veins_on_calf", "palpitations", "painful_walking",
    "pus_filled_pimples", "blackheads", "scurring", "skin_peeling", "silver_like_dusting",
    "small_dents_in_nails", "inflammatory_nails", "blister", "red_sore_around_nose",
    "yellow_crust_ooze"
]

# Synonyms mapping
synonyms = {
    "chest discomfort": "chest_pain", "tightness in chest": "chest_pain", "chest pressure": "chest_pain",
    "lightheaded": "dizziness", "lightheadedness": "dizziness", "feeling faint": "dizziness",
    "tired": "fatigue", "exhausted": "fatigue", "low energy": "lethargy",
    "burning while urinating": "burning_micturition", "pain while urinating": "burning_micturition",
    "stomach ache": "stomach_pain", "abdominal cramps": "abdominal_pain", "belly pain": "abdominal_pain",
    "no appetite": "loss_of_appetite", "not hungry": "loss_of_appetite",
    "can't breathe": "breathlessness", "shortness of breath": "breathlessness",
    "throwing up": "vomiting", "nauseated": "nausea", "nauseous": "nausea",
    "runny nose": "runny_nose", "sore throat": "throat_irritation", "scratchy throat": "throat_irritation",
    "fever": "high_fever", "feeling cold": "chills", "body pain": "muscle_pain", "body ache": "muscle_pain",
    "blurred vision": "blurred_and_distorted_vision", "painful joints": "joint_pain",
    "stiff joints": "movement_stiffness", "loss of balance": "unsteadiness",
    "swollen legs": "swollen_legs", "yellow skin": "yellowish_skin", "yellow eyes": "yellowing_of_eyes",
    "red eyes": "redness_of_eyes"
}

# Follow-up questions mapping
followup_questions = {
    "chest_pain": "Is the chest pain sharp, dull, or crushing?",
    "breathlessness": "Do you feel breathless during activity or at rest?",
    "fatigue": "Is your fatigue constant or does it come and go?",
    "stomach_pain": "Does the pain worsen after eating or at night?",
    "headache": "Is the headache localized or spread across your head?",
    "nausea": "Have you actually vomited or just felt nauseated?",
    "joint_pain": "Are your joints swollen or stiff?",
    "vomiting": "How often have you been vomiting?",
    "fever": "Have you measured your temperature? How high was it?"
}

# Symptom extraction function
def extract_symptoms(text):
    text = text.lower()
    doc = nlp(text)
    lemmas = " ".join([token.lemma_ for token in doc])
    found = set()

    for phrase, mapped in synonyms.items():
        if phrase in text or phrase in lemmas:
            found.add(mapped)

    for sym in symptoms:
        sym_clean = sym.replace("_", " ")
        if sym_clean in text or sym_clean in lemmas:
            found.add(sym)

    for sym in symptoms:
        try:
            score = doc.similarity(nlp(sym.replace("_", " ")))
            if score > 0.85:
                found.add(sym)
        except:
            continue

    return list(found)

# Chatbot route
@chatbot_blueprint.route('/chatbot/diagnose', methods=['POST'])
def diagnose():
    data = request.get_json()
    user_id = data.get('user_id', 'default')
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Empty message'}), 400

    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "chat": create_nurse_chat(),
            "stage": "initial",
            "symptom_notes": [],
            "symptoms": set()
        }

    session = user_sessions[user_id]
    responses = []

    extracted = extract_symptoms(message)
    session["symptom_notes"].append(message)
    session["symptoms"].update(extracted)

    continue_nurse_chat(session["chat"], message)

    disease_to_return = None  # Initialize

    if session["stage"] == "initial":
        if extracted:
            symptom = extracted[0]
            question = followup_questions.get(symptom, "Can you describe it more?")
            responses.append(f"Thanks for sharing. {question}")
        else:
            responses.append("Can you describe your symptom in more detail?")
        session["stage"] = "clarify"

    elif session["stage"] == "clarify":
        if len(session["symptom_notes"]) >= 3:
            standardized_symptoms = list(session["symptoms"])
            print("Symptoms sent to model for prediction:", standardized_symptoms)
            prediction = disease_model.predict(standardized_symptoms)
            disease = prediction["final_prediction"]

            if disease.lower() == "arthritis" and not re.search(r'joint|swelling|stiffness', " ".join(session["symptom_notes"]).lower()):
                disease = "Tension Headache"

            precautions = get_precautions_from_gemini(disease).split('\n')[:3]
            routine = get_routine_from_gemini(disease).split('\n')[:3]

            responses.append(f"Based on your symptoms, it might be **{disease}**.")
            responses.append("🩺 **Precautions:**\n- " + "\n- ".join([p.strip("- ") for p in precautions if p.strip()]))
            responses.append("🏃 **Routine Suggestions:**\n- " + "\n- ".join([r.strip("- ") for r in routine if r.strip()]))
            responses.append("Would you like help finding a doctor or specialist?")
            session["stage"] = "referral"
            disease_to_return = disease  # ✅ Add to response

        else:
            responses.append("Tell me more—any other symptoms or details?")

    elif session["stage"] == "referral":
        responses.append("Would you prefer a general physician or a specialist?")
        session["stage"] = "complete"

    else:
        responses.append("Take care, and feel free to chat with me anytime.")

    return jsonify({
        "response": responses,
        "stage": session["stage"],
        "disease": disease_to_return  # ✅ Include disease
    })
