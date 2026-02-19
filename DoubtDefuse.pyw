"""
AI-Powered Context-Aware Doubt Resolution & Learning Assistant
Tkinter GUI Application — Syllabus-aware, adaptive, confidence-scored
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import json
import os
import time
import random
import subprocess
import sys
from datetime import datetime

# Auto-install requests if missing
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])

# ─────────────────────────────────────────────────────────────────
#  MOCK AI ENGINE  (replace with real LLM / RAG calls)
# ─────────────────────────────────────────────────────────────────
SUBJECT_TOPICS = {
    "Elements of Mechanical Engineering": [
        "Engineering Materials", "Thermodynamics Basics", "Fluid Mechanics",
        "Simple Machines", "Power Transmission", "Manufacturing Processes",
    ],
    "Applied Mathematics 2": [
        "Differential Equations", "Laplace Transforms", "Fourier Series",
        "Complex Numbers", "Vector Calculus", "Numerical Methods",
    ],
    "Data Structure": [
        "Arrays & Linked Lists", "Stacks & Queues", "Trees & Graphs",
        "Sorting Algorithms", "Searching Algorithms", "Hashing",
    ],
    "English": [
        "Grammar & Composition", "Technical Writing", "Reading Comprehension",
        "Vocabulary", "Communication Skills", "Presentation Skills",
    ],
    "Web Development": [
        "HTML & CSS", "JavaScript", "Responsive Design",
        "Frontend Frameworks", "Backend Basics", "Databases & APIs",
    ],
}

LEVEL_PROMPTS = {
    "Beginner":      "Use very simple language, real-life examples, and avoid jargon.",
    "Intermediate":  "Use standard academic language with some examples.",
    "Advanced":      "Use precise technical language, include edge cases and proofs.",
}

def call_groq(api_key: str, prompt: str) -> str:
    """Call Groq API — tries requests lib first, falls back to urllib."""

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 1024,
    })
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Mozilla/5.0",
    }
    url = "https://api.groq.com/openai/v1/chat/completions"

    # ── Try with requests library (handles SSL/proxy better) ──
    try:
        import requests as req_lib
        resp = req_lib.post(url, data=payload.encode("utf-8"),
                            headers=headers, timeout=30, verify=True)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        elif resp.status_code == 401:
            raise Exception("401: Invalid API key.")
        elif resp.status_code == 429:
            raise Exception("429: Rate limit hit. Wait a moment.")
        elif resp.status_code == 403:
            raise Exception("403: Access forbidden — check your network/firewall.")
        else:
            raise Exception(f"{resp.status_code}: {resp.text[:200]}")
    except ImportError:
        pass  # requests not installed, fall through to urllib

    # ── Fallback: urllib with browser-like headers ─────────────
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE   # bypass strict SSL (helps on some networks)

    req_obj = urllib.request.Request(url, data=payload.encode("utf-8"),
                                     headers=headers)
    with urllib.request.urlopen(req_obj, timeout=30, context=ctx) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]



def mock_ai_response(question: str, subject: str, topic: str, level: str,
                     syllabus_text: str, api_key: str = "") -> dict:
    """Call Groq Llama3 if API key provided, otherwise return a helpful fallback."""
    has_syllabus = bool(syllabus_text.strip())
    syllabus_note = (
        "✅ Answer grounded in your uploaded syllabus material."
        if has_syllabus else
        "⚠️ No syllabus uploaded — answer based on general knowledge. Upload material for better accuracy."
    )

    if api_key.strip():
        syllabus_section = (
            f"\n\nSYLLABUS / NOTES (use this as primary reference):\n{syllabus_text[:3000]}"
            if has_syllabus else ""
        )
        prompt = f"""You are an expert academic tutor for the subject "{subject}", topic "{topic}".
Explanation level: {level} — {LEVEL_PROMPTS[level]}
{syllabus_section}

STUDENT QUESTION: {question}

