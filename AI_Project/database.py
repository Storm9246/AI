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

# ==========================================
# ADVANCED LOGIC (AI Search & Conflicts)
# ==========================================
def is_duplicate(date, time_str, task):
    """Checks if the EXACT same task is already scheduled at this time."""
    schedule = load_schedule()
    for e in schedule:
        if e['date'] == date and e['time'] == time_str and e['task'].strip().lower() == task.strip().lower():
            return True
    return False

def check_conflict(date, time_str, duration_mins):
    schedule = load_schedule()
    # THE FIX: Completely ignore "tasks" (deadlines) when checking for time conflicts!
    events_today = [e for e in schedule if e.get("date") == date and e.get("item_type") != "task"]
    
    req_time = datetime.strptime(time_str, "%H:%M")
    req_end = req_time + timedelta(minutes=duration_mins)

    for e in events_today:
        e_time = datetime.strptime(e['time'], "%H:%M")
        e_duration = e.get('duration_mins', 60) 
        e_end = e_time + timedelta(minutes=e_duration)
        
        if req_time < e_end and req_end > e_time:
            return f"'{e['task']}' is already scheduled here." 
            
    return False 

def is_outside_context_window(date, time_str, category):
    req_date = datetime.strptime(date, "%Y-%m-%d")
    is_weekend = req_date.weekday() >= 5 
    current_time = datetime.strptime(time_str, "%H:%M")

    # THE FIX: Exams and Quizzes must follow strict Academic rules!
    if category in ["Academic", "Exam", "Quiz"]:
        if is_weekend:
            return f"{category} cannot be scheduled on Weekends!" 
            
        start = datetime.strptime("07:00", "%H:%M")
        end = datetime.strptime("17:00", "%H:%M")
        if current_time < start or current_time >= end:
            return f"Outside normal Academic hours (07:00 - 17:00)."
    else: 
        if is_weekend:
            return False 
            
        personal_start = datetime.strptime("17:00", "%H:%M")
        if current_time < personal_start:
            return f"Outside normal {category} hours (Starts at 17:00)."
            
    return False

def find_next_available(date, start_time_str, duration_mins, category):
    req_date = datetime.strptime(date, "%Y-%m-%d")
    is_weekend = req_date.weekday() >= 5 
    current_time = datetime.strptime(start_time_str, "%H:%M")
    
    if is_weekend:
        end_of_day = datetime.strptime("23:00", "%H:%M")
    else:
        if category in ["Academic", "Exam", "Quiz"]:
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

# ==========================================
# SYSTEM OVERRIDE COMMANDS 
# ==========================================
def delete_event(date, time, task):
    schedule = load_schedule()
    # Clean kill: Strips spaces and ignores caps
    schedule = [e for e in schedule if not (e['date'] == date and e['time'] == time and e['task'].strip().lower() == task.strip().lower())]
    save_schedule(schedule)

def delete_event_at_time(date, time_str):
    schedule = load_schedule()
    schedule = [e for e in schedule if not (e['date'] == date and e['time'] == time_str)]
    save_schedule(schedule)

def clear_category_for_day(date, category):
    schedule = load_schedule()
    if category.lower() == "all":
        schedule = [e for e in schedule if e['date'] != date]
    else:
        schedule = [e for e in schedule if not (e['date'] == date and e.get('category', '').lower() == category.lower())]
    save_schedule(schedule)

def get_events_for_date(date):
    schedule = load_schedule()
    events = [e for e in schedule if e.get("date") == date]
    return sorted(events, key=lambda x: x['time'])

def get_all_available_slots(date, duration_mins, category):
    req_date = datetime.strptime(date, "%Y-%m-%d")
    is_weekend = req_date.weekday() >= 5 
    
    # THE PARADOX FIX (Now includes Exams and Quizzes)
    if is_weekend and category in ["Academic", "Exam", "Quiz"]:
        return [] 
        
    if is_weekend:
        current_time = datetime.strptime("08:00", "%H:%M")
        end_of_day = datetime.strptime("23:00", "%H:%M")
    else:
        if category in ["Academic", "Exam", "Quiz"]:
            current_time = datetime.strptime("07:00", "%H:%M")
            end_of_day = datetime.strptime("17:00", "%H:%M") 
        else:
            current_time = datetime.strptime("17:00", "%H:%M")
            end_of_day = datetime.strptime("23:00", "%H:%M")

    available_slots = []
    
    while current_time + timedelta(minutes=duration_mins) <= end_of_day:
        time_str = current_time.strftime("%H:%M")
        if not check_conflict(date, time_str, duration_mins):
            available_slots.append(time_str)
        current_time += timedelta(minutes=30)
    
    return available_slots

# ==========================================
# DASHBOARD & TASK HELPERS (PHASE 2 PREP)
# ==========================================
def get_upcoming_classes():
    """Fetches all future Academic classes/exams for the Dashboard."""
    schedule = load_schedule()
    now = datetime.now()
    
    upcoming = []
    for e in schedule:
        if e.get('item_type') != 'task':
            try:
                event_dt = datetime.strptime(f"{e['date']} {e['time']}", "%Y-%m-%d %H:%M")
                if event_dt >= now:
                    upcoming.append(e)
            except ValueError:
                pass # Skips badly formatted old data
                
    return sorted(upcoming, key=lambda x: datetime.strptime(f"{x['date']} {x['time']}", "%Y-%m-%d %H:%M"))

def get_all_tasks():
    """Fetches all tasks/deadlines."""
    schedule = load_schedule()
    tasks = [e for e in schedule if e.get('item_type') == 'task']
    return sorted(tasks, key=lambda x: datetime.strptime(f"{x['date']} {x['time']}", "%Y-%m-%d %H:%M"))

def toggle_task_status(date, time_str, task_name):
    """Switches a task between 'pending' and 'completed'."""
    schedule = load_schedule()
    for e in schedule:
        if e.get('item_type') == 'task' and e['date'] == date and e['time'] == time_str and e['task'] == task_name:
            e['status'] = 'completed' if e.get('status') == 'pending' else 'pending'
            break
    save_schedule(schedule)