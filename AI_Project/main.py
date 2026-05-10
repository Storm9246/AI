import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime, timedelta

import database 
import ai_engine
import gui  # Imports all your visual components from gui.py

# ==========================================
# 1. VIEW SWITCHERS & DASHBOARDS
# ==========================================
def switch_view(view_name):
    gui.top_frame.pack_forget() 
    gui.task_view_frame.pack_forget() 
    gui.dash_view_frame.pack_forget() 
    gui.settings_view_frame.pack_forget() # NEW
    gui.ai_frame.pack_forget() 
    
    if view_name == "og":
        gui.ai_frame.pack(fill="x", padx=30, pady=10, before=gui.btn_toggle_manual)
        gui.top_frame.pack(pady=20, fill="x", padx=20, before=gui.ai_frame)
    elif view_name == "tasks":
        gui.task_view_frame.pack(pady=20, fill="both", expand=True, padx=20, before=gui.btn_toggle_manual)
        refresh_task_manager() 
    elif view_name == "dash":
        gui.dash_view_frame.pack(pady=20, fill="both", expand=True, padx=20, before=gui.btn_toggle_manual)
        refresh_grand_dashboard() 
    elif view_name == "settings": # NEW
        gui.settings_view_frame.pack(pady=20, fill="both", expand=True, padx=20, before=gui.btn_toggle_manual)
        refresh_settings()

def refresh_task_manager():
    """Wipes the task screen and rebuilds it into chronological categories."""
    for widget in gui.task_scroll.winfo_children():
        widget.destroy()

    tasks = database.get_all_tasks()
    if not tasks:
        ctk.CTkLabel(gui.task_scroll, text="No tasks found! You're all caught up. 🎉", font=("Segoe UI", 16)).pack(pady=20)
        return

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    end_of_week = now + timedelta(days=7)

    today_tasks, week_tasks, later_tasks = [], [], []

    # Sort tasks into the three buckets
    for task in tasks:
        try:
            t_date = datetime.strptime(task['date'], "%Y-%m-%d")
            # Overdue or Due Today
            if task['date'] == today_str or (t_date < now and task.get('status') != 'completed'):
                today_tasks.append(task)
            # Due in the next 7 days
            elif now <= t_date <= end_of_week:
                week_tasks.append(task)
            # Due later
            else:
                later_tasks.append(task)
        except Exception:
            later_tasks.append(task) # Fallback for bad data

    # Helper function to build each UI section cleanly
    def build_task_section(title, task_list, header_color):
        if not task_list: 
            return
            
        ctk.CTkLabel(gui.task_scroll, text=title, font=("Segoe UI", 16, "bold"), text_color=header_color).pack(anchor="w", pady=(15, 5), padx=5)
        
        for task in task_list:
            try:
                deadline = datetime.strptime(f"{task['date']} {task['time']}", "%Y-%m-%d %H:%M")
                is_overdue = deadline < now and task.get('status') != 'completed'
            except:
                is_overdue = False

            text_color = "#ff4c4c" if is_overdue else "white"
            task_text = f"[{task['category']}] {task['task']} - Due: {task['date']} @ {task['time']}"
            is_done = task.get('status') == 'completed'

            def toggle_wrapper(d=task['date'], t=task['time'], n=task['task']):
                database.toggle_task_status(d, t, n)
                refresh_task_manager() 

            cb = ctk.CTkCheckBox(gui.task_scroll, text=task_text, text_color=text_color, 
                                 font=("Segoe UI", 14, "overstrike" if is_done else "normal"), 
                                 command=toggle_wrapper)
            if is_done:
                cb.select()
            cb.pack(anchor="w", pady=5, padx=15)

    # Render the buckets
    build_task_section("🚨 Today & Overdue", today_tasks, "#ff4c4c")
    build_task_section("📅 This Week", week_tasks, "#3b8ed0")
    build_task_section("⏳ Later", later_tasks, "#a0a0a0")

