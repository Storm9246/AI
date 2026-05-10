import tkinter as tk
import customtkinter as ctk
from tkcalendar import Calendar
from datetime import datetime

# ==========================================
# 1. ROOT SETUP
# ==========================================
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

root = ctk.CTk()
root.title("SAPSA - Smart Assistant")
root.geometry("900x800")

# ==========================================
# 2. CONFLICT DIALOG CLASS
# ==========================================
class ConflictDialog(ctk.CTkToplevel):
    def __init__(self, master, date, original_time, category, duration, all_slots, is_flexible, task_name, conflict_reason):
        super().__init__(master)
        self.title("🚨 SAPSA Conflict Resolution")
        self.geometry("520x600")
        self.attributes("-topmost", True)
        self.grab_set() 

        self.result_action = None 
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=f"Conflict: {task_name}", font=("Segoe UI", 22, "bold"), text_color="#c93434").grid(row=0, column=0, pady=(20, 5))
        ctk.CTkLabel(self, text=f"🚨 {conflict_reason}", font=("Segoe UI", 16, "bold"), text_color="#d68910", wraplength=450).grid(row=1, column=0, pady=(0, 20))

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

        drop_frame = ctk.CTkFrame(self, corner_radius=10)
        drop_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(drop_frame, text="🔍 Browse All Free Slots", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        
        self.slot_var = ctk.StringVar(value=all_slots[0] if all_slots else "No slots available")
        self.dropdown = ctk.CTkComboBox(drop_frame, values=all_slots if all_slots else ["None"], variable=self.slot_var, width=200)
        self.dropdown.pack(pady=5)
        ctk.CTkButton(drop_frame, text="Select This Slot", command=lambda: self.close_with(self.slot_var.get())).pack(pady=10)

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

        self.info_label = ctk.CTkLabel(self, text="Hover over an action to see what it does.", font=("Segoe UI", 12, "italic"), text_color="gray")
        self.info_label.grid(row=5, column=0, pady=(0, 10))

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
# 3. CONTAINERS & VIEWS
# ==========================================
top_frame = ctk.CTkFrame(root, fg_color="transparent")
top_frame.pack(pady=20, fill="x", padx=20)

task_view_frame = ctk.CTkFrame(root, corner_radius=15, fg_color="#2b2b2b")
ctk.CTkLabel(task_view_frame, text="📋 Task Manager", font=("Segoe UI", 20, "bold")).pack(pady=(10, 5))
task_scroll = ctk.CTkScrollableFrame(task_view_frame, fg_color="transparent")
task_scroll.pack(fill="both", expand=True, padx=10, pady=10)

dash_view_frame = ctk.CTkFrame(root, corner_radius=15, fg_color="#2b2b2b")
ctk.CTkLabel(dash_view_frame, text="🚀 Dashboard (Upcoming)", font=("Segoe UI", 20, "bold")).pack(pady=(10, 5))

# NEW: The Smart Search Bar
dash_search_frame = ctk.CTkFrame(dash_view_frame, fg_color="transparent")
dash_search_frame.pack(fill="x", padx=20, pady=(0, 10))

dash_search_var = tk.StringVar()
dash_search_entry = ctk.CTkEntry(dash_search_frame, textvariable=dash_search_var, placeholder_text="🔍 Search classes, locations, categories...", font=("Segoe UI", 14), width=400)
dash_search_entry.pack()

dash_scroll = ctk.CTkScrollableFrame(dash_view_frame, fg_color="transparent")
dash_scroll.pack(fill="both", expand=True, padx=10, pady=10)

# ==========================================
# SETTINGS CONTROL CENTER (NEW)
# ==========================================
settings_view_frame = ctk.CTkFrame(root, corner_radius=15, fg_color="#2b2b2b")
ctk.CTkLabel(settings_view_frame, text="⚙️ Settings & Constraints", font=("Segoe UI", 20, "bold")).pack(pady=(10, 5))

# 1. Academic Hours Config
hours_frame = ctk.CTkFrame(settings_view_frame, fg_color="transparent")
hours_frame.pack(fill="x", padx=20, pady=5)
ctk.CTkLabel(hours_frame, text="Academic Hours (HH:MM 24hr):", font=("Segoe UI", 16, "bold")).pack(anchor="w")
start_frame = ctk.CTkFrame(hours_frame, fg_color="transparent")
start_frame.pack(anchor="w", pady=5)
ctk.CTkLabel(start_frame, text="Start: ").pack(side="left")
set_acad_start = ctk.CTkEntry(start_frame, width=80)
set_acad_start.pack(side="left", padx=5)
ctk.CTkLabel(start_frame, text="End: ").pack(side="left", padx=(10,0))
set_acad_end = ctk.CTkEntry(start_frame, width=80)
set_acad_end.pack(side="left", padx=5)

# 2. Weekend Config
weekends_frame = ctk.CTkFrame(settings_view_frame, fg_color="transparent")
weekends_frame.pack(fill="x", padx=20, pady=5)
ctk.CTkLabel(weekends_frame, text="Weekend Days (Blocks Academic Classes):", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 5))
chk_days = []
days_inner = ctk.CTkFrame(weekends_frame, fg_color="transparent")
days_inner.pack(anchor="w")
for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
    var = tk.IntVar()
    chk = ctk.CTkCheckBox(days_inner, text=day, variable=var, width=50)
    chk.pack(side="left", padx=5)
    chk_days.append(var)

