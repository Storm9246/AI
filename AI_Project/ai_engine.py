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
    1. TIME TRAVEL: If the user requests a time that has already passed today, you MUST assume TOMORROW and set the date accordingly.
    2. MISSING INFO: If no date is specified, assume today. If no time is specified, make a logical guess or default to "09:00".
    3. TASKS VS EVENTS (CRITICAL DISTINCTION): 
       - "event": Things that take up a physical block of time and cause conflicts (Classes, Meetings, Exams, Quizzes).
       - "task": Things that are due at a specific time but don't block the calendar (Deadlines, Projects, Assignments, Lab Tasks, Personal Tasks).

    Extract the information into a strict JSON ARRAY of objects. Use exactly these keys:
    - "action" (string: 'schedule' or 'clear_day')
    - "item_type" (string: 'event' or 'task')
    - "task" (string: The name, e.g., 'AI Class', 'Final Exam', or 'Gym/Pay Bills')
    - "date" (string: format YYYY-MM-DD)
    - "time" (string: format HH:MM in 24-hour time. For events, start time. For tasks, deadline time)
    - "location" (string: Room name, or 'TBD')
    - "category" (string: 'Academic', 'Self-Study', 'Home Chores', 'Outdoor Errands', 'Project', 'Exam', 'Quiz', 'Assignment', 'Lab Task', 'Personal Task')
    - "duration_mins" (integer: Default 60 for classes/quizzes, 120 for exams. 0 for tasks)
    - "is_flexible" (boolean: true if it can be moved, false if strict like exams/classes)
    - "status" (string: 'pending' if it's a task. Leave blank "" for events)

    EXAMPLE INPUT 1: "I have a DB lab task due tomorrow at 5pm."
    EXAMPLE OUTPUT 1: [{{"action": "schedule", "item_type": "task", "task": "DB Lab Task", "date": "2026-05-11", "time": "17:00", "location": "TBD", "category": "Lab Task", "duration_mins": 0, "is_flexible": false, "status": "pending"}}]
    
    EXAMPLE INPUT 2: "Schedule my AI Midterm Exam for Friday at 10 AM."
    EXAMPLE OUTPUT 2: [{{"action": "schedule", "item_type": "event", "task": "AI Midterm Exam", "date": "2026-05-15", "time": "10:00", "location": "TBD", "category": "Exam", "duration_mins": 120, "is_flexible": false, "status": ""}}]

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