def refresh_grand_dashboard(*args):
    """Rebuilds the dashboard with Smart Search and Inline Delete Buttons."""
    for widget in gui.dash_scroll.winfo_children():
        widget.destroy()

    upcoming = database.get_upcoming_classes()
    search_query = gui.dash_search_var.get().lower().strip()

    if search_query:
        filtered_upcoming = []
        for e in upcoming:
            search_string = f"{e['task']} {e.get('location', '')} {e['category']} {e['date']}".lower()
            if search_query in search_string:
                filtered_upcoming.append(e)
        upcoming = filtered_upcoming

    if not upcoming:
        ctk.CTkLabel(gui.dash_scroll, text="No matches found!", font=("Segoe UI", 16)).pack(pady=20)
        return

    for e in upcoming:
        row_frame = ctk.CTkFrame(gui.dash_scroll, fg_color="transparent")
        row_frame.pack(fill="x", pady=2, padx=10)
        
        display_str = f"📅 {e['date']} | 🕒 {e['time']} ({e.get('duration_mins', 60)}m) | {e['task']} (Loc: {e.get('location', 'TBD')}) [{e['category']}]"
        lbl_color = "#d68910" if e['category'] == "Exam" else "white"
        
        # Left side: The Class Info
        ctk.CTkLabel(row_frame, text=display_str, font=("Segoe UI", 15), text_color=lbl_color, anchor="w").pack(side="left")
        
        # Right side: The Delete Button
        def delete_wrapper(d=e['date'], t=e['time'], n=e['task']):
            database.delete_event(d, t, n)
            refresh_grand_dashboard() # Instantly refresh dashboard
            paint_calendar() # Keep calendar colors synced
            
        btn_del = ctk.CTkButton(row_frame, text="❌", width=30, fg_color="transparent", hover_color="#c93434", command=delete_wrapper)
        btn_del.pack(side="right")

