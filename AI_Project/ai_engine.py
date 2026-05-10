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
    # Grab the exact date, day, AND exact current time
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    today_name = now.strftime("%A") 
    current_time = now.strftime("%H:%M") # NEW: Grabs 24-hour time right now

    prompt = f"""
    You are the brain of SAPSA, a highly precise scheduling extraction API.
    Today is {today_name}, {today_date}. The current exact time is {current_time}.
    
    Analyze this user request: "{user_text}"
    
    CRITICAL RULES:
    1. TIME TRAVEL: If the user requests a time that has already passed today, assume TOMORROW and set the date.
    2. TASKS VS EVENTS: "event" blocks time (Classes, Meetings). "task" is a deadline (Projects).
    3. RECURRENCE (CRITICAL): If the user asks for a repeating event (e.g., "Every Thursday for a month" or "Sick day all week"), output "recur_type": "weekly" (or "daily") and "recur_until": "YYYY-MM-DD". For single events, use "recur_type": "none".
    4. BATCHING: If asking for multiple different days/times (e.g., "Mon and Wed at 8am"), output multiple JSON objects.

    Extract into a strict JSON ARRAY of objects. Keys:
    - "action" ('schedule' or 'clear_day')
    - "item_type" ('event' or 'task')
    - "task" (String. If clear_day, put 'Off Day' or 'Sick Day')
    - "date" (YYYY-MM-DD. For clear_day, the date to wipe)
    - "time" (HH:MM in 24-hour. Use "00:00" for clear_day)
    - "location" (Room or 'TBD')
    - "category" ('Academic', 'Self-Study', 'Home Chores', 'Outdoor Errands', 'Project', 'Exam', 'Quiz', 'Assignment', 'Lab Task', 'Personal Task', 'All')
    - "duration_mins" (integer: Default 60. 0 for tasks/clear_day)
    - "is_flexible" (boolean: true/false)
    - "status" ('pending' for task. "" for events/clear_day)
    - "recur_type" ('none', 'daily', or 'weekly')
    - "recur_until" (YYYY-MM-DD of the end date, or "")

    EXAMPLE 1 (Batching): "Add OS Lab on Mon and Wed at 2pm"
    OUTPUT 1: [{{"action": "schedule", "item_type": "event", "task": "OS Lab", "date": "2026-05-11", "time": "14:00", "location": "TBD", "category": "Academic", "duration_mins": 60, "is_flexible": false, "status": "", "recur_type": "none", "recur_until": ""}}, {{"action": "schedule", "item_type": "event", "task": "OS Lab", "date": "2026-05-13", "time": "14:00", "location": "TBD", "category": "Academic", "duration_mins": 60, "is_flexible": false, "status": "", "recur_type": "none", "recur_until": ""}}]

    EXAMPLE 2 (Recurrence): "I have a weekly team meeting every Friday at 10am until June 30th"
    OUTPUT 2: [{{"action": "schedule", "item_type": "event", "task": "Team Meeting", "date": "2026-05-15", "time": "10:00", "location": "TBD", "category": "Academic", "duration_mins": 60, "is_flexible": true, "status": "", "recur_type": "weekly", "recur_until": "2026-06-30"}}]

    EXAMPLE 3 (Off Day): "Mark tomorrow as a sick day"
    OUTPUT 3: [{{"action": "clear_day", "item_type": "event", "task": "Sick Day", "date": "2026-05-11", "time": "00:00", "location": "TBD", "category": "All", "duration_mins": 0, "is_flexible": false, "status": "", "recur_type": "none", "recur_until": ""}}]

    EXAMPLE 4 (Parallel Mapping / Respectively): "Add OS, AI, and DB on Mon, Tue, and Fri at 8am, 9am, and 10am in D16, E32, and C16 respectively."
    OUTPUT 4: [{{"action": "schedule", "item_type": "event", "task": "OS", "date": "2026-05-11", "time": "08:00", "location": "D16", "category": "Academic", "duration_mins": 60, "is_flexible": false, "status": "", "recur_type": "none", "recur_until": ""}}, {{"action": "schedule", "item_type": "event", "task": "AI", "date": "2026-05-12", "time": "09:00", "location": "E32", "category": "Academic", "duration_mins": 60, "is_flexible": false, "status": "", "recur_type": "none", "recur_until": ""}}, {{"action": "schedule", "item_type": "event", "task": "DB", "date": "2026-05-15", "time": "10:00", "location": "C16", "category": "Academic", "duration_mins": 60, "is_flexible": false, "status": "", "recur_type": "none", "recur_until": ""}}]

    Return ONLY the raw JSON array. Do not wrap it in markdown formatting or backticks.
    """
    
    # ... (Keep the try/except block below exactly the same)

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
    
def generate_daily_briefing(date, events):
    """Sends the day's schedule to Gemini for a personalized summary."""
    if not events:
        return "Your schedule is completely clear for this day. Enjoy your free time!", None
    
    # We pass the raw JSON data to Gemini so it can read it
    prompt = f"""
    You are SAPSA, an AI scheduling assistant.
    The user's name is Zain. The date you are analyzing is {date}.
    Here are Zain's scheduled events for this day:
    {json.dumps(events, indent=2)}
    
    Write a quick, friendly, and concise morning briefing (max 3 sentences).
    Acknowledge the balance of Academic vs Personal tasks, point out any heavy blocks or gaps, and offer a quick word of encouragement. Do not use markdown formatting or asterisks.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip(), None
    except Exception as e:
        return None, str(e)