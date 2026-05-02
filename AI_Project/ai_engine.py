import google.generativeai as genai
import json
import os # New: To talk to the system
from datetime import datetime
from dotenv import load_dotenv # New: To load secrets

# 1. Load the hidden variables from the .env file
load_dotenv()

# 2. Securely fetch the key from the vault
API_KEY = os.getenv("GEMINI_API_KEY")

# 3. Configure the AI using that fetched key
genai.configure(api_key=API_KEY)

# Using your account's specific model string
model = genai.GenerativeModel('models/gemini-2.5-flash')

def process_command(user_text):
   # Grab the exact date AND the name of the day
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    today_name = now.strftime("%A") # This outputs "Monday", "Friday", etc.

    # Notice the updated first line of the prompt!
    prompt = f"""
    Today is {today_name}, {today_date}.
    Analyze this scheduling request: "{user_text}"
    
    Extract the information into a strict JSON ARRAY of objects. 
    Even if there is only one event, it MUST be inside a JSON array.
    If the user asks for recurring events (e.g., "for the next 3 weeks", "every Monday"), calculate the exact dates using today's date ({today_name}) as the starting point and generate a separate JSON object for EACH individual occurrence.
    
    Each object must have these exact keys:
    - "task" (string: a short name for the event)
    - "date" (string: format YYYY-MM-DD)
    - "time" (string: format HH:MM in 24-hour time)
    - "category" (string: either 'Academic' or 'Personal')

    Return ONLY the raw JSON array format. Do not add markdown formatting, backticks, or conversational text.
    """
    
    # ... (Keep the rest of your try/except block exactly the same)

    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        
        # This will now load a LIST of dictionaries
        data_list = json.loads(clean_text)
        
        # Safety check: if the AI accidentally returned a single dict, wrap it in a list
        if isinstance(data_list, dict):
            data_list = [data_list]
            
        return data_list, None 

    except Exception as e:
        return None, str(e)