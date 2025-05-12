import os
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def create_nurse_chat():
    model = genai.GenerativeModel("models/gemini-1.5-pro")
    chat = model.start_chat(history=[
        {
            "role": "user",
            "parts": "You are Aura, a kind and professional virtual nurse. Gently ask follow-up questions and guide users with empathy."
        }
    ])
    return chat

def continue_nurse_chat(chat, user_input):
    try:
        return chat.send_message("Patient said: " + user_input).text.strip()
    except Exception as e:
        print("Gemini Chat Error:", e)
        return "Sorry, I'm having trouble understanding. Can you try rephrasing?"

def get_precautions_from_gemini(disease):
    prompt = f"What are the top 3 self-care precautions for {disease}?"
    try:
        return genai.GenerativeModel("models/gemini-1.5-pro").generate_content(prompt).text.strip()
    except Exception as e:
        return "Precaution data not available."

def get_routine_from_gemini(disease):
    prompt = f"What daily habits help manage {disease}?"
    try:
        return genai.GenerativeModel("models/gemini-1.5-pro").generate_content(prompt).text.strip()
    except Exception:
        return "Routine suggestions not available."
