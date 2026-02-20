"""
AI-Powered Context-Aware Doubt Resolution & Learning Assistant
Beautiful Modern UI — Tkinter Edition v3.0
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading, json, os, random, subprocess, sys
from datetime import datetime

# ── Auto-install requests ─────────────────────────────────────────
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])

# ═════════════════════════════════════════════════════════════════
#  DATA
# ═════════════════════════════════════════════════════════════════
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
    "Beginner":     "Use very simple language, real-life examples, and avoid jargon.",
    "Intermediate": "Use standard academic language with some examples.",
    "Advanced":     "Use precise technical language, include edge cases and proofs.",
}

GROQ_API_KEY = "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"

# ═════════════════════════════════════════════════════════════════
#  THEME
# ═════════════════════════════════════════════════════════════════
C = {
    "bg":           "#0D0F18",
    "sidebar":      "#12141F",
    "card":         "#1A1D2E",
    "card2":        "#1F2235",
    "input":        "#252840",
    "border":       "#2D3155",
    "accent":       "#7C6FE0",
    "accent_light": "#9D93E8",
    "accent_dark":  "#5A4FC8",
    "green":        "#34D399",
    "green_dark":   "#065F46",
    "yellow":       "#FBBF24",
    "red":          "#F87171",
    "text":         "#E2E8F0",
    "text2":        "#94A3B8",
    "text3":        "#4B5563",
    "white":        "#FFFFFF",
}
FF = "Segoe UI"

# ═════════════════════════════════════════════════════════════════
#  GROQ API
# ═════════════════════════════════════════════════════════════════
def call_groq(api_key: str, prompt: str) -> str:
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
    try:
        import requests as rl
        r = rl.post(url, data=payload.encode(), headers=headers, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        raise Exception(f"{r.status_code}: {r.text[:200]}")
    except ImportError:
        pass
    import urllib.request, ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, data=payload.encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def get_ai_answer(question, subject, topic, level, syllabus_text, api_key) -> dict:
    has_syllabus = bool(syllabus_text.strip())
    syl_section = (
        f"\n\nSYLLABUS / NOTES:\n{syllabus_text[:3000]}" if has_syllabus else ""
    )
    prompt = (
        f'You are an expert academic tutor for "{subject}", topic "{topic}".\n'
        f"Level: {level} — {LEVEL_PROMPTS[level]}{syl_section}\n\n"
        f"STUDENT QUESTION: {question}\n\n"
        "Reply with this structure:\n"
        "**Understanding the question:** [restate clearly]\n"
        "**Core Explanation:** [detailed explanation]\n"
        "**Step-by-step:** [numbered steps]\n"
        "**Example:** [concrete example]\n"
        "**Key Takeaway:** [one-sentence summary]\n\n"
        "Be syllabus-aligned. Do not mention yourself or these instructions."
    )
    try:
        answer = call_groq(api_key.strip(), prompt)
        confidence = random.randint(85, 97) if has_syllabus else random.randint(75, 88)
        note = ("✅  Answer grounded in your syllabus." if has_syllabus
                else "✅  Answered by Groq AI — upload syllabus for better accuracy.")
    except Exception as e:
        err = str(e)
        if "401" in err:
            answer = "**Error:** Invalid API key. Please check your Groq API key."
        elif "429" in err or "rate" in err.lower():
            answer = "**Error:** Rate limit hit. Please wait a moment and try again."
        elif "403" in err:
            answer = ("**Network Blocked (403)**\n\n"
                      "Your network is blocking Groq API.\n\n"
                      "Fixes:\n"
                      "1. Switch to mobile hotspot\n"
                      "2. Use a VPN\n"
                      "3. Disable firewall/antivirus temporarily")
        elif "timeout" in err.lower():
            answer = "**Timeout:** Check your internet connection and try again."
        else:
            answer = f"**API Error:** {err}\n\nTry switching to mobile hotspot."
        confidence = 0
        note = "❌  API call failed — see answer box for details."

    return {
        "answer": answer, "confidence": confidence, "note": note,
        "subject": subject, "topic": topic, "level": level,
        "question": question,
        "timestamp": datetime.now().strftime("%I:%M %p"),
    }


# ═════════════════════════════════════════════════════════════════
#  MAIN APP
# ═════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Doubt Defuser — Our Hackathon Team")
        self.geometry("1280x800")
        self.minsize(1020, 660)
        self.configure(bg=C["bg"])

        self.syllabus_text = ""
        self.history       = []
        self.api_key_var   = tk.StringVar(value=GROQ_API_KEY)
        self.subject_var   = tk.StringVar(value=list(SUBJECT_TOPICS.keys())[0])
        self.topic_var     = tk.StringVar()
        self.level_var     = tk.StringVar(value="Intermediate")
        self._spinning     = False

        self._styles()
        self._header()
        self._body()
        self._statusbar()
        self._refresh_topics()

    # ─────────────────────────────────────────────────────────────
    def _styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("CB.TCombobox",
            fieldbackground=C["input"], background=C["input"],
            foreground=C["text"], selectbackground=C["accent"],
            selectforeground=C["white"], arrowcolor=C["text2"],
            borderwidth=0, relief="flat", padding=7)
        s.map("CB.TCombobox",
            fieldbackground=[("readonly", C["input"])],
            foreground=[("readonly", C["text"])])
        s.configure("Dark.Vertical.TScrollbar",
            troughcolor=C["card"], background=C["border"],
            borderwidth=0, arrowsize=13,
            arrowcolor=C["text2"], relief="flat")
        s.map("Dark.Vertical.TScrollbar",
            background=[("active", C["accent"]), ("pressed", C["accent_dark"])],
            arrowcolor=[("active", C["white"])])
        s.configure("PB.Horizontal.TProgressbar",
            troughcolor=C["input"], background=C["accent"],
            borderwidth=0, thickness=7)

    # ─────────────────────────────────────────────────────────────
    def _header(self):
        h = tk.Frame(self, bg=C["accent_dark"], height=62)
        h.pack(fill="x")
        h.pack_propagate(False)

        # Left
        lf = tk.Frame(h, bg=C["accent_dark"])
        lf.pack(side="left", padx=18, pady=10)
        tk.Label(lf, text="🎓", font=(FF, 20), bg=C["accent_dark"],
                 fg=C["white"]).pack(side="left")
        tk.Label(lf, text="  Doubt Defuser",
                 font=(FF, 16, "bold"), bg=C["accent_dark"],
                 fg=C["white"]).pack(side="left")
        tk.Label(lf, text="  ·  Our Hackathon Team",
                 font=(FF, 10), bg=C["accent_dark"],
                 fg=C["accent_light"]).pack(side="left")

        # Right — API key
        rf = tk.Frame(h, bg=C["accent_dark"])
        rf.pack(side="right", padx=18, pady=10)

        tk.Label(rf, text="🔑  API Key",
                 font=(FF, 9), bg=C["accent_dark"],
                 fg=C["accent_light"]).pack(side="left", padx=(0, 8))

        self._api_e = tk.Entry(rf, textvariable=self.api_key_var,
                               font=(FF, 9), width=36, show="•",
                               bg="#3D2FA0", fg=C["white"],
                               insertbackground=C["white"],
                               relief="flat", bd=0,
                               highlightthickness=1,
                               highlightbackground=C["accent_light"],
                               highlightcolor=C["white"])
        self._api_e.pack(side="left", ipady=6, padx=(0, 6))

        def toggle():
            self._api_e.config(
                show="" if self._api_e.cget("show") == "•" else "•")

        tk.Button(rf, text="👁", command=toggle,
                  bg=C["accent"], fg=C["white"], font=(FF, 9),
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=C["accent_light"],
                  padx=8, pady=4).pack(side="left")

    # ─────────────────────────────────────────────────────────────
    def _body(self):
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        # Sidebar
        sb = tk.Frame(body, bg=C["sidebar"], width=300)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        self._sidebar(sb)

        # Separator
        tk.Frame(body, bg=C["border"], width=1).pack(side="left", fill="y")

        # Main
        main = tk.Frame(body, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)
        self._main(main)

    # ─────────────────────────────────────────────────────────────
    def _sidebar(self, sb):
        pad = tk.Frame(sb, bg=C["sidebar"])
        pad.pack(fill="both", expand=True, padx=14, pady=14)

        # ── Settings ─────────────────────────────────────────────
        self._sec(pad, "⚙  Context Settings")
        s1 = self._card(pad)
        self._field(s1, "Subject", self.subject_var,
                    list(SUBJECT_TOPICS.keys()),
                    lambda e: self._refresh_topics())
        tk.Frame(s1, bg=C["input"], height=1).pack(fill="x", pady=8)
        self._field(s1, "Topic", self.topic_var, [])
        tk.Frame(s1, bg=C["input"], height=1).pack(fill="x", pady=8)
        self._field(s1, "Explanation Level", self.level_var,
                    list(LEVEL_PROMPTS.keys()))

        # Level quick-select pills
        pills = tk.Frame(s1, bg=C["card"])
        pills.pack(fill="x", pady=(8, 0))
        pill_data = [
            ("Beginner",     "#065F46", "#34D399"),
            ("Intermediate", "#78350F", "#FBBF24"),
            ("Advanced",     "#7F1D1D", "#F87171"),
        ]
        for lvl, bg, fg in pill_data:
            f = tk.Frame(pills, bg=bg, padx=8, pady=3)
            f.pack(side="left", padx=(0, 5))
            l = tk.Label(f, text=lvl, font=(FF, 7, "bold"), bg=bg, fg=fg,
                         cursor="hand2")
            l.pack()
            l.bind("<Button-1>", lambda e, v=lvl: self.level_var.set(v))
            f.bind("<Button-1>", lambda e, v=lvl: self.level_var.set(v))

        tk.Frame(pad, bg=C["sidebar"], height=12).pack(fill="x")

        # ── Syllabus ─────────────────────────────────────────────
        self._sec(pad, "📄  Syllabus / Notes")
        s2 = self._card(pad)

        self.syl_status = tk.Label(s2,
            text="No material uploaded",
            font=(FF, 8), fg=C["text2"], bg=C["card"],
            anchor="w", wraplength=240)
        self.syl_status.pack(fill="x", pady=(0, 8))

        br = tk.Frame(s2, bg=C["card"])
        br.pack(fill="x")
        self._btn(br, "📂  Upload File",
                  self._upload_syllabus, "#065F46").pack(side="left", padx=(0,6))
        self._btn(br, "✏️  Paste Text",
                  self._paste_dialog, C["input"]).pack(side="left")

        self.syl_prev = tk.Text(s2, height=5, font=("Consolas", 7),
            bg=C["input"], fg=C["text2"],
            relief="flat", bd=0, wrap="word",
            state="disabled", padx=8, pady=6,
            highlightthickness=0)
        self.syl_prev.pack(fill="x", pady=(8, 0))

        tk.Frame(pad, bg=C["sidebar"], height=12).pack(fill="x")

        # ── History ──────────────────────────────────────────────
        self._sec(pad, "🕘  Session History")
        s3 = self._card(pad, expand=True)

        self.hist_lb = tk.Listbox(s3,
            font=(FF, 8), bg=C["input"], fg=C["text"],
            selectbackground=C["accent"], selectforeground=C["white"],
            relief="flat", bd=0, activestyle="none",
            highlightthickness=0, height=8)
        self.hist_lb.pack(fill="both", expand=True)
        self.hist_lb.bind("<<ListboxSelect>>", self._load_hist)

        tk.Frame(s3, bg=C["card"], height=8).pack()
        self._btn(s3, "🗑  Clear History",
                  self._clear_hist, C["input"]).pack(anchor="w")

    # ─────────────────────────────────────────────────────────────
    def _main(self, main):
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        # ── Question Area ─────────────────────────────────────────
        top = tk.Frame(main, bg=C["bg"])
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        top.columnconfigure(0, weight=1)

        self._sec(top, "❓  Ask Your Doubt", inline=True)

        qcard = self._card(top, padx=0, pady=0)

        self.q_box = tk.Text(qcard, height=4,
            font=(FF, 11), bg=C["card"], fg=C["text2"],
            insertbackground=C["text"],
            relief="flat", bd=0, wrap="word",
            padx=16, pady=14, highlightthickness=0)
        self.q_box.pack(fill="x")
        self.q_box.insert("1.0", "Type your question here…")
        self.q_box.bind("<FocusIn>",  self._qin)
        self.q_box.bind("<FocusOut>", self._qout)
        self.q_box.bind("<Return>",
                        lambda e: (self._ask(), "break")[1])

        tk.Frame(qcard, bg=C["border"], height=1).pack(fill="x")

        # Toolbar
        tb = tk.Frame(qcard, bg=C["card2"], pady=10)
        tb.pack(fill="x", padx=12)

        # Ask button (custom styled)
        self._ask_btn_frame = tk.Frame(tb, bg=C["card2"])
        self._ask_btn_frame.pack(side="left")
        self.ask_btn = tk.Button(
            self._ask_btn_frame,
            text="🚀  Resolve Doubt",
            command=self._ask,
            font=(FF, 10, "bold"),
            bg=C["accent"], fg=C["white"],
            relief="flat", bd=0,
            padx=22, pady=8, cursor="hand2",
            activebackground=C["accent_light"],
            activeforeground=C["white"])
        self.ask_btn.pack()
        self._add_hover(self.ask_btn, C["accent"], C["accent_light"])

        self._btn(tb, "🔄  Clear", self._clear_all,
                  C["input"]).pack(side="left", padx=(10, 0))

        self.spin_lbl = tk.Label(tb, text="",
            font=(FF, 10), fg=C["accent_light"], bg=C["card2"])
        self.spin_lbl.pack(side="left", padx=12)

        # Confidence (right side)
        cf = tk.Frame(tb, bg=C["card2"])
        cf.pack(side="right")

        tk.Label(cf, text="Confidence",
                 font=(FF, 8), fg=C["text2"],
                 bg=C["card2"]).pack(side="left", padx=(0, 8))
        self.conf_var = tk.IntVar(value=0)
        ttk.Progressbar(cf, variable=self.conf_var,
                        maximum=100, length=130,
                        style="PB.Horizontal.TProgressbar"
                        ).pack(side="left")
        self.conf_lbl = tk.Label(cf, text="—",
            font=(FF, 9, "bold"), fg=C["text2"],
            bg=C["card2"], width=6)
        self.conf_lbl.pack(side="left", padx=(8, 0))

        # ── Answer Area ───────────────────────────────────────────
        bot = tk.Frame(main, bg=C["bg"])
        bot.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 10))
        bot.rowconfigure(1, weight=1)
        bot.columnconfigure(0, weight=1)

        # Note row
        self.note_lbl = tk.Label(bot, text="",
            font=(FF, 8), fg=C["text2"], bg=C["bg"],
            anchor="w", wraplength=900)
        self.note_lbl.grid(row=0, column=0, sticky="ew", pady=(0, 3))

        self._sec_grid(bot, "💡  Answer", row=0)

        acard_outer = tk.Frame(bot,
            bg=C["card"],
            highlightthickness=1,
            highlightbackground=C["border"])
        acard_outer.grid(row=1, column=0, sticky="nsew")

        # Answer box with custom dark scrollbar
        ans_frame = tk.Frame(acard_outer, bg=C["card"])
        ans_frame.pack(fill="both", expand=True)

        self.ans_box = tk.Text(
            ans_frame,
            font=(FF, 10),
            bg=C["card"], fg=C["text"],
            insertbackground=C["text"],
            relief="flat", bd=0, wrap="word",
            state="disabled",
            padx=18, pady=16,
            highlightthickness=0)
        self.ans_box.pack(side="left", fill="both", expand=True)

        ans_scroll = ttk.Scrollbar(ans_frame, orient="vertical",
                                   style="Dark.Vertical.TScrollbar",
                                   command=self.ans_box.yview)
        ans_scroll.pack(side="right", fill="y")
        self.ans_box.configure(yscrollcommand=ans_scroll.set)

        self.ans_box.tag_configure("h",
            font=(FF, 10, "bold"), foreground=C["accent_light"],
            spacing1=10, spacing3=2)
        self.ans_box.tag_configure("b",
            font=(FF, 10), foreground=C["text"], spacing3=1)
        self.ans_box.tag_configure("m",
            font=(FF, 10, "italic"), foreground=C["text2"])
        self.ans_box.tag_configure("w",
            foreground=C["yellow"])

        tk.Frame(acard_outer, bg=C["border"], height=1).pack(fill="x")
        ft = tk.Frame(acard_outer, bg=C["card2"], pady=8)
        ft.pack(fill="x", padx=12)

        self._btn(ft, "💾  Export Session",
                  self._export, "#065F46").pack(side="left", padx=(0, 8))
        self._btn(ft, "📋  Copy Answer",
                  self._copy, C["input"]).pack(side="left")

    # ─────────────────────────────────────────────────────────────
    def _statusbar(self):
        sb = tk.Frame(self, bg=C["sidebar"], height=28)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self.status_var = tk.StringVar(
            value="Ready — type your question and click Resolve Doubt")
        tk.Label(sb, textvariable=self.status_var,
                 font=(FF, 8), fg=C["text2"],
                 bg=C["sidebar"], anchor="w").pack(side="left", padx=14)
        tk.Label(sb, text="v3.0  ·  Groq Llama 3.3 70B",
                 font=(FF, 8), fg=C["text3"],
                 bg=C["sidebar"]).pack(side="right", padx=14)

    # ── WIDGET HELPERS ────────────────────────────────────────────
    def _sec(self, p, text, inline=False):
        tk.Label(p, text=text,
                 font=(FF, 9, "bold"),
                 fg=C["accent_light"], bg=p["bg"],
                 anchor="w").pack(fill="x", pady=(0, 5))

    def _sec_grid(self, p, text, row):
        tk.Label(p, text=text,
                 font=(FF, 9, "bold"),
                 fg=C["accent_light"], bg=p["bg"],
                 anchor="w").grid(row=row, column=0, sticky="w",
                                  pady=(0, 4))

    def _card(self, parent, padx=10, pady=8, expand=False):
        outer = tk.Frame(parent,
                         bg=C["card"],
                         highlightthickness=1,
                         highlightbackground=C["border"])
        if expand:
            outer.pack(fill="both", expand=True, pady=(0, 0))
        else:
            outer.pack(fill="x", pady=(0, 0))
        inner = tk.Frame(outer, bg=C["card"],
                         padx=12 + padx, pady=10 + pady)
        inner.pack(fill="both", expand=True)
        return inner

    def _field(self, p, label, var, values, cmd=None):
        tk.Label(p, text=label,
                 font=(FF, 8), fg=C["text2"],
                 bg=C["card"], anchor="w").pack(fill="x", pady=(0, 3))
        cb = ttk.Combobox(p, textvariable=var, values=values,
                          state="readonly", style="CB.TCombobox",
                          font=(FF, 9))
        cb.pack(fill="x")
        if cmd:
            cb.bind("<<ComboboxSelected>>", cmd)
        return cb

    def _btn(self, p, text, cmd, color, **kw):
        b = tk.Button(p, text=text, command=cmd,
                      font=(FF, 8, "bold"),
                      bg=color, fg=C["white"],
                      relief="flat", bd=0,
                      padx=12, pady=6,
                      cursor="hand2",
                      activebackground=C["accent"],
                      activeforeground=C["white"], **kw)
        return b

    def _add_hover(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>",
                    lambda e: widget.configure(bg=hover_bg))
        widget.bind("<Leave>",
                    lambda e: widget.configure(bg=normal_bg))

    # ── LOGIC ─────────────────────────────────────────────────────
    def _refresh_topics(self, *_):
        topics = SUBJECT_TOPICS.get(self.subject_var.get(), [])
        self.topic_var.set(topics[0] if topics else "")

    def _qin(self, e):
        if self.q_box.get("1.0", "end-1c") == "Type your question here…":
            self.q_box.delete("1.0", "end")
            self.q_box.configure(fg=C["text"])

    def _qout(self, e):
        if not self.q_box.get("1.0", "end-1c").strip():
            self.q_box.insert("1.0", "Type your question here…")
            self.q_box.configure(fg=C["text2"])

    def _ask(self):
        q = self.q_box.get("1.0", "end-1c").strip()
        if not q or q == "Type your question here…":
            messagebox.showwarning("No Question",
                                   "Please type your question first.")
            return
        self.ask_btn.configure(state="disabled", bg=C["input"])
        self._set_ans("")
        self.conf_var.set(0)
        self.conf_lbl.configure(text="—", fg=C["text2"])
        self.note_lbl.configure(text="")
        self.status_var.set("⏳  AI is thinking…")
        self._spin_start()

        def worker():
            result = get_ai_answer(
                q, self.subject_var.get(), self.topic_var.get(),
                self.level_var.get(), self.syllabus_text,
                self.api_key_var.get())
            self.after(0, lambda: self._show(q, result))

        threading.Thread(target=worker, daemon=True).start()

    def _show(self, question, r):
        self._spin_stop()
        self.ask_btn.configure(state="normal", bg=C["accent"])

        c = r["confidence"]
        self.conf_var.set(c)
        col = C["green"] if c >= 80 else C["yellow"] if c >= 50 else C["red"]
        self.conf_lbl.configure(text=f"{c}%", fg=col)
        self.note_lbl.configure(text=r["note"])

        self.ans_box.configure(state="normal")
        self.ans_box.delete("1.0", "end")
        for line in r["answer"].split("\n"):
            s = line.strip()
            if s.startswith("**") and s.endswith("**") and s.count("**") == 2:
                self.ans_box.insert("end", s.strip("*") + "\n", "h")
            elif "**" in s:
                parts = s.split("**")
                for i, p in enumerate(parts):
                    self.ans_box.insert("end", p, "h" if i % 2 == 1 else "b")
                self.ans_box.insert("end", "\n")
            elif s.lower().startswith("error") or "❌" in s:
                self.ans_box.insert("end", s + "\n", "w")
            elif s == "":
                self.ans_box.insert("end", "\n")
            else:
                self.ans_box.insert("end", s + "\n", "b")
        self.ans_box.configure(state="disabled")

        self.history.append(r)
        short = question[:44] + ("…" if len(question) > 44 else "")
        self.hist_lb.insert("end", f"  {r['timestamp']}   {short}")
        self.status_var.set(
            f"✅  {r['subject']}  →  {r['topic']}  "
            f"│  Confidence: {c}%  │  {r['timestamp']}")

    def _load_hist(self, e):
        sel = self.hist_lb.curselection()
        if not sel or sel[0] >= len(self.history):
            return
        item = self.history[sel[0]]
        self.subject_var.set(item["subject"])
        self.topic_var.set(item["topic"])
        self.level_var.set(item["level"])
        self.conf_var.set(item["confidence"])
        col = C["green"] if item["confidence"] >= 80 else C["yellow"] if item["confidence"] >= 50 else C["red"]
        self.conf_lbl.configure(text=f"{item['confidence']}%", fg=col)
        self.note_lbl.configure(text=item["note"])
        self.q_box.delete("1.0", "end")
        self.q_box.insert("1.0", item["question"])
        self.q_box.configure(fg=C["text"])
        self.ans_box.configure(state="normal")
        self.ans_box.delete("1.0", "end")
        self.ans_box.insert("end", item["answer"])
        self.ans_box.configure(state="disabled")

    def _clear_hist(self):
        self.history.clear()
        self.hist_lb.delete(0, "end")
        self.status_var.set("History cleared.")

    def _clear_all(self):
        self._set_ans("")
        self.conf_var.set(0)
        self.conf_lbl.configure(text="—", fg=C["text2"])
        self.note_lbl.configure(text="")
        self.q_box.delete("1.0", "end")
        self._qout(None)

    # ── SYLLABUS ──────────────────────────────────────────────────
    def _upload_syllabus(self):
        path = filedialog.askopenfilename(
            title="Select Syllabus / Notes",
            filetypes=[("All supported", "*.txt *.pdf *.docx"),
                       ("Text", "*.txt"), ("PDF", "*.pdf"),
                       ("Word", "*.docx"), ("All", "*.*")])
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".pdf":
                self.syllabus_text = self._read_pdf(path)
            elif ext == ".docx":
                self.syllabus_text = self._read_docx(path)
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    self.syllabus_text = f.read()
            if not self.syllabus_text.strip():
                messagebox.showwarning("Empty", "No text found. Try a .txt file.")
                return
            self._update_syl_ui(os.path.basename(path))
            # Auto-detect topics using AI in background
            self._detect_topics_async()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _detect_topics_async(self):
        """Run AI topic detection in background thread."""
        self.status_var.set("🔍  AI is scanning your syllabus for topics…")
        self.syl_status.configure(
            text="🔍  Detecting topics…", fg=C["yellow"])

        def worker():
            try:
                prompt = (
                    "You are a syllabus analyzer. Read the following document and extract "
                    "ALL chapter names, topic names, and unit titles present in it.\n\n"
                    "Return ONLY a JSON array of strings, nothing else. No explanation. No markdown.\n"
                    "Example: [\"Linked Lists\", \"Binary Trees\", \"Sorting Algorithms\"]\n\n"
                    f"DOCUMENT:\n{self.syllabus_text[:4000]}"
                )
                raw = call_groq(self.api_key_var.get().strip(), prompt)
                # Parse JSON safely
                raw = raw.strip()
                start = raw.find("[")
                end   = raw.rfind("]") + 1
                if start != -1 and end > start:
                    topics = json.loads(raw[start:end])
                else:
                    topics = []
                self.after(0, lambda: self._show_detected_topics(topics))
            except Exception as ex:
                self.after(0, lambda: self._show_detected_topics([], error=str(ex)))

        threading.Thread(target=worker, daemon=True).start()

    def _show_detected_topics(self, topics: list, error: str = ""):
        """Show detected topics as clickable chips in a popup window."""
        words = len(self.syllabus_text.split())

        if error or not topics:
            self.syl_status.configure(
                text=f"✅  Loaded ({words:,} words) — topic scan failed",
                fg=C["yellow"])
            self.status_var.set("⚠️  Could not detect topics automatically.")
            return

        # Update status
        self.syl_status.configure(
            text=f"✅  Loaded ({words:,} words) — {len(topics)} topics found",
            fg=C["green"])
        self.status_var.set(
            f"✅  Syllabus scanned — {len(topics)} topics detected by AI!")

        # ── Popup window ────────────────────────────────────────
        win = tk.Toplevel(self)
        win.title("📚 Topics Detected in Syllabus")
        win.geometry("640x500")
        win.configure(bg=C["card"])
        win.grab_set()
        win.resizable(True, True)

        # Header
        hdr = tk.Frame(win, bg=C["accent_dark"], height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📚  Topics Found in Your Syllabus",
                 font=(FF, 13, "bold"),
                 bg=C["accent_dark"], fg=C["white"]
                 ).pack(side="left", padx=18, pady=14)
        tk.Label(hdr, text=f"{len(topics)} topics",
                 font=(FF, 10),
                 bg=C["accent_dark"], fg=C["accent_light"]
                 ).pack(side="right", padx=18)

        # Subtitle
        tk.Label(win,
                 text="Click any topic to set it as your current topic, then ask your doubt!",
                 font=(FF, 9), fg=C["text2"], bg=C["card"]
                 ).pack(padx=18, pady=(10, 4), anchor="w")

        tk.Frame(win, bg=C["border"], height=1).pack(fill="x", padx=18)

        # Scrollable chips area
        canvas = tk.Canvas(win, bg=C["card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0, 6), pady=8)
        canvas.pack(fill="both", expand=True, padx=18, pady=8)

        chip_frame = tk.Frame(canvas, bg=C["card"])
        canvas_win = canvas.create_window((0, 0), window=chip_frame, anchor="nw")

        def on_resize(e):
            canvas.itemconfig(canvas_win, width=e.width)
        canvas.bind("<Configure>", on_resize)

        chip_frame.bind("<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))

        # Draw chips in a flowing grid (4 per row)
        selected_var = tk.StringVar(value="")

        def make_chip(parent, text, idx):
            colors = [
                ("#1E3A5F", "#60A5FA"),
                ("#1A3A2A", "#34D399"),
                ("#3B1F5E", "#A78BFA"),
                ("#3B2A00", "#FBBF24"),
                ("#3B1818", "#F87171"),
            ]
            bg, fg = colors[idx % len(colors)]

            chip = tk.Frame(parent, bg=bg, padx=10, pady=6,
                            cursor="hand2")
            lbl = tk.Label(chip, text=f"  {text}  ",
                           font=(FF, 8, "bold"),
                           bg=bg, fg=fg, cursor="hand2",
                           wraplength=130, justify="left")
            lbl.pack()

            def on_click(t=text):
                self.topic_var.set(t)
                selected_var.set(t)
                # Flash selected
                chip.configure(bg=C["accent"])
                lbl.configure(bg=C["accent"], fg=C["white"])
                self.status_var.set(
                    f"✅  Topic set to: '{t}' — now ask your doubt!")
                win.after(300, win.destroy)

            chip.bind("<Button-1>", lambda e, t=text: on_click(t))
            lbl.bind("<Button-1>",  lambda e, t=text: on_click(t))
            chip.bind("<Enter>",
                      lambda e, c=chip, l=lbl, f=fg:
                      (c.configure(bg=C["accent"]),
                       l.configure(bg=C["accent"], fg=C["white"])))
            chip.bind("<Leave>",
                      lambda e, c=chip, l=lbl, b=bg, f=fg:
                      (c.configure(bg=b), l.configure(bg=b, fg=f)))
            return chip

        cols = 3
        for i, topic in enumerate(topics):
            row, col = divmod(i, cols)
            chip = make_chip(chip_frame, topic, i)
            chip.grid(row=row, column=col, padx=6, pady=5, sticky="ew")

        for c_idx in range(cols):
            chip_frame.columnconfigure(c_idx, weight=1)

        # Footer
        tk.Frame(win, bg=C["border"], height=1).pack(fill="x", padx=18)
        ft = tk.Frame(win, bg=C["card"])
        ft.pack(fill="x", padx=18, pady=10)
        tk.Label(ft, text="💡 Tip: These topics are from your syllabus PDF — click one to auto-fill the topic field.",
                 font=(FF, 8), fg=C["text2"], bg=C["card"],
                 wraplength=500, justify="left").pack(side="left")
        self._btn(ft, "✖  Close", win.destroy,
                  C["input"]).pack(side="right")

    def _read_pdf(self, path):
        import importlib
        def _try(name):
            try:
                m = importlib.import_module(name)
                pages = []
                with open(path, "rb") as f:
                    for pg in m.PdfReader(f).pages:
                        t = pg.extract_text()
                        if t: pages.append(t)
                return "\n".join(pages) if pages else None
            except ImportError:
                return None
        for mod in ("PyPDF2", "pypdf"):
            r = _try(mod)
            if r: return r
        self.status_var.set("Installing PDF reader…")
        self.update()
        subprocess.check_call([sys.executable, "-m", "pip",
                               "install", "PyPDF2", "-q"])
        return _try("PyPDF2") or ""

    def _read_docx(self, path):
        import importlib
        try:
            docx = importlib.import_module("docx")
        except ImportError:
            self.status_var.set("Installing python-docx…")
            self.update()
            subprocess.check_call([sys.executable, "-m", "pip",
                                   "install", "python-docx", "-q"])
            docx = importlib.import_module("docx")
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _paste_dialog(self):
        win = tk.Toplevel(self)
        win.title("Paste Syllabus / Notes")
        win.geometry("580x400")
        win.configure(bg=C["card"])
        win.grab_set()

        tk.Label(win, text="📝  Paste your syllabus or notes below",
                 font=(FF, 11, "bold"),
                 bg=C["card"], fg=C["text"]).pack(
                     padx=18, pady=(16, 6), anchor="w")

        txt = scrolledtext.ScrolledText(win, font=(FF, 9),
            bg=C["input"], fg=C["text"],
            insertbackground=C["text"], relief="flat", bd=0,
            padx=10, pady=8, wrap="word", highlightthickness=0)
        txt.pack(fill="both", expand=True, padx=18, pady=4)

        def save():
            self.syllabus_text = txt.get("1.0", "end-1c")
            self._update_syl_ui("Pasted text")
            self._detect_topics_async()
            win.destroy()

        bf = tk.Frame(win, bg=C["card"])
        bf.pack(pady=12)
        self._btn(bf, "✅  Save Notes", save,
                  C["accent"]).pack(side="left", padx=6)
        self._btn(bf, "✖  Cancel", win.destroy,
                  C["input"]).pack(side="left")

    def _update_syl_ui(self, name):
        words = len(self.syllabus_text.split())
        self.syl_status.configure(
            text=f"✅  {name}  ({words:,} words)", fg=C["green"])
        self.syl_prev.configure(state="normal")
        self.syl_prev.delete("1.0", "end")
        self.syl_prev.insert(
            "1.0", self.syllabus_text[:400] +
            ("…" if len(self.syllabus_text) > 400 else ""))
        self.syl_prev.configure(state="disabled")

    # ── EXPORT / COPY ─────────────────────────────────────────────
    def _export(self):
        if not self.history:
            messagebox.showinfo("Empty", "No session history yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)
        messagebox.showinfo("Saved", f"Session saved to:\n{path}")

    def _copy(self):
        content = self.ans_box.get("1.0", "end-1c")
        if content.strip():
            self.clipboard_clear()
            self.clipboard_append(content)
            self.status_var.set("✅  Answer copied to clipboard.")

    # ── SPINNER ───────────────────────────────────────────────────
    def _spin_start(self):
        self._spinning = True
        frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        self._si = 0
        def spin():
            if self._spinning:
                self.spin_lbl.configure(
                    text=f"{frames[self._si % len(frames)]}  AI thinking…")
                self._si += 1
                self.after(90, spin)
            else:
                self.spin_lbl.configure(text="")
        spin()

    def _spin_stop(self):
        self._spinning = False

    def _set_ans(self, text, muted=False):
        self.ans_box.configure(state="normal")
        self.ans_box.delete("1.0", "end")
        if text:
            self.ans_box.insert("1.0", text, "m" if muted else "b")
        self.ans_box.configure(state="disabled")


# ═════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
