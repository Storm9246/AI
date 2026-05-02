import json
import os
from datetime import datetime, timedelta

SCHEDULE_FILE = "schedule.json"

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return []
    with open(SCHEDULE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=4)

def add_event(event_data):
    schedule = load_schedule()
    schedule.append(event_data)
    save_schedule(schedule)

def delete_event(date, time, task):
    schedule = load_schedule()
    for i, e in enumerate(schedule):
        if e['date'] == date and e['time'] == time and e['task'] == task:
            del schedule[i]
            break
    save_schedule(schedule)

# ==========================================
# ADVANCED LOGIC (AI Search & Conflicts)
# ==========================================
def is_duplicate(date, time_str, task):
    """Checks if the EXACT same task is already scheduled at this time."""
    schedule = load_schedule()
    for e in schedule:
        # We use .lower() so "OS class" and "os class" are flagged as the same thing
        if e['date'] == date and e['time'] == time_str and e['task'].lower() == task.lower():
            return True
    return False

def check_conflict(date, time_str, duration_mins=60):
    schedule = load_schedule()
    events_today = [e for e in schedule if e.get("date") == date]
    
    req_time = datetime.strptime(time_str, "%H:%M")
    req_end = req_time + timedelta(minutes=duration_mins)

    for e in events_today:
        e_time = datetime.strptime(e['time'], "%H:%M")
        e_end = e_time + timedelta(minutes=60)
        
        if req_time < e_end and req_end > e_time:
            return True 
            
    return False 

def find_next_available(date, start_time_str, duration_mins=60):
    current_time = datetime.strptime(start_time_str, "%H:%M")
    end_of_day = datetime.strptime("23:00", "%H:%M") 

    while current_time <= end_of_day:
        time_str = current_time.strftime("%H:%M")
        if not check_conflict(date, time_str, duration_mins):
            return time_str 
        current_time += timedelta(minutes=30)
    
    return None