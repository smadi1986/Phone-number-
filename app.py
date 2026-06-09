import customtkinter as ctk
import sqlite3
import os
import csv
from tkinter import messagebox, filedialog
import hashlib
import shutil

# ─── Configuration & Theme ────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DB_PATH = os.path.join(os.path.dirname(__file__), "phonebook.db")

# Dynamic Colors (Light, Dark)
COLOR_BG       = ("#F8F9FA", "#0D1117")
COLOR_CARD     = ("#FFFFFF", "#161B22")
COLOR_BORDER   = ("#E1E4E8", "#30363D")
COLOR_TEXT_PRI = ("#24292E", "#E6EDF3")
COLOR_TEXT_SEC = ("#57606A", "#8B949E")
COLOR_GOLD     = "#D4A853"
COLOR_GOLD_HOV = "#C49743"
COLOR_RED      = "#CF222E"
COLOR_GREEN    = "#2DA44E"
COLOR_BLUE     = "#0969DA"
COLOR_RED_LOW  = ("#FEE2E2", "#450A0A")

# ─── Database ─────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            rank     TEXT,
            unit     TEXT,
            subunit  TEXT,
            phone1   TEXT    NOT NULL,
            phone2   TEXT,
            notes    TEXT,
            created  TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cur.execute("ALTER TABLE contacts ADD COLUMN subunit TEXT")
    except Exception:
        pass
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)
    pw = hashlib.sha256("admin123".encode()).hexdigest()
    cur.execute("INSERT OR IGNORE INTO users (username,password,is_admin) VALUES (?,?,1)",
                ("admin", pw))
    con.commit()
    con.close()

