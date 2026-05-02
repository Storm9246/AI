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
            display_str = f"🕒 {e['time']} | {e['task']} [{e['category']}]"
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
        
        # 1. NEW: Check for an exact duplicate first!
        if database.is_duplicate(date, original_time, task_name):
            messagebox.showinfo("Duplicate Event", f"You already have '{task_name}' scheduled on {date} at {original_time}.\n\nSkipping duplicate!")
            continue # Skip adding this specific duplicate event
            
        # 2. Check for a general time slot conflict
        if database.check_conflict(date, original_time):
            new_time = database.find_next_available(date, original_time)
            
            if new_time:
                msg = f"Time slot {original_time} on {date} is booked!\n\nSAPSA found a gap at {new_time}.\n\nSchedule '{task_name}' on {date} at {new_time} instead?"
                if messagebox.askyesno("Conflict Detected!", msg):
                    data['time'] = new_time 
                else:
                    continue 
            else:
                messagebox.showerror("Error", f"Your schedule on {date} is completely full!")
                continue 

        # Save if it passes all checks
        database.add_event(data)
        events_added += 1
    
    status_label.config(text=f"Status: Successfully added {events_added} new event(s)!", fg="green")
    command_entry.delete(0, tk.END)
    
    if data_list:
        target_date = datetime.strptime(data_list[0]['date'], "%Y-%m-%d").date()
        cal.selection_set(target_date)
        view_schedule()

def add_manually():
    task = manual_task.get()
    time = manual_time.get()
    cat = manual_cat.get()
    date = cal.selection_get().strftime("%Y-%m-%d")
    
    if not task or not time:
        status_label.config(text="Status: Fill all manual fields!", fg="red")
        return
        
    # Manual Entry Checks
    if database.is_duplicate(date, time, task):
        messagebox.showinfo("Duplicate Event", f"You already have '{task}' scheduled at this time!")
        return
        
    if database.check_conflict(date, time):
        messagebox.showwarning("Conflict", f"You already have a different event scheduled at {time}!")
        return
        
    new_event = {"task": task, "date": date, "time": time, "category": cat}
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
    event_time = parts[0]
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
manual_cat = ttk.Combobox(man_frame, values=["Academic", "Personal"], width=10)
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