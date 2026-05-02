import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import ai_engine
import database 

# ==========================================
# 1. EVENT HANDLERS 
# ==========================================
def view_schedule(*args): 
    formatted_date = cal.selection_get().strftime("%Y-%m-%d")
    date_label.config(text=f"Schedule for: {formatted_date}")
    
    schedule_listbox.delete(0, tk.END)
    schedule = database.load_schedule()
    events_today = [e for e in schedule if e.get("date") == formatted_date]
    events_today = sorted(events_today, key=lambda x: x['time'])
    
    if not events_today:
        schedule_listbox.insert(tk.END, " No events scheduled for this day.")
    else:
        for e in events_today:
            # 1. Safely get the duration (default to 60m if it's an older event without one)
            duration = e.get('duration_mins', 60)
            
            # 2. Add ({duration}m) to the display string
            display_str = f"🕒 {e['time']} ({duration}m) | {e['task']} [{e['category']}]"
            
            schedule_listbox.insert(tk.END, display_str)

def ask_ai():
    user_text = command_entry.get()
    if not user_text.strip():
        status_label.config(text="Status: Please type a command first!", fg="red")
        return

    status_label.config(text="Status: AI is calculating dates & thinking...", fg="blue")
    root.update() 

    data_list, error = ai_engine.process_command(user_text)

    if error:
        status_label.config(text=f"Status: AI Error! \n({error})", fg="red")
        return
        
    events_added = 0
    
    for data in data_list:
        original_time = data['time']
        date = data['date']
        task_name = data['task']
        category = data['category']
        
        duration = data.get('duration_mins', 60) 
        is_flexible = data.get('is_flexible', True) 
        
        if database.is_duplicate(date, original_time, task_name):
            messagebox.showinfo("Duplicate", f"Skipping duplicate: '{task_name}'")
            continue 
            
        has_conflict = database.check_conflict(date, original_time, duration)
        out_of_window = database.is_outside_context_window(date, original_time, category)

        # SCENARIO 1: The time slot is already taken!
        if has_conflict:
            new_time = database.find_next_available(date, original_time, duration, category)
            if new_time:
                strict_note = "This is a STRICT class!" if not is_flexible else "This is a flexible event."
                msg = f"Time slot {original_time} is booked! ({strict_note})\n\nSAPSA found an open {category} slot at {new_time}. Schedule it then?"
                if messagebox.askyesno("Conflict Detected", msg):
                    data['time'] = new_time 
                else:
                    continue 
            else:
                messagebox.showerror("Error", f"No available {category} slots found!")
                continue 

        # SCENARIO 2: The time is free, but breaks the Weekday rules!
        elif out_of_window:
            msg = f"{original_time} is outside normal hours for '{category}'.\n\nDo you want to FORCE add it anyway (e.g., taking a day off)?"
            if not messagebox.askyesno("Rule Warning", msg):
                # User clicked NO, they want SAPSA to auto-fix it
                new_time = database.find_next_available(date, original_time, duration, category)
                if new_time:
                    if messagebox.askyesno("Auto-Fix", f"Move it to the correct time window at {new_time}?"):
                        data['time'] = new_time
                    else:
                        continue
                else:
                    messagebox.showerror("Error", "No available slots found.")
                    continue

        # If it passes all checks (or user clicked FORCE), save it!
        database.add_event(data)
        events_added += 1
    
    status_label.config(text=f"Status: Successfully added {events_added} new event(s)!", fg="green")
    command_entry.delete(0, tk.END)
    
    if data_list:
        target_date = datetime.strptime(data_list[0]['date'], "%Y-%m-%d").date()
        cal.selection_set(target_date)
        view_schedule()

def get_briefing():
    selected_date = cal.selection_get().strftime("%Y-%m-%d")
    events = database.get_events_for_date(selected_date)
    
    status_label.config(text="Status: AI is analyzing your day...", fg="blue")
    root.update()
    
    # Send the events to Gemini
    briefing, error = ai_engine.generate_daily_briefing(selected_date, events)
    
    if error:
        messagebox.showerror("AI Error", f"Failed to generate briefing:\n{error}")
        status_label.config(text="Status: Ready", fg="black")
    else:
        # Pop up a nice message box with the AI's summary
        messagebox.showinfo(f"SAPSA Briefing - {selected_date}", briefing)
        status_label.config(text="Status: Briefing generated!", fg="green")

