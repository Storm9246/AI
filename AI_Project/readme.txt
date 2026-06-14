---

```markdown
# SAPSA - Smart Academic & Personal Schedule Assistant

SAPSA is a lightweight, AI-driven desktop scheduling assistant designed to replace manual, rigid calendar applications. By integrating the **Google Gemini 2.5 Flash LLM** for Natural Language Understanding (NLU) and employing advanced **Heuristic Best-First Search (Constraint Satisfaction)** algorithms, SAPSA completely automates the organization of a student’s daily timeline.

## ✨ Key Features
* **AI Semantic Parsing:** Just type *"Add OS and DB on Mon and Tue at 8am and 9am respectively"* and the AI handles the complex parallel variable mapping.
* **Smart Conflict Resolution:** If you try to schedule a class over an existing one, SAPSA doesn't just error out. It runs a Best-First Search algorithm to mathematically find and suggest the closest available time slot.
* **Dynamic Rule Engine:** Configure your specific "Academic Hours" and "Weekends" in the settings. SAPSA will automatically block classes outside these hours but allow flexible personal tasks.
* **Predictive Template Engine:** Features a Google-style smart dropdown with 35 complex scheduling templates and a custom `Ctrl+Backspace` macro for rapid data entry.
* **Information Retrieval Dashboard:** A real-time fuzzy search bar that instantly filters your upcoming classes and exams as you type.
* **Automation Macros:** Tell the AI to *"Mark tomorrow as a sick day,"* and the system will automatically wipe your academic classes, bypass standard time rules, and visually paint your calendar red.

---

## 🚀 Installation & Setup

### 1. Prerequisites
You need Python installed on your computer. You also need to install the required external libraries. Open your terminal or command prompt and run:
```bash
pip install google-generativeai python-dotenv customtkinter tkcalendar

```

### 2. Setting Up the AI (CRITICAL STEP)

SAPSA relies on Google's Gemini AI to parse text. **The app will not work unless you provide your own free API key.**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and sign in with a personal Google account.
2. Click **Create API Key**.
3. In the root folder of this project (the exact same folder where `main.py` is located), create a new text file and name it exactly **`.env`** (make sure there is no `.txt` extension at the end).
4. Open the `.env` file in Notepad or your code editor and paste your key exactly like this:
```env
GEMINI_API_KEY=AIzaSyYourGeneratedKeyGoesHere...

```


5. Save the `.env` file.

*(Note: Never share your `.env` file or upload it to a public GitHub repository. The code uses `python-dotenv` to securely load this key in the background).*

### 3. Run the App

Once your `.env` file is saved with your API key, simply run the main controller file:

```bash
python main.py

```

---

## 📂 Project Architecture (MVC Pattern)

SAPSA is built using a highly modular Model-View-Controller architecture:

* `main.py` **(Controller):** The central nervous system. Routes UI clicks to database operations, manages the single-page application views, and handles complex recurrence loops.
* `database.py` **(Model/Algorithms):** The logic powerhouse. Enforces dynamic constraints, calculates time overlaps, and runs the A* Heuristic Search algorithm.
* `ai_engine.py` **(AI Brain):** The NLP translation layer. Uses Few-Shot Prompting and temporal context injection to talk to Google Gemini securely.
* `gui.py` **(View):** The CustomTkinter visual layer. Contains the interactive widgets, scrollable frames, and custom conflict pop-up dialogs.
* `config.json` & `schedule.json`: Dynamic local storage files that auto-generate upon first run.

---

## 👥 Project Team

Submitted for the Artificial Intelligence (AI) course (Spring 2026):

* **Zain ul Abideen Ahmad** (24K-0818)
* **Usman Hasan** (24K-0759)
* **Fatima Salman** (24K-1021)

```

```
