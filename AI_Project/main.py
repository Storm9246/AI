import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import ai_engine
import database 
import customtkinter as ctk 
from datetime import datetime, timedelta

class ConflictDialog(ctk.CTkToplevel):
    def __init__(self, master, date, original_time, category, duration, all_slots, is_flexible, task_name, conflict_reason):
        super().__init__(master)
        self.title("🚨 SAPSA Conflict Resolution")
        self.geometry("520x600")
        self.attributes("-topmost", True)
        self.grab_set() 

        self.result_action = None 
        self.grid_columnconfigure(0, weight=1)

        # Top Warning Header (Now uses the exact reason from the database!)
        ctk.CTkLabel(self, text=f"Conflict: {task_name}", font=("Segoe UI", 22, "bold"), text_color="#c93434").grid(row=0, column=0, pady=(20, 5))
        ctk.CTkLabel(self, text=f"🚨 {conflict_reason}", font=("Segoe UI", 16, "bold"), text_color="#d68910", wraplength=450).grid(row=1, column=0, pady=(0, 20))

        # 1. The "Smart Suggestion" Panel
        if all_slots:
            orig_dt = datetime.strptime(original_time, "%H:%M")
            recommended = min(all_slots, key=lambda slot: abs((datetime.strptime(slot, "%H:%M") - orig_dt).total_seconds()))
        else:
            recommended = None

        if recommended:
            rec_frame = ctk.CTkFrame(self, fg_color="#1f538d", corner_radius=10)
            rec_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
            ctk.CTkLabel(rec_frame, text="💡 Smart Suggestion", font=("Segoe UI", 15, "bold")).pack(pady=(10, 0))
            ctk.CTkLabel(rec_frame, text=f"Closest free {category} slot: {recommended}").pack(pady=5)
            ctk.CTkButton(rec_frame, text=f"Accept {recommended}", fg_color="#2fa572", hover_color="#248058", command=lambda: self.close_with(recommended)).pack(pady=10)

        # 2. The Slider/Dropdown Panel
        drop_frame = ctk.CTkFrame(self, corner_radius=10)
        drop_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(drop_frame, text="🔍 Browse All Free Slots", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        
        self.slot_var = ctk.StringVar(value=all_slots[0] if all_slots else "No slots available")
        self.dropdown = ctk.CTkComboBox(drop_frame, values=all_slots if all_slots else ["None"], variable=self.slot_var, width=200)
        self.dropdown.pack(pady=5)
        ctk.CTkButton(drop_frame, text="Select This Slot", command=lambda: self.close_with(self.slot_var.get())).pack(pady=10)

        # 3. Action Buttons
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure((0, 1), weight=1)
        
        btn_overwrite = ctk.CTkButton(action_frame, text="🗑️ Replace Conflicting Event", fg_color="#d68910", hover_color="#b3710d", command=lambda: self.close_with("OVERWRITE"))
        btn_overwrite.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        btn_next = ctk.CTkButton(action_frame, text="⏭️ Find Next Free Day", command=lambda: self.close_with("NEXT_DAY"))
        btn_next.grid(row=1, column=0, sticky="ew", padx=(0, 5))

        force_color = "#c93434" if not is_flexible else "#b08d5c"
        btn_force = ctk.CTkButton(action_frame, text="⚠️ Stack (Ignore Rules)", fg_color=force_color, hover_color="#852121", command=lambda: self.close_with("FORCE"))
        btn_force.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        # 4. The Hover Info Bar 
        self.info_label = ctk.CTkLabel(self, text="Hover over an action to see what it does.", font=("Segoe UI", 12, "italic"), text_color="gray")
        self.info_label.grid(row=5, column=0, pady=(0, 10))

        # Bind hover events to update the text!
        btn_overwrite.bind("<Enter>", lambda e: self.info_label.configure(text="Deletes the blocking event and schedules this one instead."))
        btn_overwrite.bind("<Leave>", lambda e: self.info_label.configure(text="Hover over an action to see what it does."))
        
        btn_next.bind("<Enter>", lambda e: self.info_label.configure(text="Skips blocked days and finds the exact next day this time slot is open."))
        btn_next.bind("<Leave>", lambda e: self.info_label.configure(text="Hover over an action to see what it does."))
        
        btn_force.bind("<Enter>", lambda e: self.info_label.configure(text="Forces the event to save here, even if it overlaps or breaks rules."))
        btn_force.bind("<Leave>", lambda e: self.info_label.configure(text="Hover over an action to see what it does."))

    def close_with(self, choice):
        if choice == "None" or choice == "No slots available":
            return
        self.result_action = choice
        self.destroy()

# ==========================================
# STAGE 2: THE VIEW SWITCHER (NEW)
# ==========================================
def switch_view(view_name):
    """Hides all frames and only shows the one requested."""
    top_frame.pack_forget() 
    task_view_frame.pack_forget() 
    dash_view_frame.pack_forget() 
    
    # We use 'before=ai_frame' so the views always stay at the top of the app!
    if view_name == "og":
        top_frame.pack(pady=20, fill="x", padx=20, before=ai_frame)
    elif view_name == "tasks":
        task_view_frame.pack(pady=20, fill="both", expand=True, padx=20, before=ai_frame)
        refresh_task_manager()  # <--- STAGE 3 TRIGGER
    elif view_name == "dash":
        dash_view_frame.pack(pady=20, fill="both", expand=True, padx=20, before=ai_frame)
        refresh_grand_dashboard()  # <--- STAGE 3 TRIGGER

# ==========================================
# STAGE 3: THE DYNAMIC DASHBOARDS (NEW)
# ==========================================
def refresh_task_manager():
    """Wipes the task screen and rebuilds it with fresh checkboxes."""
    for widget in task_scroll.winfo_children():
        widget.destroy()

    tasks = database.get_all_tasks()
    if not tasks:
        ctk.CTkLabel(task_scroll, text="No tasks found! You're all caught up. 🎉", font=("Segoe UI", 16)).pack(pady=20)
        return

    now = datetime.now()
    for task in tasks:
        # Check if overdue
        try:
            deadline = datetime.strptime(f"{task['date']} {task['time']}", "%Y-%m-%d %H:%M")
            is_overdue = deadline < now and task.get('status') != 'completed'
        except:
            is_overdue = False

        # Turn overdue items RED
        text_color = "#ff4c4c" if is_overdue else "white"
        task_text = f"[{task['category']}] {task['task']} - Due: {task['date']} @ {task['time']}"
        is_done = task.get('status') == 'completed'

        # The magic wrapper to toggle status and refresh instantly
        def toggle_wrapper(d=task['date'], t=task['time'], n=task['task']):
            database.toggle_task_status(d, t, n)
            refresh_task_manager() 

        cb = ctk.CTkCheckBox(task_scroll, text=task_text, text_color=text_color, 
                             font=("Segoe UI", 14, "overstrike" if is_done else "normal"), 
                             command=toggle_wrapper)
        if is_done:
            cb.select()

        cb.pack(anchor="w", pady=8, padx=10)

def refresh_grand_dashboard():
    """Wipes the dashboard and builds a chronological list of future classes."""
    for widget in dash_scroll.winfo_children():
        widget.destroy()

    upcoming = database.get_upcoming_classes()
    if not upcoming:
        ctk.CTkLabel(dash_scroll, text="No upcoming classes found!", font=("Segoe UI", 16)).pack(pady=20)
        return

    for e in upcoming:
        display_str = f"📅 {e['date']} | 🕒 {e['time']} ({e.get('duration_mins', 60)}m) | {e['task']} (Loc: {e.get('location', 'TBD')}) [{e['category']}]"
        # Alternate colors based on category to make it look cool
        lbl_color = "#d68910" if e['category'] == "Exam" else "white"
        ctk.CTkLabel(dash_scroll, text=display_str, font=("Segoe UI", 15), text_color=lbl_color, anchor="w").pack(fill="x", pady=5, padx=10)

# ==========================================
# 1. EVENT HANDLERS 
# ==========================================
def view_schedule(*args): 
    formatted_date = cal.selection_get().strftime("%Y-%m-%d")
    date_label.configure(text=f"Schedule for: {formatted_date}")
    
    schedule_listbox.delete(0, tk.END)
    schedule = database.load_schedule()
    events_today = [e for e in schedule if e.get("date") == formatted_date]
    events_today = sorted(events_today, key=lambda x: x['time'])
    
    if not events_today:
        schedule_listbox.insert(tk.END, " No events scheduled for this day.")
    else:
        for e in events_today:
            duration = e.get('duration_mins', 60)
            location = e.get('location', 'TBD') 
            
            display_str = f"🕒 {e['time']} ({duration}m) | {e['task']} (Loc: {location}) [{e['category']}]"
            schedule_listbox.insert(tk.END, display_str)
            
    # NEW: Snap back to the OG view automatically when a date is clicked!
    switch_view("og")

# ==========================================
# THE UNIVERSAL EVENT HANDLER
# ==========================================
def process_and_save_event(data):
    task = data['task']
    cat = data['category']
    duration = data.get('duration_mins', 60) 
    is_flexible = data.get('is_flexible', True) 
    item_type = data.get('item_type', 'event')
    
    original_time = data['time']
    date = data['date']

    if database.is_duplicate(date, original_time, task):
        return False 
        
    # TASK BYPASS
    if item_type == 'task':
        if 'status' not in data:
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
            all_slots = database.get_all_available_slots(date, duration, cat)
            
            dialog = ConflictDialog(root, date, original_time, cat, duration, all_slots, is_flexible, task, display_msg)
            root.wait_window(dialog) 
            
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

def ask_ai():
    user_text = command_entry.get()
    if not user_text.strip():
        status_label.configure(text="Status: Please type a command first!", text_color="red")
        return

    status_label.configure(text="Status: AI is calculating dates & thinking...", text_color="#3b8ed0")
    root.update() 

    data_list, error = ai_engine.process_command(user_text)

    if error:
        status_label.configure(text=f"Status: AI Error! \n({error})", text_color="red")
        return
        
    events_added = 0
    
    for data in data_list:
        action = data.get('action', 'schedule')
        
        if action == "clear_day":
            target_date = data.get('date')
            target_cat = data.get('target_category', 'All')
            database.clear_category_for_day(target_date, target_cat)
            status_label.configure(text=f"Status: Wiped {target_cat} schedule for {target_date}.", text_color="#2fa572")
            continue 
            
        if process_and_save_event(data):
            events_added += 1
    
    status_label.configure(text=f"Status: Successfully added {events_added} new event(s)!", text_color="#2fa572")
    command_entry.delete(0, tk.END)
    
    if data_list and data_list[0].get('date'):
        target_date = datetime.strptime(data_list[0]['date'], "%Y-%m-%d").date()
        cal.selection_set(target_date)
        view_schedule()


def add_manually():
    task = manual_task.get()
    time = manual_time.get()
    cat = manual_cat.get()
    loc = manual_loc.get() 
    date = cal.selection_get().strftime("%Y-%m-%d")
    
    is_task = (manual_type_var.get() == "Task (Deadline)")
    item_type = "task" if is_task else "event"
    duration = 0 if is_task else 60 
    
    if not loc.strip(): 
        loc = "TBD" 
    
    if not task or not time:
        status_label.configure(text="Status: Fill all manual fields!", text_color="red")
        return
        
    try:
        req_time_obj = datetime.strptime(time, "%H:%M")
    except ValueError:
        messagebox.showerror("Time Format Error", "Please enter the time in 24-hour format (e.g., 14:00).")
        return

    now = datetime.now()
    if date == now.strftime("%Y-%m-%d") and req_time_obj.time() < now.time():
        tomorrow_obj = now + timedelta(days=1)
        date = tomorrow_obj.strftime("%Y-%m-%d")
        messagebox.showinfo("Time Travel", f"That time has already passed today!\n\nSAPSA automatically moved '{task}' to tomorrow ({date}).")
        cal.selection_set(tomorrow_obj.date())

    data = {
        "task": task, "date": date, "time": time, 
        "category": cat, "duration_mins": duration, 
        "is_flexible": False, "location": loc,
        "item_type": item_type
    }
    
    if process_and_save_event(data):
        status_label.configure(text="Status: Event added manually.", text_color="#2fa572")
        manual_task.delete(0, tk.END)
        manual_time.delete(0, tk.END)
        manual_loc.delete(0, tk.END) 
        view_schedule()
        toggle_manual_panel()

def get_briefing():
    selected_date = cal.selection_get().strftime("%Y-%m-%d")
    events = database.get_events_for_date(selected_date)
    
    status_label.configure(text="Status: AI is analyzing your day...", text_color="#3b8ed0")
    root.update()
    
    briefing, error = ai_engine.generate_daily_briefing(selected_date, events)
    
    if error:
        messagebox.showerror("AI Error", f"Failed to generate briefing:\n{error}")
        status_label.configure(text="Status: Ready", text_color="gray")
    else:
        messagebox.showinfo(f"SAPSA Briefing - {selected_date}", briefing)
        status_label.configure(text="Status: Briefing generated!", text_color="#2fa572")
    
def delete_gui_event():
    selected = schedule_listbox.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Please select an event to delete.")
        return
    
    item_text = schedule_listbox.get(selected[0])
    if "No events" in item_text:
        return

    parts = item_text.replace("🕒 ", "").split(" | ")
    event_time = parts[0].split(" ")[0] 
    event_task = parts[1].split(" (Loc:")[0].strip() 
    selected_date = cal.selection_get().strftime("%Y-%m-%d")
    
    database.delete_event(selected_date, event_time, event_task)
    status_label.configure(text="Status: Event deleted.", text_color="#2fa572")
    view_schedule()

def exit_app():
    root.destroy()

# ==========================================
# 2. GUI SETUP 
# ==========================================
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

root = ctk.CTk()
root.title("SAPSA - Smart Assistant")
root.geometry("900x800")

# --- STAGE 2: THE 3 MAIN VIEW CONTAINERS ---
# --- STAGE 3: THE SCROLLABLE VIEW CONTAINERS ---
top_frame = ctk.CTkFrame(root, fg_color="transparent")
top_frame.pack(pady=20, fill="x", padx=20)

# The Task Manager Frame
task_view_frame = ctk.CTkFrame(root, corner_radius=15, fg_color="#2b2b2b")
ctk.CTkLabel(task_view_frame, text="📋 Task Manager", font=("Segoe UI", 20, "bold")).pack(pady=(10, 5))
task_scroll = ctk.CTkScrollableFrame(task_view_frame, fg_color="transparent")
task_scroll.pack(fill="both", expand=True, padx=10, pady=10)

# The Grand Dashboard Frame
dash_view_frame = ctk.CTkFrame(root, corner_radius=15, fg_color="#2b2b2b")
ctk.CTkLabel(dash_view_frame, text="🚀 Grand Dashboard (Upcoming)", font=("Segoe UI", 20, "bold")).pack(pady=(10, 5))
dash_scroll = ctk.CTkScrollableFrame(dash_view_frame, fg_color="transparent")
dash_scroll.pack(fill="both", expand=True, padx=10, pady=10)
# -------------------------------------------

today = datetime.now()

cal_frame = ctk.CTkFrame(top_frame, corner_radius=15)
cal_frame.pack(side="left", padx=10, fill="both", expand=True)

cal = Calendar(cal_frame, selectmode='day', 
               year=today.year, month=today.month, day=today.day, 
               font=("Segoe UI", 15), cursor="hand2", background="#2b2b2b", 
               foreground="white", headersbackground="#1f538d",
               selectbackground="#8e44ad") 
               
cal.pack(padx=15, pady=15, fill="both", expand=True) 
cal.bind("<<CalendarSelected>>", view_schedule) 
cal.tag_config("current_day", background="#2fa572", foreground="white")
cal.calevent_create(today.date(), "Today", "current_day")

list_frame = ctk.CTkFrame(top_frame, corner_radius=15)
list_frame.pack(side="right", fill="both", expand=True, padx=10)

date_label = ctk.CTkLabel(list_frame, text="Schedule for: ", font=("Segoe UI", 16, "bold"))
date_label.pack(pady=10)

schedule_listbox = tk.Listbox(list_frame, font=("Consolas", 12), height=10, 
                              bg="#2b2b2b", fg="white", selectbackground="#1f538d", borderwidth=0)
schedule_listbox.pack(fill="both", expand=True, padx=10, pady=5)

btn_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
btn_frame.pack(pady=10)

btn_delete = ctk.CTkButton(btn_frame, text="Delete Selected", fg_color="#c93434", hover_color="#a32a2a", command=delete_gui_event)
btn_delete.pack(side="left", padx=5)

btn_briefing = ctk.CTkButton(btn_frame, text="Generate AI Briefing", command=get_briefing)
btn_briefing.pack(side="left", padx=5)

ai_frame = ctk.CTkFrame(root, corner_radius=15)
ai_frame.pack(fill="x", padx=30, pady=10)

ctk.CTkLabel(ai_frame, text="🤖 AI Assistant", font=("Segoe UI", 16, "bold"), text_color="#3b8ed0").pack(pady=(10, 0))

ai_input_frame = ctk.CTkFrame(ai_frame, fg_color="transparent")
ai_input_frame.pack(pady=10)

command_entry = ctk.CTkEntry(ai_input_frame, font=("Segoe UI", 14), width=450, placeholder_text="e.g., Schedule a 2-hour OS lab tomorrow at 2 PM")
command_entry.pack(side="left", padx=10)

btn_ask = ctk.CTkButton(ai_input_frame, text="Ask AI", font=("Segoe UI", 14, "bold"), command=ask_ai)
btn_ask.pack(side="left")

# ==========================================
# STAGE 1 UI: SMART MANUAL ENTRY PANEL
# ==========================================
def toggle_manual_panel():
    if manual_panel.winfo_ismapped():
        manual_panel.pack_forget()
        btn_toggle_manual.configure(text="➕ Add Manually")
    else:
        manual_panel.pack(fill="x", padx=30, pady=10, after=btn_toggle_manual)
        btn_toggle_manual.configure(text="➖ Close Manual Entry")

def update_manual_ui(*args):
    if manual_type_var.get() == "Task (Deadline)":
        time_label.configure(text="Deadline Time:")
    else:
        time_label.configure(text="Start Time:")

btn_toggle_manual = ctk.CTkButton(root, text="➕ Add Manually", fg_color="transparent", border_width=2, text_color="white", hover_color="#8e44ad", command=toggle_manual_panel)
btn_toggle_manual.pack(pady=(5, 10))

manual_panel = ctk.CTkFrame(root, corner_radius=15, fg_color="#2b2b2b")

man_inner = ctk.CTkFrame(manual_panel, fg_color="transparent")
man_inner.pack(pady=15)

manual_type_var = ctk.StringVar(value="Event (Takes Time)")
manual_type_var.trace_add("write", update_manual_ui) 

ctk.CTkLabel(man_inner, text="Type:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
ctk.CTkSegmentedButton(man_inner, values=["Event (Takes Time)", "Task (Deadline)"], variable=manual_type_var, selected_color="#8e44ad").grid(row=0, column=1, columnspan=3, pady=5, sticky="ew")

ctk.CTkLabel(man_inner, text="Title:").grid(row=1, column=0, padx=5, pady=5)
manual_task = ctk.CTkEntry(man_inner, width=150)
manual_task.grid(row=1, column=1, padx=5, pady=5)

time_label = ctk.CTkLabel(man_inner, text="Start Time:")
time_label.grid(row=1, column=2, padx=5, pady=5)
manual_time = ctk.CTkEntry(man_inner, width=80, placeholder_text="14:00")
manual_time.grid(row=1, column=3, padx=5, pady=5)

ctk.CTkLabel(man_inner, text="Loc:").grid(row=1, column=4, padx=5, pady=5)
manual_loc = ctk.CTkEntry(man_inner, width=80)
manual_loc.grid(row=1, column=5, padx=5, pady=5)

ctk.CTkLabel(man_inner, text="Category:").grid(row=2, column=0, padx=5, pady=10)
manual_cat = ctk.CTkComboBox(man_inner, values=["Academic", "Self-Study", "Home Chores", "Outdoor Errands", "Project", "Exam", "Quiz", "Assignment", "Lab Task", "Personal Task"], width=150)
manual_cat.grid(row=2, column=1, columnspan=2, padx=5, pady=10, sticky="w")

btn_man = ctk.CTkButton(man_inner, text="Save to Schedule", font=("Segoe UI", 12, "bold"), fg_color="#2fa572", hover_color="#248058", command=add_manually)
btn_man.grid(row=2, column=4, columnspan=2, padx=15, pady=10)

# ==========================================
# STAGE 2 UI: NAVIGATION HUB 
# ==========================================
nav_frame = ctk.CTkFrame(root, fg_color="transparent")
nav_frame.pack(pady=10)

btn_og = ctk.CTkButton(nav_frame, text="📅 OG Schedule", font=("Segoe UI", 14, "bold"), height=40, command=lambda: switch_view("og"))
btn_og.pack(side="left", padx=10)

btn_tasks = ctk.CTkButton(nav_frame, text="📋 Task Manager", font=("Segoe UI", 14, "bold"), height=40, fg_color="#d68910", hover_color="#b3710d", command=lambda: switch_view("tasks"))
btn_tasks.pack(side="left", padx=10)

btn_dash = ctk.CTkButton(nav_frame, text="🚀 Grand Dashboard", font=("Segoe UI", 14, "bold"), height=40, fg_color="#2fa572", hover_color="#248058", command=lambda: switch_view("dash"))
btn_dash.pack(side="left", padx=10)

# ==========================================

status_label = ctk.CTkLabel(root, text="Status: Ready", font=("Segoe UI", 14, "italic"), text_color="gray")
status_label.pack(pady=10)

btn_exit = ctk.CTkButton(root, text="Close SAPSA", fg_color="transparent", border_width=2, text_color="gray", hover_color="#c93434", command=exit_app)
btn_exit.pack(pady=10)

view_schedule() 
root.mainloop()