def add_manually():
    task = manual_task.get()
    time = manual_time.get()
    cat = manual_cat.get()
    date = cal.selection_get().strftime("%Y-%m-%d")
    duration = 60 # Default manual entries to 1 hour
    
    if not task or not time:
        status_label.config(text="Status: Fill all manual fields!", fg="red")
        return
        
    # Safety Check: Make sure the user typed valid 24-hour time (HH:MM)
    try:
        datetime.strptime(time, "%H:%M")
    except ValueError:
        messagebox.showerror("Time Format Error", "Please enter the time in 24-hour format (e.g., 14:00 for 2 PM).")
        return
        
    if database.is_duplicate(date, time, task):
        messagebox.showinfo("Duplicate Event", f"You already have '{task}' scheduled at this time!")
        return
        
    # Apply the same AI Rules to Manual Entry
    has_conflict = database.check_conflict(date, time, duration)
    out_of_window = database.is_outside_context_window(date, time, cat)

    # SCENARIO 1: Conflict
    if has_conflict:
        new_time = database.find_next_available(date, time, duration, cat)
        if new_time:
            msg = f"Time slot {time} is booked!\n\nSAPSA found an open {cat} slot at {new_time}. Schedule it then?"
            if messagebox.askyesno("Conflict Detected", msg):
                time = new_time 
            else:
                return # Stop if user says no
        else:
            messagebox.showerror("Error", f"No available {cat} slots found!")
            return 

    # SCENARIO 2: Out of Window Rules
    elif out_of_window:
        msg = f"{time} is outside normal hours for '{cat}'.\n\nDo you want to FORCE add it anyway?"
        if not messagebox.askyesno("Rule Warning", msg):
            # User clicked NO, they want SAPSA to auto-fix it
            new_time = database.find_next_available(date, time, duration, cat)
            if new_time:
                if messagebox.askyesno("Auto-Fix", f"Move it to the correct time window at {new_time}?"):
                    time = new_time
                else:
                    return
            else:
                messagebox.showerror("Error", "No available slots found.")
                return

    # Assuming manual entries are "Hard Anchors" (Strict) so the AI doesn't move them later
    new_event = {"task": task, "date": date, "time": time, "category": cat, "duration_mins": duration, "is_flexible": False}
    database.add_event(new_event) 
    
    status_label.config(text="Status: Event added manually.", fg="green")
    manual_task.delete(0, tk.END)
    manual_time.delete(0, tk.END)
    view_schedule()

def delete_gui_event():
    selected = schedule_listbox.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Please select an event to delete.")
        return
    
    item_text = schedule_listbox.get(selected[0])
    if "No events" in item_text:
        return

    parts = item_text.replace("🕒 ", "").split(" | ")
    
    # FIX: Split the time string again to remove the "(60m)" part
    event_time = parts[0].split(" ")[0] 
    
    event_task = parts[1].split(" [")[0]
    selected_date = cal.selection_get().strftime("%Y-%m-%d")
    
    database.delete_event(selected_date, event_time, event_task)
    status_label.config(text="Status: Event deleted.", fg="green")
    view_schedule()

def exit_app():
    root.destroy()

# ==========================================
# 2. GUI SETUP 
# ==========================================
root = tk.Tk()
root.title("SAPSA - Smart Assistant")
root.geometry("850x950")

# --- Top Section: Calendar & Schedule ---
top_frame = tk.Frame(root)
top_frame.pack(pady=10, fill="x", padx=20)

today = datetime.now()

# 1. Create the calendar normally
cal = Calendar(top_frame, selectmode='day', 
               year=today.year, month=today.month, day=today.day, 
               font="Arial 14", cursor="hand2")
cal.pack(side="left", padx=10)
cal.bind("<<CalendarSelected>>", view_schedule) 

# 2. THE FIX: Force today's date to have a bright green background
cal.tag_config("current_day", background="lightgreen", foreground="black")
cal.calevent_create(today.date(), "Today", "current_day") 

list_frame = tk.Frame(top_frame)
list_frame.pack(side="right", fill="both", expand=True, padx=10)

date_label = tk.Label(list_frame, text="Schedule for: ", font=("Arial", 12, "bold"))
date_label.pack(pady=5)

schedule_listbox = tk.Listbox(list_frame, font=("Consolas", 12), height=10)
schedule_listbox.pack(fill="both", expand=True)

btn_delete = tk.Button(list_frame, text="Delete Selected", bg="red", fg="white", command=delete_gui_event)
btn_delete.pack(pady=5)

btn_briefing = tk.Button(list_frame, text="Generate AI Briefing", bg="blue", fg="white", font=("Arial", 10, "bold"), command=get_briefing)
btn_briefing.pack(pady=5)

ai_frame = tk.LabelFrame(root, text=" 🤖 AI Assistant ", font=("Arial", 12, "bold"), fg="blue", padx=10, pady=10)
ai_frame.pack(fill="x", padx=20, pady=10)

tk.Label(ai_frame, text="Type what you want to schedule:").pack(side="left")
command_entry = tk.Entry(ai_frame, font=("Arial", 14), width=40)
command_entry.pack(side="left", padx=10)

btn_ask = tk.Button(ai_frame, text="Ask AI", font=("Arial", 11, "bold"), bg="blue", fg="white", command=ask_ai)
btn_ask.pack(side="left")

man_frame = tk.LabelFrame(root, text=" ✍️ Manual Entry ", font=("Arial", 12, "bold"), fg="purple", padx=10, pady=10)
man_frame.pack(fill="x", padx=20, pady=10)

tk.Label(man_frame, text="Task:").grid(row=0, column=0, padx=5)
manual_task = tk.Entry(man_frame, width=20)
manual_task.grid(row=0, column=1, padx=5)

tk.Label(man_frame, text="Time (HH:MM):").grid(row=0, column=2, padx=5)
manual_time = tk.Entry(man_frame, width=10)
manual_time.grid(row=0, column=3, padx=5)

tk.Label(man_frame, text="Type:").grid(row=0, column=4, padx=5)
manual_cat = ttk.Combobox(man_frame, values=["Academic", "Self-Study", "Home Chores", "Outdoor Errands"], width=15)
manual_cat.current(0)
manual_cat.grid(row=0, column=5, padx=5)

btn_man = tk.Button(man_frame, text="Add Manually", bg="purple", fg="white", command=add_manually)
btn_man.grid(row=0, column=6, padx=15)

status_label = tk.Label(root, text="Status: Ready", font=("Arial", 11, "italic"))
status_label.pack(pady=10)

btn_exit = tk.Button(root, text="Close SAPSA", bg="darkred", fg="white", font=("Arial", 12, "bold"), command=exit_app)
btn_exit.pack(pady=10)

view_schedule() 
root.mainloop()