def refresh_settings():
    """Loads the config.json into the UI boxes."""
    config = database.load_config()
    
    # Fill text boxes
    gui.set_acad_start.delete(0, tk.END)
    gui.set_acad_start.insert(0, config["academic_start"])
    gui.set_acad_end.delete(0, tk.END)
    gui.set_acad_end.insert(0, config["academic_end"])

    # Check the right boxes (0=Mon, 6=Sun)
    for i, var in enumerate(gui.chk_days):
        var.set(1 if i in config["weekends"] else 0)

    # Load Active Sick/Off Days
    for widget in gui.settings_off_scroll.winfo_children():
        widget.destroy()

    schedule = database.load_schedule()
    off_days = [e for e in schedule if e.get("action") == "clear_day"]

    if not off_days:
        ctk.CTkLabel(gui.settings_off_scroll, text="No off days currently active.", font=("Segoe UI", 14, "italic")).pack(pady=10)
    else:
        for e in off_days:
            row = ctk.CTkFrame(gui.settings_off_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(row, text=f"🗓️ {e['date']} - {e.get('task', 'Off Day')}", font=("Segoe UI", 15)).pack(side="left")
            
            def del_off(d=e['date'], t=e['time'], n=e['task']):
                database.delete_event(d, t, n)
                refresh_settings() # Refresh list
                paint_calendar()   # Remove red color from calendar instantly
                
            ctk.CTkButton(row, text="❌ Remove", width=60, fg_color="#c93434", hover_color="#852121", command=del_off).pack(side="right")

def save_settings():
    """Reads the UI boxes and writes to config.json."""
    start = gui.set_acad_start.get().strip()
    end = gui.set_acad_end.get().strip()
    weekends = [i for i, var in enumerate(gui.chk_days) if var.get() == 1]

    # Validate Time Format
    try:
        datetime.strptime(start, "%H:%M")
        datetime.strptime(end, "%H:%M")
    except ValueError:
        gui.status_label.configure(text="Status: Invalid Time! Use HH:MM (e.g. 08:00)", text_color="red")
        return

    config = {
        "academic_start": start,
        "academic_end": end,
        "weekends": weekends
    }
    database.save_config(config)
    gui.status_label.configure(text="Status: Settings Saved Successfully!", text_color="#2fa572")

# ==========================================
# 2. CORE LOGIC (CALENDAR & SCHEDULING)
# ==========================================
def view_schedule(*args): 
    formatted_date = gui.cal.selection_get().strftime("%Y-%m-%d")
    gui.date_label.configure(text=f"Schedule for: {formatted_date}")
    
    gui.schedule_listbox.delete(0, tk.END)
    schedule = database.load_schedule()
    events_today = [e for e in schedule if e.get("date") == formatted_date and e.get("action") != "clear_day"]
    events_today = sorted(events_today, key=lambda x: x['time'])
    
    if not events_today:
        gui.schedule_listbox.insert(tk.END, " No events scheduled for this day.")
    else:
        for e in events_today:
            if e.get('item_type') == 'task':
                display_str = f"🚨 {e['time']} | {e['task']} [{e.get('category', 'Task')}]"
            else:
                duration = e.get('duration_mins', 60)
                location = e.get('location', 'TBD') 
                display_str = f"🕒 {e['time']} ({duration}m) | {e['task']} (Loc: {location}) [{e.get('category')}]"
            gui.schedule_listbox.insert(tk.END, display_str)
            
    switch_view("og")
    paint_calendar()

def paint_calendar():
    gui.cal.calevent_remove('all')
    schedule = database.load_schedule()
    for e in schedule:
        if e.get('action') == 'clear_day':
            try:
                dt = datetime.strptime(e['date'], "%Y-%m-%d").date()
                gui.cal.calevent_create(dt, "Off Day", "off_day")
            except:
                pass
            
    gui.cal.tag_config("off_day", background="#c93434", foreground="white") 
    gui.cal.tag_config("current_day", background="#2fa572", foreground="white")
    gui.cal.calevent_create(datetime.now().date(), "Today", "current_day")

def generate_recurring_events(data):
    events = []
    recur_type = data.get('recur_type', 'none')
    recur_until = data.get('recur_until', '')
    events.append(data.copy())
    
    if recur_type in ['daily', 'weekly'] and recur_until:
        try:
            curr_date = datetime.strptime(data['date'], "%Y-%m-%d")
            end_date = datetime.strptime(recur_until, "%Y-%m-%d")
            delta = timedelta(days=1 if recur_type == 'daily' else 7)
            
            curr_date += delta
            while curr_date <= end_date:
                new_data = data.copy()
                new_data['date'] = curr_date.strftime("%Y-%m-%d")
                new_data['recur_type'] = 'none' 
                events.append(new_data)
                curr_date += delta
        except Exception:
            pass
    return events

def process_and_save_event(data):
    task = data['task']
    cat = data.get('category', 'Academic')
    duration = data.get('duration_mins', 60) 
    is_flexible = data.get('is_flexible', True) 
    item_type = data.get('item_type', 'event')
    
    original_time = data['time']
    date = data['date']

    if database.is_duplicate(date, original_time, task):
        return False 
        
    if item_type == 'task' or data.get('action') == 'clear_day':
        if 'status' not in data and item_type == 'task':
            data['status'] = 'pending'
        database.add_event(data)
        return True 
    
    resolved = False
    while not resolved:
        original_time = data['time']
        date = data['date']

        conflict_msg = database.check_conflict(date, original_time, duration)
        rule_msg = database.is_outside_context_window(date, original_time, cat)

        if conflict_msg or rule_msg:
            display_msg = conflict_msg if conflict_msg else rule_msg
            all_slots = database.get_all_available_slots(date, duration, cat, original_time)
            
            dialog = gui.ConflictDialog(gui.root, date, original_time, cat, duration, all_slots, is_flexible, task, display_msg)
            gui.root.wait_window(dialog) 
            
            choice = dialog.result_action
            
            if choice is None:
                return False 
            elif choice == "FORCE":
                resolved = True 
            elif choice == "OVERWRITE":
                database.delete_event_at_time(date, original_time)
                resolved = True
            elif choice == "NEXT_DAY":
                current_date_obj = datetime.strptime(date, "%Y-%m-%d")
                next_day_obj = current_date_obj + timedelta(days=1)
                while database.check_conflict(next_day_obj.strftime("%Y-%m-%d"), original_time, duration):
                    next_day_obj += timedelta(days=1)
                data['date'] = next_day_obj.strftime("%Y-%m-%d")
            else:
                data['time'] = choice 
        else:
            resolved = True

    database.add_event(data)
    return True

# ==========================================
# 3. INTERFACE HANDLERS
# ==========================================
def ask_ai():
    user_text = gui.command_entry.get()
    if not user_text.strip():
        gui.status_label.configure(text="Status: Please type a command first!", text_color="red")
        return

    gui.status_label.configure(text="Status: AI is calculating dates & thinking...", text_color="#3b8ed0")
    gui.root.update() 

    data_list, error = ai_engine.process_command(user_text)

    if error:
        gui.status_label.configure(text=f"Status: AI Error! \n({error})", text_color="red")
        return
        
    events_added = 0
    for data in data_list:
        action = data.get('action', 'schedule')
        expanded_events = generate_recurring_events(data)
        
        for ev in expanded_events:
            if action == "clear_day":
                database.clear_category_for_day(ev['date'], "Academic") 
                database.add_event(ev) 
                events_added += 1
            else:
                if process_and_save_event(ev):
                    events_added += 1
    
    gui.status_label.configure(text=f"Status: Successfully added {events_added} new event(s)!", text_color="#2fa572")
    gui.command_entry.delete(0, tk.END)
    
    if data_list and data_list[0].get('date'):
        target_date = datetime.strptime(data_list[0]['date'], "%Y-%m-%d").date()
        gui.cal.selection_set(target_date)
        view_schedule()

def toggle_manual_panel():
    if gui.manual_panel.winfo_ismapped():
        gui.manual_panel.pack_forget()
    else:
        gui.manual_date.delete(0, tk.END)
        gui.manual_date.insert(0, gui.cal.selection_get().strftime("%Y-%m-%d"))
        gui.manual_panel.pack(fill="x", padx=30, pady=10, after=gui.btn_toggle_manual)

def add_manually():
    task, time, cat, loc = gui.manual_task.get(), gui.manual_time.get(), gui.manual_cat.get(), gui.manual_loc.get() 
    date = gui.manual_date.get()
    recur_type = gui.manual_recur.get().lower()
    recur_until = gui.manual_end_date.get()
    
    is_task = (gui.manual_type_var.get() == "Task (Deadline)")
    item_type = "task" if is_task else "event"
    duration = 0 if is_task else 60 
    
    if not loc.strip(): 
        loc = "TBD" 
    
    if not task or not time or not date:
        gui.status_label.configure(text="Status: Fill Title, Date, and Time!", text_color="red")
        return
        
    data = {
        "task": task, "date": date, "time": time, 
        "category": cat, "duration_mins": duration, 
        "is_flexible": False, "location": loc,
        "item_type": item_type, "recur_type": recur_type, "recur_until": recur_until
    }
    
    expanded = generate_recurring_events(data)
    for ev in expanded:
        process_and_save_event(ev)
        
    gui.status_label.configure(text=f"Status: Saved {len(expanded)} event(s)!", text_color="#2fa572")
    view_schedule()
    toggle_manual_panel()

def get_briefing():
    selected_date = gui.cal.selection_get().strftime("%Y-%m-%d")
    events = database.get_events_for_date(selected_date)
    
    gui.status_label.configure(text="Status: AI is analyzing your day...", text_color="#3b8ed0")
    gui.root.update()
    
    briefing, error = ai_engine.generate_daily_briefing(selected_date, events)
    if error:
        messagebox.showerror("AI Error", f"Failed to generate briefing:\n{error}")
        gui.status_label.configure(text="Status: Ready", text_color="gray")
    else:
        messagebox.showinfo(f"SAPSA Briefing - {selected_date}", briefing)
        gui.status_label.configure(text="Status: Briefing generated!", text_color="#2fa572")
    
def delete_gui_event():
    selected = gui.schedule_listbox.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Please select an event to delete.")
        return
    
    item_text = gui.schedule_listbox.get(selected[0])
    if "No events" in item_text:
        return

    if "🚨" in item_text:
        parts = item_text.replace("🚨 ", "").split(" | ")
        event_time = parts[0].strip()
        event_task = parts[1].split(" [")[0].strip()
    else:
        parts = item_text.replace("🕒 ", "").split(" | ")
        event_time = parts[0].split(" ")[0].strip() 
        event_task = parts[1].split(" (Loc:")[0].strip() 
        
    selected_date = gui.cal.selection_get().strftime("%Y-%m-%d")
    database.delete_event(selected_date, event_time, event_task)
    gui.status_label.configure(text="Status: Event deleted.", text_color="#2fa572")
    view_schedule()

def exit_app():
    gui.root.destroy()

# ==========================================
# PREDICTIVE TEMPLATE ENGINE
# ==========================================
# ==========================================
# PREDICTIVE TEMPLATE ENGINE
# ==========================================
TEMPLATES = [
    # --- LEVEL 1: THE BASICS (SINGLE EVENTS) ---
    "Schedule [Class] tomorrow at [Time] for [Duration] mins.",
    "Add [Class] today at [Time] in [Location].",
    "Book a [Duration] min meeting for [Class] on [YYYY-MM-DD] at [Time].",
    "I have [Class] on [Day] at [Time] in room [Location].",
    "Set up a study session for [Class] at [Time].",
    "Add a personal event called [Event Name] tonight at [Time].",
    
    # --- LEVEL 2: TASKS & DEADLINES ---
    "Add a task called [Task Name] due on [YYYY-MM-DD] at [Time].",
    "Remind me to [Task Name] by [Time] tomorrow.",
    "Set a deadline for [Task Name] on [Day] at [Time].",
    "Add a project milestone [Task Name] due next [Day] at [Time].",
    "Create a task [Task Name] due today at [Time].",

    # --- LEVEL 3: RECURRENCE & ROUTINES ---
    "Schedule [Class] every [Day] at [Time] until [YYYY-MM-DD].",
    "Book [Class] every [Day] and [Day] at [Time].",
    "Add a weekly [Task/Event] every [Day] until [YYYY-MM-DD].",
    "Set up a daily review session at [Time] until [YYYY-MM-DD].",
    "Schedule [Class] every [Day] at [Time] in [Location] for [Duration] mins.",

    # --- LEVEL 4: BATCHING (MULTIPLE SAME-DAY / DIFFERENT DAYS) ---
    "Add [Class A] at [Time A] and [Class B] at [Time B] for tomorrow.",
    "Schedule [Class A], [Class B], and [Class C] on [Day] at [Time 1], [Time 2], and [Time 3].",
    "Book [Class A] on [Day 1] and [Class B] on [Day 2] at [Time].",
    "Add a task [Task A] and task [Task B] both due on [YYYY-MM-DD].",
    
    # --- LEVEL 5: THE "RESPECTIVELY" LEGENDS ---
    "Add [Class A], [Class B], and [Class C] on [Day 1], [Day 2], and [Day 3] at [Time 1], [Time 2], and [Time 3] respectively.",
    "Schedule [Class 1] and [Class 2] at [Time 1] and [Time 2] in [Loc 1] and [Loc 2] respectively.",
    "Add [Class A], [Class B], and [Class C] on [Day] at [Time 1], [Time 2], and [Time 3] in [Loc 1], [Loc 2], and [Loc 3] respectively.",
    "Book [Class 1] and [Class 2] on [Day 1] and [Day 2] respectively, both at [Time].",

    # --- LEVEL 6: AUTOMATION & SICK DAYS ---
    "Mark every [Day] this month as an Off Day.",
    "Mark [YYYY-MM-DD] and [YYYY-MM-DD] as Sick Days.",
    "Clear my schedule completely for [YYYY-MM-DD].",
    "Set tomorrow as a Sick Day.",
    "Mark next [Day] as an Off Day.",
    
    # --- LEVEL 7: HYBRID (TASKS + EVENTS) ---
    "Schedule [Class] at [Time] and add a task [Task] due at [Time].",
    "Add [Class] on [Day] at [Time] and remind me to [Task] by [Time].",
    "Book [Class] tomorrow at [Time] and add a project deadline [Task] on [Date].",
    "Set [Class] for [Day] at [Time], also set [Task] due the same day at [Time].",
    
    # --- LEVEL 8: EXAMS & QUIZZES ---
    "Schedule a [Class] Exam on [YYYY-MM-DD] at [Time] in [Location].",
    "Add a [Duration] min [Class] Quiz tomorrow at [Time]."
]

def handle_typing(event):
    """Fires every time a key is pressed to filter templates."""
    # Ignore keys used for navigation and deletion
    if event.keysym in ['Up', 'Down', 'Return', 'Tab', 'Control_L', 'Control_R', 'BackSpace']: 
        return

    typed = gui.command_entry.get().lower()
    if not typed:
        gui.suggestion_box.place_forget()
        return

    # Fuzzy match: Find templates that contain the typed letters (Max 6 results now)
    matches = [t for t in TEMPLATES if typed in t.lower()][:6]

    if matches:
        gui.suggestion_box.delete(0, tk.END)
        for m in matches:
            gui.suggestion_box.insert(tk.END, m)
            
        x_pos = gui.command_entry.winfo_rootx() - gui.root.winfo_rootx()
        y_pos = gui.command_entry.winfo_rooty() - gui.root.winfo_rooty() + gui.command_entry.winfo_height()
        
        gui.suggestion_box.place(x=x_pos, y=y_pos, width=gui.command_entry.winfo_width(), height=len(matches) * 25)
        gui.suggestion_box.lift()
        
        # Auto-highlight the top item so 'Enter' grabs it immediately
        gui.suggestion_box.selection_clear(0, tk.END)
        gui.suggestion_box.selection_set(0)
    else:
        gui.suggestion_box.place_forget()

def navigate_suggestions(event):
    """Allows arrow keys to scroll through the dropdown box."""
    if not gui.suggestion_box.winfo_ismapped():
        return
        
    size = gui.suggestion_box.size()
    if size == 0: return

    sel = gui.suggestion_box.curselection()
    current_idx = sel[0] if sel else 0

    if event.keysym == 'Up':
        next_idx = max(0, current_idx - 1)
    elif event.keysym == 'Down':
        next_idx = min(size - 1, current_idx + 1)
            
    gui.suggestion_box.selection_clear(0, tk.END)
    gui.suggestion_box.selection_set(next_idx)
    gui.suggestion_box.activate(next_idx)
    return 'break' # Prevents cursor from jumping in the text box

def custom_ctrl_backspace(event):
    """Custom macro to delete whole words or [Bracketed] templates."""
    cursor_pos = gui.command_entry.index(tk.INSERT)
    text = gui.command_entry.get()[:cursor_pos]
    
    if not text: return 'break'

    i = cursor_pos - 1
    # 1. Skip trailing spaces
    while i >= 0 and text[i] == ' ':
        i -= 1
        
    # 2. Skip letters until we hit a space or an opening bracket '['
    while i >= 0 and text[i] not in [' ', '[']:
        i -= 1
        
    # 3. If we stopped on an opening bracket '[', delete that bracket too
    if i >= 0 and text[i] == '[':
        i -= 1 
        
    delete_start = i + 1
    gui.command_entry.delete(delete_start, cursor_pos)
    
    # Manually trigger the typing handler so the dropdown updates!
    handle_typing(event)
    return 'break'

def accept_suggestion(event):
    """Fires when Tab or Enter is pressed to auto-fill the text."""
    if gui.suggestion_box.winfo_ismapped():
        selection = gui.suggestion_box.curselection()
        selected_text = gui.suggestion_box.get(selection[0]) if selection else gui.suggestion_box.get(0)
        
        gui.command_entry.delete(0, tk.END)
        gui.command_entry.insert(0, selected_text)
        gui.suggestion_box.place_forget()
        return 'break'

def hide_suggestions(event):
    """Hides the box if you click somewhere else."""
    gui.suggestion_box.place_forget()

# ==========================================
# 4. INITIALIZATION & COMMAND HOOKUPS
# ==========================================
gui.btn_ask.configure(command=ask_ai)
gui.btn_man_save.configure(command=add_manually)
gui.btn_toggle_manual.configure(command=toggle_manual_panel)
gui.btn_og.configure(command=lambda: switch_view("og"))
gui.btn_tasks.configure(command=lambda: switch_view("tasks"))
gui.btn_dash.configure(command=lambda: switch_view("dash"))
gui.btn_delete.configure(command=delete_gui_event)
gui.btn_briefing.configure(command=get_briefing)
gui.btn_exit.configure(command=exit_app)
gui.cal.bind("<<CalendarSelected>>", view_schedule)
gui.command_entry.bind('<KeyRelease>', handle_typing)
gui.command_entry.bind('<Tab>', accept_suggestion)
gui.command_entry.bind('<Up>', navigate_suggestions)
gui.command_entry.bind('<Down>', navigate_suggestions)
gui.command_entry.bind('<Control-BackSpace>', custom_ctrl_backspace)
gui.command_entry.bind('<Return>', lambda e: accept_suggestion(e) if gui.suggestion_box.winfo_ismapped() else ask_ai())
gui.root.bind('<Button-1>', hide_suggestions)
# Tells Python to fire the refresh function the millisecond a character is typed or deleted!
gui.dash_search_var.trace_add("write", refresh_grand_dashboard)
gui.btn_settings.configure(command=lambda: switch_view("settings"))
gui.btn_save_settings.configure(command=save_settings)


paint_calendar()
view_schedule() 
gui.root.mainloop()