btn_save_settings = ctk.CTkButton(settings_view_frame, text="Save Configurations", font=("Segoe UI", 14, "bold"), fg_color="#2fa572", hover_color="#248058")
btn_save_settings.pack(pady=10)

# 3. Off Day Management
ctk.CTkLabel(settings_view_frame, text="🛑 Active Off/Sick Days", font=("Segoe UI", 16, "bold"), text_color="#c93434").pack(anchor="w", padx=20, pady=(10, 0))
settings_off_scroll = ctk.CTkScrollableFrame(settings_view_frame, fg_color="#1e1e1e", height=150)
settings_off_scroll.pack(fill="both", expand=True, padx=20, pady=10)

# ==========================================
# 4. CALENDAR & LISTBOX
# ==========================================
today = datetime.now()

cal_frame = ctk.CTkFrame(top_frame, corner_radius=15)
cal_frame.pack(side="left", padx=10, fill="both", expand=True)

cal = Calendar(cal_frame, selectmode='day', 
               year=today.year, month=today.month, day=today.day, 
               font=("Segoe UI", 15), cursor="hand2", background="#2b2b2b", 
               foreground="white", headersbackground="#1f538d",
               selectbackground="#8e44ad") 
               
cal.pack(padx=15, pady=15, fill="both", expand=True) 

list_frame = ctk.CTkFrame(top_frame, corner_radius=15)
list_frame.pack(side="right", fill="both", expand=True, padx=10)

date_label = ctk.CTkLabel(list_frame, text="Schedule for: ", font=("Segoe UI", 16, "bold"))
date_label.pack(pady=10)

schedule_listbox = tk.Listbox(list_frame, font=("Consolas", 12), height=10, 
                              bg="#2b2b2b", fg="white", selectbackground="#1f538d", borderwidth=0)
schedule_listbox.pack(fill="both", expand=True, padx=10, pady=5)

btn_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
btn_frame.pack(pady=10)

btn_delete = ctk.CTkButton(btn_frame, text="Delete Selected", fg_color="#c93434", hover_color="#a32a2a")
btn_delete.pack(side="left", padx=5)

btn_briefing = ctk.CTkButton(btn_frame, text="Generate AI Briefing")
btn_briefing.pack(side="left", padx=5)

# ==========================================
# 5. AI FRAME
# ==========================================
ai_frame = ctk.CTkFrame(root, corner_radius=15)
ai_frame.pack(fill="x", padx=30, pady=10)

ctk.CTkLabel(ai_frame, text="🤖 AI Assistant", font=("Segoe UI", 16, "bold"), text_color="#3b8ed0").pack(pady=(10, 0))

ai_input_frame = ctk.CTkFrame(ai_frame, fg_color="transparent")
ai_input_frame.pack(pady=10)

command_entry = ctk.CTkEntry(ai_input_frame, font=("Segoe UI", 14), width=450, placeholder_text="e.g., Schedule a 2-hour OS lab tomorrow at 2 PM")
command_entry.pack(side="left", padx=10)

btn_ask = ctk.CTkButton(ai_input_frame, text="Ask AI", font=("Segoe UI", 14, "bold"))
btn_ask.pack(side="left")

# NEW: The floating predictive dropdown box (Starts hidden)
suggestion_box = tk.Listbox(root, font=("Segoe UI", 12), bg="#1e1e1e", fg="#a0a0a0", 
                            selectbackground="#3b8ed0", selectforeground="white", 
                            borderwidth=1, relief="solid", highlightthickness=0)

