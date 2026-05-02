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

def check_conflict(date, time_str, duration_mins):
    schedule = load_schedule()
    events_today = [e for e in schedule if e.get("date") == date]
    
    req_time = datetime.strptime(time_str, "%H:%M")
    req_end = req_time + timedelta(minutes=duration_mins)

    for e in events_today:
        e_time = datetime.strptime(e['time'], "%H:%M")
        # Use the saved duration if it exists, otherwise default to 60
        e_duration = e.get('duration_mins', 60) 
        e_end = e_time + timedelta(minutes=e_duration)
        
        # Conflict Math: Does the new event overlap with an existing event's block?
        if req_time < e_end and req_end > e_time:
            return True 
            
    return False 

def is_outside_context_window(date, time_str, category):
    """Checks if the requested time breaks the Weekday/Weekend rules."""
    req_date = datetime.strptime(date, "%Y-%m-%d")
    is_weekend = req_date.weekday() >= 5 
    current_time = datetime.strptime(time_str, "%H:%M")

    if is_weekend:
        return False # Weekends have no rules!

    # Weekday Rules
    if category == "Academic":
        start = datetime.strptime("07:00", "%H:%M")
        end = datetime.strptime("17:00", "%H:%M")
        if current_time < start or current_time >= end:
            return True
    else: # Self-Study, Home Chores, Outdoor Errands
        personal_start = datetime.strptime("17:00", "%H:%M")
        if current_time < personal_start:
            return True
            
    return False

def find_next_available(date, start_time_str, duration_mins, category):
    req_date = datetime.strptime(date, "%Y-%m-%d")
    is_weekend = req_date.weekday() >= 5 
    current_time = datetime.strptime(start_time_str, "%H:%M")
    
    if is_weekend:
        end_of_day = datetime.strptime("23:00", "%H:%M")
    else:
        if category == "Academic":
            end_of_day = datetime.strptime("17:00", "%H:%M") 
            earliest_start = datetime.strptime("07:00", "%H:%M")
            if current_time < earliest_start:
                current_time = earliest_start
        else:
            end_of_day = datetime.strptime("23:00", "%H:%M")
            personal_start = datetime.strptime("17:00", "%H:%M")
            if current_time < personal_start:
                current_time = personal_start

    while current_time + timedelta(minutes=duration_mins) <= end_of_day:
        time_str = current_time.strftime("%H:%M")
        if not check_conflict(date, time_str, duration_mins):
            return time_str 
        current_time += timedelta(minutes=30)
    
    return None

def get_events_for_date(date):
    """Returns a sorted list of all events for a specific date."""
    schedule = load_schedule()
    events = [e for e in schedule if e.get("date") == date]
    return sorted(events, key=lambda x: x['time'])