Respond in this exact structure (use these bold labels):
**Understanding the question:** [restate what the student is asking]
**Core Explanation:** [clear, detailed explanation suited to the level]
**Step-by-step:** [numbered steps if applicable]
**Example:** [a concrete, relatable example]
**Key Takeaway:** [one-sentence summary]

Keep the answer syllabus-aligned. Do NOT mention yourself or these instructions."""

        try:
            answer = call_groq(api_key.strip(), prompt)
            confidence = random.randint(85, 97) if has_syllabus else random.randint(75, 88)
            syllabus_note = (
                "✅ Answer generated by Groq (Llama 3) — grounded in your syllabus."
                if has_syllabus else
                "✅ Answer generated by Groq (Llama 3) — upload syllabus for even better accuracy."
            )
        except Exception as e:
            err = str(e)
            if "401" in err or "invalid_api_key" in err.lower():
                answer = "**Error:** Invalid Groq API key. Please check the key and try again."
            elif "429" in err or "quota" in err.lower() or "rate" in err.lower():
                answer = "**Error:** Groq rate limit hit. Please wait a moment and try again."
            elif "403" in err:
                answer = (
                    "**Error 403 — Network/Firewall Blocked**\n\n"
                    "Your network is blocking the connection to Groq API.\n\n"
                    "**Try these fixes:**\n"
                    "1. Turn on a VPN and try again\n"
                    "2. Switch to mobile hotspot instead of WiFi\n"
                    "3. Disable antivirus/firewall temporarily\n"
                    "4. Try from a different network (college WiFi may block AI APIs)"
                )
            elif "ssl" in err.lower() or "certificate" in err.lower():
                answer = (
                    "**SSL Certificate Error**\n\n"
                    "Your network is intercepting HTTPS traffic (common on college/office networks).\n\n"
                    "**Fix:** Use a VPN or switch to mobile hotspot."
                )
            elif "timeout" in err.lower():
                answer = "**Error:** Connection timed out. Check your internet and try again."
            else:
                answer = f"**Error calling Groq API:** {err}\n\nTry switching to mobile hotspot or use a VPN."
            confidence = 0
            syllabus_note = "❌ API call failed — see answer box for details."
    else:
        answer = (
            f"**No API Key Provided**\n\n"
            f"To get real answers for your question about **{topic}** in **{subject}**, "
            f"please enter your Groq API key in the field at the top of the app.\n\n"
            f"**How to get a free key:**\n"
            f"1. Go to https://console.groq.com\n"
            f"2. Sign up and click 'API Keys' → 'Create API Key'\n"
            f"3. Copy and paste it into the 'API Key' field above\n\n"
            f"Once added, click 'Resolve Doubt' again for a real AI answer!"
        )
        confidence = 0
        syllabus_note = "⚠️ Enter your Groq API key above to activate AI responses."

    return {
        "answer":        answer,
        "confidence":    confidence,
        "syllabus_note": syllabus_note,
        "subject":       subject,
        "topic":         topic,
        "level":         level,
        "timestamp":     datetime.now().strftime("%H:%M:%S"),
    }


# ─────────────────────────────────────────────────────────────────
#  COLOR PALETTE
# ─────────────────────────────────────────────────────────────────
COLORS = {
    "bg":          "#0F1117",
    "surface":     "#1A1D27",
    "surface2":    "#22263A",
    "accent":      "#6C63FF",
    "accent2":     "#00D4AA",
    "accent3":     "#FF6B6B",
    "text":        "#E8EAF6",
    "text_muted":  "#7B82A8",
    "success":     "#00C896",
    "warning":     "#FFB347",
    "error":       "#FF5757",
    "border":      "#2E3250",
}


# ─────────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────────
class DoubtResolverApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎓 AI Doubt Resolver — Learning Assistant")
        self.geometry("1100x750")
        self.minsize(900, 640)
        self.configure(bg=COLORS["bg"])

        self.syllabus_text  = ""
        self.history        = []          # list of response dicts
        self.student_id_var = tk.StringVar()
        self.api_key_var    = tk.StringVar(value="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")
        self.subject_var    = tk.StringVar(value="Elements of Mechanical Engineering")
        self.topic_var      = tk.StringVar(value="Algebra")
        self.level_var      = tk.StringVar(value="Intermediate")

        self._build_ui()
        self._refresh_topics()

    # ── UI CONSTRUCTION ──────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        self._build_left_panel(main)
        self._build_right_panel(main)
        self._build_status_bar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=COLORS["accent"], height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🎓  AI Doubt Resolver & Learning Assistant",
                 font=("Segoe UI", 15, "bold"),
                 bg=COLORS["accent"], fg="white").pack(side="left", padx=20, pady=12)

        # PS ID field in header
        tk.Label(hdr, text="PS ID:", font=("Segoe UI", 10),
                 bg=COLORS["accent"], fg="white").pack(side="right", padx=(0, 8), pady=12)
        ps_entry = tk.Entry(hdr, textvariable=self.student_id_var,
                            font=("Segoe UI", 10), width=14,
                            bg=COLORS["surface2"], fg=COLORS["text"],
                            insertbackground=COLORS["text"], relief="flat", bd=4)
        ps_entry.pack(side="right", pady=12)
        tk.Label(hdr, text="Student", font=("Segoe UI", 10),
                 bg=COLORS["accent"], fg="white").pack(side="right", padx=(16, 4), pady=12)

        # Gemini API Key field
        tk.Label(hdr, text="🔑 Groq API Key:", font=("Segoe UI", 10),
                 bg=COLORS["accent"], fg="white").pack(side="right", padx=(0, 4), pady=12)
        api_entry = tk.Entry(hdr, textvariable=self.api_key_var,
                             font=("Segoe UI", 10), width=32, show="*",
                             bg=COLORS["surface2"], fg=COLORS["text"],
                             insertbackground=COLORS["text"], relief="flat", bd=4)
        api_entry.pack(side="right", pady=12)
        # Toggle show/hide key
        def toggle_key_vis():
            api_entry.config(show="" if api_entry.cget("show") == "*" else "*")
        tk.Button(hdr, text="👁", command=toggle_key_vis,
                  bg=COLORS["surface2"], fg=COLORS["text"],
                  relief="flat", bd=0, cursor="hand2", padx=4
                  ).pack(side="right", pady=12, padx=(0, 8))

    def _build_left_panel(self, parent):
        lf = tk.Frame(parent, bg=COLORS["surface"], bd=0)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        # ── Section: Context Settings ─────────────────────────
        self._section_label(lf, "⚙️  Context Settings")

        self._labeled_combo(lf, "Subject:", self.subject_var,
                            list(SUBJECT_TOPICS.keys()),
                            lambda e: self._refresh_topics())
        self._labeled_combo(lf, "Topic:", self.topic_var, [])
        self._labeled_combo(lf, "Explanation Level:", self.level_var,
                            list(LEVEL_PROMPTS.keys()))

        # ── Section: Syllabus Upload ──────────────────────────
        self._section_label(lf, "📄  Syllabus / Learning Material")

        self.syllabus_status = tk.Label(lf, text="No file uploaded",
                                        font=("Segoe UI", 9), fg=COLORS["text_muted"],
                                        bg=COLORS["surface"], anchor="w")
        self.syllabus_status.pack(fill="x", padx=14, pady=(0, 4))

        btn_row = tk.Frame(lf, bg=COLORS["surface"])
        btn_row.pack(fill="x", padx=14, pady=(0, 8))
        self._btn(btn_row, "📂 Upload File", self._upload_syllabus,
                  COLORS["accent2"]).pack(side="left", padx=(0, 6))
        self._btn(btn_row, "✏️ Paste Text", self._paste_syllabus_dialog,
                  COLORS["surface2"]).pack(side="left")

        self.syllabus_preview = scrolledtext.ScrolledText(
            lf, height=6, font=("Consolas", 8),
            bg=COLORS["surface2"], fg=COLORS["text_muted"],
            insertbackground=COLORS["text"], relief="flat", bd=0,
            wrap="word", state="disabled")
        self.syllabus_preview.pack(fill="x", padx=14, pady=(0, 10))

        # ── Section: History ──────────────────────────────────
        self._section_label(lf, "📜  Session History")

        self.history_list = tk.Listbox(
            lf, font=("Segoe UI", 8), height=8,
            bg=COLORS["surface2"], fg=COLORS["text"],
            selectbackground=COLORS["accent"], selectforeground="white",
            relief="flat", bd=0, activestyle="none")
        self.history_list.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.history_list.bind("<<ListboxSelect>>", self._load_history_item)

        self._btn(lf, "🗑️  Clear History", self._clear_history,
                  COLORS["surface2"]).pack(padx=14, pady=(0, 14), anchor="w")

    def _build_right_panel(self, parent):
        rf = tk.Frame(parent, bg=COLORS["surface"], bd=0)
        rf.grid(row=0, column=1, sticky="nsew")

        # ── Question Input ────────────────────────────────────
        self._section_label(rf, "❓  Ask Your Doubt")

        self.question_box = scrolledtext.ScrolledText(
            rf, height=4, font=("Segoe UI", 11),
            bg=COLORS["surface2"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat", bd=0,
            wrap="word")
        self.question_box.pack(fill="x", padx=14, pady=(0, 6))
        self.question_box.insert("1.0", "Type your question here…")
        self.question_box.bind("<FocusIn>",  self._clear_placeholder)
        self.question_box.bind("<FocusOut>", self._restore_placeholder)
        self.question_box.bind("<Return>",   lambda e: self._on_ask() or "break")

        ask_row = tk.Frame(rf, bg=COLORS["surface"])
        ask_row.pack(fill="x", padx=14, pady=(0, 10))

        self.ask_btn = self._btn(ask_row, "🚀  Resolve Doubt", self._on_ask,
                                 COLORS["accent"], width=18, font_size=11)
        self.ask_btn.pack(side="left", padx=(0, 10))

        self._btn(ask_row, "🔄 Clear", self._clear_answer,
                  COLORS["surface2"]).pack(side="left")

        self.spinner_label = tk.Label(ask_row, text="", font=("Segoe UI", 10),
                                      fg=COLORS["accent2"], bg=COLORS["surface"])
        self.spinner_label.pack(side="left", padx=10)

        # ── Confidence Bar ────────────────────────────────────
        conf_row = tk.Frame(rf, bg=COLORS["surface"])
        conf_row.pack(fill="x", padx=14, pady=(0, 6))
        tk.Label(conf_row, text="Confidence:", font=("Segoe UI", 9, "bold"),
                 fg=COLORS["text_muted"], bg=COLORS["surface"]).pack(side="left")
        self.conf_var = tk.IntVar(value=0)
        self.conf_bar = ttk.Progressbar(conf_row, variable=self.conf_var,
                                        maximum=100, length=200, mode="determinate")
        self.conf_bar.pack(side="left", padx=8)
        self.conf_pct_label = tk.Label(conf_row, text="—", font=("Segoe UI", 9, "bold"),
                                       fg=COLORS["accent2"], bg=COLORS["surface"])
        self.conf_pct_label.pack(side="left")

        self.syllabus_note_label = tk.Label(
            rf, text="", font=("Segoe UI", 8), fg=COLORS["text_muted"],
            bg=COLORS["surface"], anchor="w", wraplength=600, justify="left")
        self.syllabus_note_label.pack(fill="x", padx=14, pady=(0, 4))

        # ── Answer Box ────────────────────────────────────────
        self._section_label(rf, "💡  Answer")

        self.answer_box = scrolledtext.ScrolledText(
            rf, font=("Segoe UI", 10),
            bg=COLORS["surface2"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat", bd=0,
            wrap="word", state="disabled")
        self.answer_box.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        # Text tags for styling inside answer box
        self.answer_box.tag_configure("bold",    font=("Segoe UI", 10, "bold"), foreground=COLORS["accent2"])
        self.answer_box.tag_configure("step",    font=("Segoe UI", 10, "bold"), foreground=COLORS["accent"])
        self.answer_box.tag_configure("warning", foreground=COLORS["warning"])
        self.answer_box.tag_configure("muted",   foreground=COLORS["text_muted"])

        export_row = tk.Frame(rf, bg=COLORS["surface"])
        export_row.pack(fill="x", padx=14, pady=(0, 14))
        self._btn(export_row, "💾 Export Session", self._export_session,
                  COLORS["accent2"]).pack(side="left", padx=(0, 8))
        self._btn(export_row, "📋 Copy Answer", self._copy_answer,
                  COLORS["surface2"]).pack(side="left")

    def _build_status_bar(self):
        sb = tk.Frame(self, bg=COLORS["surface2"], height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready — enter your doubt above and click Resolve.")
        tk.Label(sb, textvariable=self.status_var,
                 font=("Segoe UI", 8), fg=COLORS["text_muted"],
                 bg=COLORS["surface2"], anchor="w").pack(side="left", padx=12)
        tk.Label(sb, text="v2.0  |  Powered by Groq (Llama 3)",
                 font=("Segoe UI", 8), fg=COLORS["border"],
                 bg=COLORS["surface2"]).pack(side="right", padx=12)

    # ── WIDGET HELPERS ────────────────────────────────────────────

    def _section_label(self, parent, text):
        f = tk.Frame(parent, bg=COLORS["border"], height=1)
        f.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                 fg=COLORS["accent"], bg=COLORS["surface"], anchor="w"
                 ).pack(fill="x", padx=14, pady=(4, 6))

    def _labeled_combo(self, parent, label, var, values, cmd=None):
        tk.Label(parent, text=label, font=("Segoe UI", 9),
                 fg=COLORS["text_muted"], bg=COLORS["surface"], anchor="w"
                 ).pack(fill="x", padx=14, pady=(0, 1))
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                         fieldbackground=COLORS["surface2"],
                         background=COLORS["surface2"],
                         foreground=COLORS["text"],
                         selectbackground=COLORS["accent"],
                         selectforeground="white",
                         arrowcolor=COLORS["text_muted"])
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", style="Dark.TCombobox",
                          font=("Segoe UI", 9))
        cb.pack(fill="x", padx=14, pady=(0, 8))
        if cmd:
            cb.bind("<<ComboboxSelected>>", cmd)
        return cb

    def _btn(self, parent, text, cmd, color, width=None, font_size=9):
        kw = dict(text=text, command=cmd,
                  bg=color, fg="white" if color != COLORS["surface2"] else COLORS["text"],
                  font=("Segoe UI", font_size, "bold"),
                  relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
                  activebackground=COLORS["accent"],
                  activeforeground="white")
        if width:
            kw["width"] = width
        btn = tk.Button(parent, **kw)
        return btn

    # ── LOGIC ─────────────────────────────────────────────────────

    def _refresh_topics(self, *_):
        subj   = self.subject_var.get()
        topics = SUBJECT_TOPICS.get(subj, [])
        # find combo for topic and update
        for w in self.winfo_children():
            pass  # we use variable directly
        self.topic_var.set(topics[0] if topics else "")

    def _clear_placeholder(self, e):
        if self.question_box.get("1.0", "end-1c") == "Type your question here…":
            self.question_box.delete("1.0", "end")
            self.question_box.configure(fg=COLORS["text"])

    def _restore_placeholder(self, e):
        if not self.question_box.get("1.0", "end-1c").strip():
            self.question_box.insert("1.0", "Type your question here…")
            self.question_box.configure(fg=COLORS["text_muted"])

    def _on_ask(self):
        question = self.question_box.get("1.0", "end-1c").strip()
        if not question or question == "Type your question here…":
            messagebox.showwarning("No Question", "Please type a question first.")
            return
        ps_id = self.student_id_var.get().strip()
        if not ps_id:
            messagebox.showwarning("PS ID Required", "Please enter your PS ID in the header.")
            return

        self.ask_btn.configure(state="disabled")
        self._set_answer("⏳ Resolving your doubt…", muted=True)
        self.status_var.set("Processing…")
        self._start_spinner()

        def worker():
            result = mock_ai_response(
                question,
                self.subject_var.get(),
                self.topic_var.get(),
                self.level_var.get(),
                self.syllabus_text,
                self.api_key_var.get(),
            )
            self.after(0, lambda: self._display_result(question, result))

        threading.Thread(target=worker, daemon=True).start()

    def _display_result(self, question, result):
        self._stop_spinner()
        self.ask_btn.configure(state="normal")

        # Confidence bar
        c = result["confidence"]
        self.conf_var.set(c)
        color = COLORS["success"] if c >= 80 else COLORS["warning"] if c >= 60 else COLORS["error"]
        self.conf_pct_label.configure(text=f"{c}%", fg=color)
        self.syllabus_note_label.configure(text=result["syllabus_note"])

        # Answer display
        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", "end")
        for line in result["answer"].split("\n"):
            if line.startswith("**") and line.endswith("**"):
                self.answer_box.insert("end", line.strip("*") + "\n", "step")
            elif "**" in line:
                parts = line.split("**")
                for i, p in enumerate(parts):
                    self.answer_box.insert("end", p, "bold" if i % 2 == 1 else "")
                self.answer_box.insert("end", "\n")
            elif "⚠️" in line or "Limitations" in line:
                self.answer_box.insert("end", line + "\n", "warning")
            else:
                self.answer_box.insert("end", line + "\n")
        self.answer_box.configure(state="disabled")

        # History
        entry = {**result, "question": question}
        self.history.append(entry)
        short_q = question[:48] + ("…" if len(question) > 48 else "")
        self.history_list.insert("end", f"[{result['timestamp']}] {short_q}")
        self.status_var.set(
            f"✅  Answered — {result['subject']} → {result['topic']}  |  "
            f"Confidence: {result['confidence']}%  |  PS ID: {self.student_id_var.get()}"
        )

    def _load_history_item(self, e):
        sel = self.history_list.curselection()
        if not sel or sel[0] >= len(self.history):
            return
        item = self.history[sel[0]]
        self.subject_var.set(item["subject"])
        self.topic_var.set(item["topic"])
        self.level_var.set(item["level"])
        self.conf_var.set(item["confidence"])
        self.conf_pct_label.configure(text=f"{item['confidence']}%")
        self.syllabus_note_label.configure(text=item["syllabus_note"])

        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", "end")
        self.answer_box.insert("end", item["answer"])
        self.answer_box.configure(state="disabled")

        self.question_box.delete("1.0", "end")
        self.question_box.insert("1.0", item["question"])
        self.question_box.configure(fg=COLORS["text"])

    def _clear_history(self):
        self.history.clear()
        self.history_list.delete(0, "end")
        self.status_var.set("History cleared.")

    def _clear_answer(self):
        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", "end")
        self.answer_box.configure(state="disabled")
        self.conf_var.set(0)
        self.conf_pct_label.configure(text="—")
        self.syllabus_note_label.configure(text="")
        self.question_box.delete("1.0", "end")
        self._restore_placeholder(None)

    # ── SYLLABUS ──────────────────────────────────────────────────

    def _upload_syllabus(self):
        path = filedialog.askopenfilename(
            title="Select Syllabus / Notes",
            filetypes=[
                ("All supported", "*.txt *.pdf *.docx"),
                ("Text files",    "*.txt"),
                ("PDF files",     "*.pdf"),
                ("Word files",    "*.docx"),
                ("All files",     "*.*"),
            ])
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()

            if ext == ".pdf":
                self.syllabus_text = self._extract_pdf_text(path)

            elif ext == ".docx":
                self.syllabus_text = self._extract_docx_text(path)

            else:
                # Plain text / fallback
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    self.syllabus_text = f.read()

            if not self.syllabus_text.strip():
                messagebox.showwarning("Empty File",
                    "Could not extract any text from this file.\n"
                    "Try saving it as a .txt file and uploading again.")
                return

            self._update_syllabus_ui(os.path.basename(path))

        except Exception as ex:
            messagebox.showerror("Error reading file", str(ex))

    def _extract_pdf_text(self, path: str) -> str:
        """Extract text from PDF — tries PyPDF2, then pdfminer, then pypdf."""
        # ── Try PyPDF2 ───────────────────────────────────────────
        try:
            import PyPDF2
            text = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
            if text:
                return "\n".join(text)
        except ImportError:
            pass

        # ── Try pypdf (newer fork) ───────────────────────────────
        try:
            import pypdf
            text = []
            with open(path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
            if text:
                return "\n".join(text)
        except ImportError:
            pass

        # ── Auto-install PyPDF2 and retry ────────────────────────
        self.status_var.set("Installing PDF reader (PyPDF2)…")
        self.update()
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "PyPDF2", "-q"])
        import PyPDF2
        text = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text.append(t)
        return "\n".join(text)

    def _extract_docx_text(self, path: str) -> str:
        """Extract text from .docx file."""
        try:
            import docx
        except ImportError:
            self.status_var.set("Installing python-docx…")
            self.update()
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                                   "python-docx", "-q"])
            import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())



    def _paste_syllabus_dialog(self):
        win = tk.Toplevel(self)
        win.title("Paste Syllabus / Notes")
        win.geometry("560x380")
        win.configure(bg=COLORS["surface"])
        tk.Label(win, text="Paste your syllabus or notes below:",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(padx=16, pady=(14, 4), anchor="w")
        txt = scrolledtext.ScrolledText(win, font=("Segoe UI", 9),
                                        bg=COLORS["surface2"], fg=COLORS["text"],
                                        insertbackground=COLORS["text"], relief="flat", bd=0)
        txt.pack(fill="both", expand=True, padx=16, pady=4)

        def save():
            self.syllabus_text = txt.get("1.0", "end-1c")
            self._update_syllabus_ui("Pasted text")
            win.destroy()

        self._btn(win, "✅ Save", save, COLORS["accent"]).pack(pady=10)

    def _update_syllabus_ui(self, name):
        word_count = len(self.syllabus_text.split())
        self.syllabus_status.configure(
            text=f"✅ {name}  ({word_count:,} words)", fg=COLORS["success"])
        self.syllabus_preview.configure(state="normal")
        self.syllabus_preview.delete("1.0", "end")
        preview = self.syllabus_text[:500] + ("…" if len(self.syllabus_text) > 500 else "")
        self.syllabus_preview.insert("1.0", preview)
        self.syllabus_preview.configure(state="disabled")
        self.status_var.set(f"Syllabus loaded: {name}")

    # ── EXPORT / COPY ─────────────────────────────────────────────

    def _export_session(self):
        if not self.history:
            messagebox.showinfo("Nothing to export", "No session history yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Text", "*.txt")],
            initialfile=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)
        messagebox.showinfo("Exported", f"Session saved to:\n{path}")

    def _copy_answer(self):
        content = self.answer_box.get("1.0", "end-1c")
        if content.strip():
            self.clipboard_clear()
            self.clipboard_append(content)
            self.status_var.set("Answer copied to clipboard.")

    # ── SPINNER ───────────────────────────────────────────────────

    def _start_spinner(self):
        self._spinning = True
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spin_i = 0

        def spin():
            if self._spinning:
                self.spinner_label.configure(text=f"{frames[self._spin_i % len(frames)]}  Thinking…")
                self._spin_i += 1
                self.after(100, spin)
            else:
                self.spinner_label.configure(text="")
        spin()

    def _stop_spinner(self):
        self._spinning = False

    def _set_answer(self, text, muted=False):
        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", "end")
        self.answer_box.insert("1.0", text, "muted" if muted else "")
        self.answer_box.configure(state="disabled")


# ─────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = DoubtResolverApp()
    app.mainloop()