# ==========================================
# 6. PRO MANUAL ENTRY PANEL
# ==========================================
btn_toggle_manual = ctk.CTkButton(root, text="➕ Add Manually", fg_color="transparent")
btn_toggle_manual.pack(pady=(5, 10))

manual_panel = ctk.CTkFrame(root, corner_radius=15, fg_color="#2b2b2b")
man_inner = ctk.CTkFrame(manual_panel, fg_color="transparent")
man_inner.pack(pady=15)

manual_type_var = ctk.StringVar(value="Event (Takes Time)")
ctk.CTkSegmentedButton(man_inner, values=["Event (Takes Time)", "Task (Deadline)"], variable=manual_type_var).grid(row=0, column=0, columnspan=2, pady=5)
ctk.CTkLabel(man_inner, text="Date:").grid(row=0, column=2, padx=5)
manual_date = ctk.CTkEntry(man_inner, width=100)
manual_date.grid(row=0, column=3, padx=5)

ctk.CTkLabel(man_inner, text="Title:").grid(row=1, column=0, padx=5, pady=5)
manual_task = ctk.CTkEntry(man_inner, width=150)
manual_task.grid(row=1, column=1, padx=5, pady=5)
ctk.CTkLabel(man_inner, text="Time:").grid(row=1, column=2, padx=5, pady=5)
manual_time = ctk.CTkEntry(man_inner, width=80, placeholder_text="14:00")
manual_time.grid(row=1, column=3, padx=5, pady=5)
ctk.CTkLabel(man_inner, text="Loc:").grid(row=1, column=4, padx=5, pady=5)
manual_loc = ctk.CTkEntry(man_inner, width=80)
manual_loc.grid(row=1, column=5, padx=5, pady=5)

ctk.CTkLabel(man_inner, text="Cat:").grid(row=2, column=0, padx=5, pady=10)
manual_cat = ctk.CTkComboBox(man_inner, values=["Academic", "Self-Study", "Home Chores", "Project", "Exam", "Personal Task"], width=130)
manual_cat.grid(row=2, column=1, padx=5, pady=10)
ctk.CTkLabel(man_inner, text="Recur:").grid(row=2, column=2)
manual_recur = ctk.CTkComboBox(man_inner, values=["None", "Daily", "Weekly"], width=90)
manual_recur.grid(row=2, column=3)
manual_end_date = ctk.CTkEntry(man_inner, width=110, placeholder_text="Until YYYY-MM-DD")
manual_end_date.grid(row=2, column=4, columnspan=2)

btn_man_save = ctk.CTkButton(man_inner, text="Save to Schedule", fg_color="#2fa572")
btn_man_save.grid(row=3, column=0, columnspan=6, pady=10)

# ==========================================
# 7. NAVIGATION HUB
# ==========================================
nav_frame = ctk.CTkFrame(root, fg_color="transparent")
nav_frame.pack(pady=10)

btn_og = ctk.CTkButton(nav_frame, text="📅 Schedule", font=("Segoe UI", 14, "bold"), height=40)
btn_og.pack(side="left", padx=10)

btn_tasks = ctk.CTkButton(nav_frame, text="📋 Task Manager", font=("Segoe UI", 14, "bold"), height=40, fg_color="#d68910", hover_color="#b3710d")
btn_tasks.pack(side="left", padx=10)

# ... (inside your Navigation Hub) ...
btn_dash = ctk.CTkButton(nav_frame, text="🚀 Dashboard", font=("Segoe UI", 14, "bold"), height=40, fg_color="#2fa572", hover_color="#248058")
btn_dash.pack(side="left", padx=10)

# NEW: Settings Button
btn_settings = ctk.CTkButton(nav_frame, text="⚙️ Settings", font=("Segoe UI", 14, "bold"), height=40, fg_color="#1f538d", hover_color="#14375e")
btn_settings.pack(side="left", padx=10)

# ==========================================
# 8. FOOTER
# ==========================================
status_label = ctk.CTkLabel(root, text="Status: Ready", font=("Segoe UI", 14, "italic"), text_color="gray")
status_label.pack(pady=10)

btn_exit = ctk.CTkButton(root, text="Close SAPSA", fg_color="transparent", border_width=2, text_color="gray", hover_color="#c93434")
btn_exit.pack(pady=10)