def db_query(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    con.close()
    return rows

def db_exec(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    lid = cur.lastrowid
    con.close()
    return lid

# ─── Login ────────────────────────────────────────────────
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("دليل الهاتف المؤسسي")
        self.geometry("420x550")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.logged_user = None
        self._build()
        self._center_window()

    def _center_window(self):
        self.eval('tk::PlaceWindow . center')

    def _build(self):
        ctk.CTkLabel(self, text="☎", font=("Arial", 64), text_color=COLOR_GOLD).pack(pady=(50,0))
        ctk.CTkLabel(self, text="\u202bدليل الهاتف المؤسسي\u202c",
                     font=("Arial", 24, "bold"), text_color=COLOR_TEXT_PRI).pack(pady=(8,4))
        ctk.CTkLabel(self, text="\u202bسجّل دخولك للمتابعة\u202c",
                     font=("Arial", 14), text_color=COLOR_TEXT_SEC).pack(pady=(0,30))

        frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=15,
                             border_width=1, border_color=COLOR_BORDER)
        frame.pack(padx=40, fill="x")

        ctk.CTkLabel(frame, text="اسم المستخدم", font=("Arial",13,"bold"),
                     text_color=COLOR_TEXT_SEC, anchor="e").pack(padx=25, pady=(20,5), fill="x")
        self.user_entry = ctk.CTkEntry(frame, height=45, font=("Arial",15),
                                       fg_color=COLOR_BG, border_color=COLOR_BORDER,
                                       text_color=COLOR_TEXT_PRI, justify="right")
        self.user_entry.pack(padx=25, fill="x")

        ctk.CTkLabel(frame, text="كلمة المرور", font=("Arial",13,"bold"),
                     text_color=COLOR_TEXT_SEC, anchor="e").pack(padx=25, pady=(15,5), fill="x")
        self.pass_entry = ctk.CTkEntry(frame, height=45, font=("Arial",15), show="●",
                                       fg_color=COLOR_BG, border_color=COLOR_BORDER,
                                       text_color=COLOR_TEXT_PRI, justify="right")
        self.pass_entry.pack(padx=25, fill="x")
        self.pass_entry.bind("<Return>", lambda e: self._login())

        self.err_lbl = ctk.CTkLabel(frame, text="", font=("Arial",12), text_color=COLOR_RED)
        self.err_lbl.pack(pady=(10,0))

        ctk.CTkButton(frame, text="دخول", height=45, font=("Arial",16,"bold"),
                      fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOV,
                      text_color="white", command=self._login).pack(padx=25, pady=(10,25), fill="x")

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(pady=20)
        ctk.CTkLabel(info_frame, text="المستخدم الافتراضي: admin | كلمة المرور: admin123",
                     font=("Arial",11), text_color=COLOR_TEXT_SEC).pack()
        
        self.appearance_mode_btn = ctk.CTkButton(self, text="تبديل المظهر", width=100, height=30,
                                               fg_color="transparent", border_width=1,
                                               border_color=COLOR_BORDER, text_color=COLOR_TEXT_SEC,
                                               command=self._toggle_appearance)
        self.appearance_mode_btn.pack(pady=10)

    def _toggle_appearance(self):
        ctk.set_appearance_mode("Light" if ctk.get_appearance_mode() == "Dark" else "Dark")
        self.after(100, self._update_theme_colors)
        self.after(150, self._search)

    def _login(self):
        u = self.user_entry.get().strip()
        p = hashlib.sha256(self.pass_entry.get().encode()).hexdigest()
        rows = db_query("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        if rows:
            self.logged_user = dict(rows[0])
            self.destroy()
        else:
            self.err_lbl.configure(text="❌ اسم المستخدم أو كلمة المرور غير صحيحة")

# ─── Main App ─────────────────────────────────────────────
class PhoneBookApp(ctk.CTk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"دليل الهاتف المؤسسي — {user['username']}")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color=COLOR_BG)
        self._panel = None
        
        self.search_var = ctk.StringVar()
        self.unit_var = ctk.StringVar(value="الكل")
        
        self._build()
        self._load_contacts()
        self.eval('tk::PlaceWindow . center')

    def _build(self):
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color=COLOR_CARD,
                                    corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="☎ الدليل",
                     font=("Arial",22,"bold"), text_color=COLOR_GOLD).pack(pady=(30,5))
        ctk.CTkLabel(self.sidebar, text=f"مرحباً، {self.user['username']}",
                     font=("Arial",14), text_color=COLOR_TEXT_SEC).pack(pady=(0,30))

        self._side_btn("📋  كل جهات الاتصال", self._show_all)
        if self.user["is_admin"]:
            self._side_btn("➕  إضافة جهة اتصال",  self._open_add)
            self._side_btn("📥  استيراد من Excel", self._import_excel)
        self._side_btn("📤  تصدير البيانات",  self._export_csv)
        if self.user["is_admin"]:
            self._side_btn("💾  نسخة احتياطية", self._manage_backup)
            self._side_btn("👤  إدارة المستخدمين", self._manage_users)

        self.theme_btn = ctk.CTkButton(self.sidebar, text="🌓 تبديل المظهر",
                                      fg_color="transparent", hover_color=COLOR_BG,
                                      text_color=COLOR_TEXT_PRI, font=("Arial",13),
                                      command=self._toggle_appearance)
        self.theme_btn.pack(side="bottom", pady=(0, 10), padx=20, fill="x")

        ctk.CTkButton(self.sidebar, text="🚪 تسجيل خروج",
                      fg_color="transparent", hover_color=COLOR_RED_LOW,
                      text_color=COLOR_RED, font=("Arial",13, "bold"),
                      command=self._logout).pack(side="bottom", pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.sidebar, text="v4.0", font=("Arial",10),
                     text_color=COLOR_TEXT_SEC).pack(side="bottom", pady=(0,10))

        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        topbar = ctk.CTkFrame(self.content, fg_color=COLOR_CARD, height=80,
                              corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        self.search_var.trace_add("write", lambda *_: self._search())
        srch = ctk.CTkEntry(topbar, textvariable=self.search_var,
                            placeholder_text="🔍 بحث بالاسم، الرتبة أو القسم...",
                            height=42, width=450, font=("Arial",14),
                            fg_color=COLOR_BG, border_color=COLOR_BORDER,
                            text_color=COLOR_TEXT_PRI, justify="right")
        srch.pack(side="right", padx=25, pady=19)

        self.count_lbl = ctk.CTkLabel(topbar, text="", font=("Arial",14), text_color=COLOR_TEXT_SEC)
        self.count_lbl.pack(side="left", padx=25)

        fbar = ctk.CTkFrame(self.content, fg_color="transparent", height=60, corner_radius=0)
        fbar.pack(fill="x", side="top")
        fbar.pack_propagate(False)

        ctk.CTkLabel(fbar, text="\u202bتصفية حسب التشكيل:\u202c", font=("Arial",13, "bold"),
                     text_color=COLOR_TEXT_PRI).pack(side="right", padx=(0,25), pady=15)
        self.unit_menu = ctk.CTkOptionMenu(fbar, variable=self.unit_var,
                                           values=["الكل"], width=200, height=35,
                                           fg_color=COLOR_CARD, button_color=COLOR_GOLD,
                                           button_hover_color=COLOR_GOLD_HOV,
                                           dropdown_fg_color=COLOR_CARD,
                                           text_color=COLOR_TEXT_PRI,
                                           anchor="center",
                                           command=self._handle_unit_change)
        self.unit_menu.pack(side="right", padx=10, pady=12)

        import tkinter as tk

        self.COLS = [("ملاحظات",150),("هاتف 2",150),("الهاتف الرئيسي",150),
                ("الفرع",180),("التشكيل",180),("الاسم",220),("الرتبة",180),("#",60)]
        if self.user["is_admin"]:
            self.COLS.insert(0, ("إجراءات",130))

        # ── Table area: canvas handles BOTH scroll directions ──
        table_area = tk.Frame(self.content, bg=self._get_bg_color(), bd=0)
        table_area.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self._table_area = table_area

        # Scrollbars
        self._vbar = tk.Scrollbar(table_area, orient="vertical")
        self._hbar = tk.Scrollbar(table_area, orient="horizontal")
        self._vbar.grid(row=0, column=1, sticky="ns")
        self._hbar.grid(row=1, column=0, sticky="ew")
        table_area.grid_rowconfigure(0, weight=1)
        table_area.grid_columnconfigure(0, weight=1)

        # Single canvas for header + rows
        self._tcanvas = tk.Canvas(table_area, bd=0, highlightthickness=0,
                                  yscrollcommand=self._vbar.set,
                                  xscrollcommand=self._hbar.set)
        self._tcanvas.grid(row=0, column=0, sticky="nsew")
        self._vbar.config(command=self._tcanvas.yview)
        self._hbar.config(command=self._tcanvas.xview)

        # Inner frame inside canvas
        self._inner = tk.Frame(self._tcanvas, bg=self._get_bg_color())
        self._inner_id = self._tcanvas.create_window((0,0), window=self._inner, anchor="nw")

        # Header row inside inner frame
        self._build_header()

        # Rows container
        self.scroll = tk.Frame(self._inner, bg=self._get_bg_color())
        self.scroll.pack(fill="both", expand=True)

        # Resize bindings
        self._inner.bind("<Configure>", self._on_inner_configure)
        self._tcanvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse wheel
        self._tcanvas.bind("<MouseWheel>",
            lambda e: self._tcanvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._tcanvas.bind("<Shift-MouseWheel>",
            lambda e: self._tcanvas.xview_scroll(int(-1*(e.delta/120)), "units"))

    def _get_bg_color(self):
        mode = ctk.get_appearance_mode()
        return COLOR_BG[1] if mode == "Dark" else COLOR_BG[0]

    def _get_card_color(self):
        mode = ctk.get_appearance_mode()
        return COLOR_CARD[1] if mode == "Dark" else COLOR_CARD[0]

    def _build_header(self):
        import tkinter as tk
        bg = self._get_card_color()
        hdr = tk.Frame(self._inner, bg=bg, height=45)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)
        for txt, w in self.COLS:
            cell = tk.Frame(hdr, bg=bg, width=w, height=45)
            cell.pack(side="left")
            cell.pack_propagate(False)
            tk.Label(cell, text=txt, font=("Arial",13,"bold"),
                     fg=COLOR_GOLD, bg=bg, anchor="center").place(relx=0.5, rely=0.5, anchor="center")

    def _on_inner_configure(self, event):
        self._tcanvas.configure(scrollregion=self._tcanvas.bbox("all"))

    def _on_canvas_resize(self, event):
        bg = self._get_bg_color()
        self._tcanvas.configure(bg=bg)
        self._inner.configure(bg=bg)
        self.scroll.configure(bg=bg)
        self._tcanvas.itemconfig(self._inner_id, width=max(event.width,
            sum(w for _,w in self.COLS) + 20))

    def _update_theme_colors(self):
        """Call after toggling dark/light to refresh canvas colors."""
        bg = self._get_bg_color()
        card = self._get_card_color()
        if hasattr(self, '_table_area'):
            self._table_area.configure(bg=bg)
        if hasattr(self, '_tcanvas'):
            self._tcanvas.configure(bg=bg)
        if hasattr(self, '_inner'):
            self._inner.configure(bg=bg)
        if hasattr(self, 'scroll'):
            self.scroll.configure(bg=bg)

    def _side_btn(self, label, cmd):
        ctk.CTkButton(self.sidebar, text=label, height=45,
                      fg_color="transparent", hover_color=COLOR_BG,
                      text_color=COLOR_TEXT_PRI, font=("Arial",14), anchor="e",
                      command=cmd).pack(padx=15, pady=5, fill="x")

    def _toggle_appearance(self):
        ctk.set_appearance_mode("Light" if ctk.get_appearance_mode() == "Dark" else "Dark")
        self.after(100, self._update_theme_colors)
        self.after(150, self._search)

    def _close_panel(self):
        if self._panel and self._panel.winfo_exists():
            self._panel.destroy()
        self._panel = None

    def _make_panel(self, title, width=500, height=650):
        self._close_panel()
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.configure(fg_color=COLOR_CARD)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        self._panel = win

        rx = self.winfo_x() + (self.winfo_width()  - width)  // 2
        ry = self.winfo_y() + (self.winfo_height() - height) // 2
        win.geometry(f"{width}x{height}+{rx}+{ry}")
        win.lift()
        win.focus_force()

        hdr = ctk.CTkFrame(win, fg_color=COLOR_BG, height=60, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=title, font=("Arial",18,"bold"), text_color=COLOR_GOLD).pack(side="right", padx=20, pady=15)
        ctk.CTkButton(hdr, text="إلغاء", width=100, height=35, fg_color=COLOR_RED, hover_color="#B91C1C",
                      text_color="white", font=("Arial",13,"bold"), command=self._close_panel).pack(side="left", padx=15, pady=12)

        body = ctk.CTkScrollableFrame(win, fg_color="transparent", corner_radius=0, width=width-20, height=height-80)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        return body

    # ── Data ────────────────────────────────────────────
    def _handle_unit_change(self, val):
        self._search()

    def _load_contacts(self, rows=None):
        if rows is None:
            rows = db_query("SELECT * FROM contacts ORDER BY name")

        raw_units = sorted({r["unit"] for r in db_query("SELECT DISTINCT unit FROM contacts") if r["unit"]})
        self._unit_map = {"الكل": "الكل"}
        display_units = ["الكل"]
        for u in raw_units:
            words = u.split()
            display = " ".join(reversed(words)) if len(words) > 1 else u
            self._unit_map[display] = u
            display_units.append(display)
        cur_real = self._unit_map.get(self.unit_var.get(), "الكل")
        new_display = next((d for d, r in self._unit_map.items() if r == cur_real), "الكل")
        self.unit_menu.configure(values=display_units)
        self.unit_var.set(new_display)

        for w in self.scroll.winfo_children():
            w.destroy()

        import tkinter as tk
        self.count_lbl.configure(text=f"إجمالي: {len(rows)} جهة اتصال")
        bg_page = self._get_bg_color()
        bg_card = self._get_card_color()
        txt_color = COLOR_TEXT_PRI[1] if ctk.get_appearance_mode()=="Dark" else COLOR_TEXT_PRI[0]
        brd_color = COLOR_BORDER[1] if ctk.get_appearance_mode()=="Dark" else COLOR_BORDER[0]

        for i, r in enumerate(rows):
            bg = bg_card if i % 2 == 0 else bg_page
            row_f = tk.Frame(self.scroll, bg=bg, height=50)
            row_f.pack(fill="x", pady=1, padx=4)
            row_f.pack_propagate(False)
            # Separator line
            sep = tk.Frame(self.scroll, bg=brd_color, height=1)
            sep.pack(fill="x", padx=4)

            rid = r["id"]
            if self.user["is_admin"]:
                act = tk.Frame(row_f, bg=bg, width=130, height=50)
                act.pack(side="left")
                act.pack_propagate(False)
                tk.Button(act, text="✏", width=3, font=("Arial",13),
                          bg=COLOR_BLUE, fg="white", bd=0, cursor="hand2", relief="flat",
                          activebackground="#1D4ED8", activeforeground="white",
                          command=lambda i=rid: self._open_edit(i)).place(x=8, y=9, width=38, height=32)
                tk.Button(act, text="🗑", width=3, font=("Arial",13),
                          bg=COLOR_RED, fg="white", bd=0, cursor="hand2", relief="flat",
                          activebackground="#B91C1C", activeforeground="white",
                          command=lambda i=rid: self._delete(i)).place(x=52, y=9, width=38, height=32)

            cols_data = [(r["notes"] or "—", 150),(r["phone2"] or "—", 150),(r["phone1"] or "—", 150),
                         (r["subunit"] or "—", 180),(r["unit"] or "—", 180),
                         (r["name"] or "—", 220),(r["rank"] or "—", 180),(str(i+1), 60)]
            for val, w in cols_data:
                cell = tk.Frame(row_f, bg=bg, width=w, height=50)
                cell.pack(side="left")
                cell.pack_propagate(False)
                tk.Label(cell, text=str(val), font=("Arial",13),
                         fg=txt_color, bg=bg, anchor="center").place(relx=0.5, rely=0.5, anchor="center")

        if not rows:
            tk.Label(self.scroll, text="لا توجد نتائج بحث", font=("Arial",15),
                     fg=COLOR_TEXT_SEC[1] if ctk.get_appearance_mode()=="Dark" else COLOR_TEXT_SEC[0],
                     bg=bg_page).pack(pady=80)

    def _search(self):
        q = self.search_var.get().strip()
        display_val = self.unit_var.get()
        # Resolve display label back to real DB value
        unit = getattr(self, '_unit_map', {}).get(display_val, display_val)
        unit = unit.replace("\u202b","").replace("\u202c","").replace("\u200f","").replace("\u200e","")

        params = []
        sql = "SELECT * FROM contacts WHERE 1=1"
        if q:
            sql += " AND (name LIKE ? OR rank LIKE ? OR unit LIKE ? OR phone1 LIKE ? OR phone2 LIKE ?)"
            params += [f"%{q}%"] * 5
        if unit != "الكل":
            sql += " AND unit=?"
            params.append(unit)
        sql += " ORDER BY name"
        self._load_contacts(db_query(sql, params))

    def _show_all(self):
        self._close_panel()
        self.search_var.set("")
        self.unit_var.set("الكل")
        self._load_contacts()

    # ── Import / Export ──────────────────────────────────
    def _import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if not path: return
        try:
            import pandas as pd
            df = pd.read_excel(path)
            if "الاسم" not in df.columns or "هاتف 1" not in df.columns:
                messagebox.showerror("خطأ", "يجب أن يحتوي الملف على عمودين 'الاسم' و 'هاتف 1' على الأقل.")
                return
            count = 0
            for _, row in df.iterrows():
                name = str(row.get("الاسم", "")).strip()
                p1 = str(row.get("هاتف 1", "")).strip()
                if name and p1:
                    vals = (name, str(row.get("الرتبة", "")).strip() if pd.notna(row.get("الرتبة")) else "",
                            str(row.get("التشكيل", "")).strip() if pd.notna(row.get("التشكيل")) else "",
                            p1, str(row.get("هاتف 2", "")).strip() if pd.notna(row.get("هاتف 2")) else "",
                            str(row.get("ملاحظات", "")).strip() if pd.notna(row.get("ملاحظات")) else "")
                    db_exec("INSERT INTO contacts (name,rank,unit,phone1,phone2,notes) VALUES (?,?,?,?,?,?)", vals)
                    count += 1
            self._load_contacts()
            messagebox.showinfo("نجاح", f"تم استيراد {count} جهة اتصال.")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الاستيراد:\n{e}")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="تصدير")
        if not path: return
        rows = db_query("SELECT name,rank,unit,phone1,phone2,notes FROM contacts ORDER BY name")
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["الاسم","الرتبة","التشكيل","هاتف 1","هاتف 2","ملاحظات"])
                for r in rows: w.writerow(list(r))
            messagebox.showinfo("نجاح", "تم التصدير بنجاح.")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل التصدير: {e}")

    # ── RTL text helper ──────────────────────────────────
    @staticmethod
    def _r(text):
        """Reverse word order so CTkButton (LTR engine) shows Arabic RTL correctly."""
        words = text.split(" ")
        return " ".join(reversed(words))

    # ── Backup ───────────────────────────────────────────
    def _manage_backup(self):
        body = self._make_panel("💾 النسخ الاحتياطي", width=500, height=400)
        ctk.CTkLabel(body, text=self._r("حماية البيانات"), font=("Arial", 16, "bold"), text_color=COLOR_GOLD).pack(pady=20)
        ctk.CTkButton(body, text=self._r("💾 إنشاء نسخة احتياطية"), height=50,
                      fg_color=COLOR_GREEN, command=self._backup_db).pack(fill="x", padx=40, pady=10)
        ctk.CTkFrame(body, height=2, fg_color=COLOR_BORDER).pack(fill="x", padx=20, pady=30)
        ctk.CTkButton(body, text=self._r("🔄 استعادة نسخة احتياطية"), height=50,
                      fg_color=COLOR_RED, command=self._restore_db).pack(fill="x", padx=40, pady=10)

    def _backup_db(self):
        path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("DB Files", "*.db")], title="حفظ")
        if path:
            try:
                shutil.copy2(DB_PATH, path)
                messagebox.showinfo("نجاح", "تم الحفظ بنجاح.")
            except Exception as e: messagebox.showerror("خطأ", str(e))

    def _restore_db(self):
        path = filedialog.askopenfilename(filetypes=[("DB Files", "*.db")], title="اختر")
        if path and messagebox.askyesno("تأكيد", "سيتم حذف البيانات الحالية واستبدالها، هل أنت متأكد؟"):
            try:
                shutil.copy2(path, DB_PATH)
                self._load_contacts()
                messagebox.showinfo("نجاح", "تمت الاستعادة بنجاح.")
            except Exception as e: messagebox.showerror("خطأ", str(e))

    # ── Add / Edit ───────────────────────────────────────
    def _open_add(self): self._contact_form()
    def _open_edit(self, cid):
        rows = db_query("SELECT * FROM contacts WHERE id=?", (cid,))
        if rows: self._contact_form(dict(rows[0]))

    def _contact_form(self, data=None):
        import tkinter as tk
        title = "➕ إضافة" if not data else "✏ تعديل"
        body = self._make_panel(title, width=520, height=760)
        fields = {}

        # ── helper: plain entry ───────────────────────────
        def add_entry(label, key, pre=None):
            ctk.CTkLabel(body, text=label, font=("Arial",12,"bold"),
                         text_color=COLOR_TEXT_SEC, anchor="e").pack(fill="x", padx=20, pady=(14,4))
            e = ctk.CTkEntry(body, height=42, font=("Arial",14),
                             fg_color=COLOR_BG, border_color=COLOR_BORDER,
                             text_color=COLOR_TEXT_PRI, justify="right")
            e.pack(fill="x", padx=20)
            if pre: e.insert(0, pre)
            fields[key] = e

        # ── helper: autocomplete entry ────────────────────
        def add_autocomplete(label, key, choices, pre=None):
            ctk.CTkLabel(body, text=label, font=("Arial",12,"bold"),
                         text_color=COLOR_TEXT_SEC, anchor="e").pack(fill="x", padx=20, pady=(14,4))
            wrapper = ctk.CTkFrame(body, fg_color="transparent")
            wrapper.pack(fill="x", padx=20)

            var = tk.StringVar(value=pre or "")
            entry = ctk.CTkEntry(wrapper, textvariable=var, height=42, font=("Arial",14),
                                 fg_color=COLOR_BG, border_color=COLOR_BORDER,
                                 text_color=COLOR_TEXT_PRI, justify="right")
            entry.pack(fill="x")

            # Dropdown listbox (hidden by default)
            is_dark = ctk.get_appearance_mode() == "Dark"
            lb_bg   = "#1C2128" if is_dark else "#FFFFFF"
            lb_fg   = "#E6EDF3" if is_dark else "#24292E"
            lb_frame = tk.Frame(body, bg=lb_bg, relief="flat", bd=1)
            lb = tk.Listbox(lb_frame, font=("Arial",13), bg=lb_bg, fg=lb_fg,
                            selectbackground=COLOR_GOLD, selectforeground="#000",
                            activestyle="none", bd=0, highlightthickness=0,
                            justify="right", height=5)
            lb.pack(fill="both", expand=True, padx=1, pady=1)

            def show_suggestions(*_):
                q = var.get().strip()
                matches = [c for c in choices if q.lower() in c.lower()] if q else choices
                lb.delete(0, "end")
                if matches and q != lb.get("active"):
                    for m in matches[:8]:
                        lb.insert("end", m)
                    lb_frame.place(in_=wrapper, x=0, rely=1.0, relwidth=1.0)
                    lb_frame.lift()
                else:
                    lb_frame.place_forget()

            def on_select(event):
                sel = lb.curselection()
                if sel:
                    var.set(lb.get(sel[0]))
                    lb_frame.place_forget()
                    entry.focus()

            def on_focus_out(event):
                body.after(150, lb_frame.place_forget)

            var.trace_add("write", show_suggestions)
            lb.bind("<<ListboxSelect>>", on_select)
            entry.bind("<FocusOut>", on_focus_out)
            entry.bind("<Escape>", lambda e: lb_frame.place_forget())
            entry.bind("<Down>", lambda e: lb.focus_set())
            lb.bind("<Return>", on_select)

            fields[key] = entry
            fields[key + "_var"] = var

        # ── fetch existing values ─────────────────────────
        units    = sorted({r["unit"]    for r in db_query("SELECT DISTINCT unit    FROM contacts") if r["unit"]})
        subunits = sorted({r["subunit"] for r in db_query("SELECT DISTINCT subunit FROM contacts") if r["subunit"]})
        ranks    = sorted({r["rank"]    for r in db_query("SELECT DISTINCT rank    FROM contacts") if r["rank"]})

        # ── build form ────────────────────────────────────
        add_entry("الاسم الكامل *", "name", data.get("name") if data else None)
        add_autocomplete("الرتبة", "rank", ranks, data.get("rank") if data else None)
        add_autocomplete("التشكيل", "unit", units, data.get("unit") if data else None)
        add_autocomplete("الفرع (اختياري)", "subunit", subunits, data.get("subunit") if data else None)
        add_entry("هاتف رئيسي *", "phone1", data.get("phone1") if data else None)
        add_entry("هاتف إضافي",   "phone2", data.get("phone2") if data else None)
        add_entry("ملاحظات",      "notes",  data.get("notes")  if data else None)

        def get_val(key):
            if key + "_var" in fields:
                return fields[key + "_var"].get().strip()
            return fields[key].get().strip()

        def save():
            name  = get_val("name")
            p1    = get_val("phone1")
            if not name or not p1:
                return
            vals = (name, get_val("rank"), get_val("unit"), get_val("subunit"),
                    p1, get_val("phone2"), get_val("notes"))
            if data:
                db_exec("UPDATE contacts SET name=?,rank=?,unit=?,subunit=?,phone1=?,phone2=?,notes=? WHERE id=?",
                        vals + (data["id"],))
            else:
                db_exec("INSERT INTO contacts (name,rank,unit,subunit,phone1,phone2,notes) VALUES (?,?,?,?,?,?,?)", vals)
            self._close_panel(); self._search()

        ctk.CTkButton(body, text="💾 حفظ", height=48, fg_color=COLOR_GOLD,
                      hover_color=COLOR_GOLD_HOV, text_color="#000",
                      font=("Arial",14,"bold"), command=save).pack(fill="x", padx=20, pady=20)

    def _delete(self, cid):
        if messagebox.askyesno("حذف", "هل أنت متأكد؟"):
            db_exec("DELETE FROM contacts WHERE id=?", (cid,))
            self._search()

    # ── Users ────────────────────────────────────────────
    def _manage_users(self):
        body = self._make_panel("👤 المستخدمين", width=500, height=600)
        list_f = ctk.CTkFrame(body, fg_color=COLOR_BG, corner_radius=10)
        list_f.pack(fill="x", padx=20, pady=10)
        def rf():
            for w in list_f.winfo_children(): w.destroy()
            for u in db_query("SELECT * FROM users ORDER BY is_admin DESC"):
                row = ctk.CTkFrame(list_f, fg_color=COLOR_CARD, height=40); row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"{u['username']} ({'مدير' if u['is_admin'] else 'مستخدم'})").pack(side="right", padx=10)
                if u["username"] != "admin":
                    ctk.CTkButton(row, text="حذف", width=60, command=lambda i=u['id']: [db_exec("DELETE FROM users WHERE id=?", (i,)), rf()]).pack(side="left", padx=10)
        rf()
        ctk.CTkLabel(body, text="إضافة مستخدم").pack(pady=10)
        u_en = ctk.CTkEntry(body, placeholder_text="اسم المستخدم"); u_en.pack(padx=20, fill="x", pady=5)
        p_en = ctk.CTkEntry(body, placeholder_text="كلمة المرور", show="●"); p_en.pack(padx=20, fill="x", pady=5)
        is_adm = ctk.BooleanVar()
        ctk.CTkCheckBox(body, text="مدير", variable=is_adm).pack(pady=5)
        def add():
            u, p = u_en.get().strip(), p_en.get().strip()
            if u and p:
                db_exec("INSERT INTO users (username,password,is_admin) VALUES (?,?,?)", (u, hashlib.sha256(p.encode()).hexdigest(), int(is_adm.get())))
                rf()
        ctk.CTkButton(body, text="إضافة", command=add).pack(pady=10)

    def _logout(self):
        if messagebox.askyesno("خروج", "هل تريد الخروج؟"): self.destroy(); main()

def main():
    import traceback
    try:
        init_db()
        login = LoginWindow()
        login.mainloop()
        if login.logged_user:
            app = PhoneBookApp(login.logged_user)
            app.mainloop()
    except Exception as e:
        with open("error_log.txt", "w", encoding="utf-8") as f: f.write(traceback.format_exc())
        messagebox.showerror("خطأ", f"حدث خطأ، راجع error_log.txt\n{e}")

if __name__ == "__main__":
    main()
