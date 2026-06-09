import customtkinter as ctk
import sqlite3
import os
import csv
from tkinter import messagebox, filedialog
import hashlib

# ─── Configuration & Theme ────────────────────────────────
ctk.set_appearance_mode("dark")  # Default to dark as per original
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
            phone1   TEXT    NOT NULL,
            phone2   TEXT,
            notes    TEXT,
            created  TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
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
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _build(self):
        # Header
        ctk.CTkLabel(self, text="☎", font=("Arial", 64), text_color=COLOR_GOLD).pack(pady=(50,0))
        ctk.CTkLabel(self, text="دليل الهاتف المؤسسي",
                     font=("Arial", 24, "bold"), text_color=COLOR_TEXT_PRI).pack(pady=(8,4))
        ctk.CTkLabel(self, text="سجّل دخولك للمتابعة",
                     font=("Arial", 14), text_color=COLOR_TEXT_SEC).pack(pady=(0,30))

        # Login Frame
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

        # Footer
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(pady=20)
        ctk.CTkLabel(info_frame, text="المستخدم الافتراضي: admin | كلمة المرور: admin123",
                     font=("Arial",11), text_color=COLOR_TEXT_SEC).pack()

        # Appearance Toggle
        self.appearance_mode_btn = ctk.CTkButton(self, text="تبديل المظهر", width=100, height=30,
                                               fg_color="transparent", border_width=1,
                                               border_color=COLOR_BORDER, text_color=COLOR_TEXT_SEC,
                                               command=self._toggle_appearance)
        self.appearance_mode_btn.pack(pady=10)

    def _toggle_appearance(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

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

        # Initialize variables before building UI to avoid trace issues
        self.search_var = ctk.StringVar()
        self.unit_var = ctk.StringVar(value="الكل")

        self._build()
        self._load_contacts()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _build(self):
        # ── Sidebar (Right Side)
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color=COLOR_CARD,
                                    corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar Header
        ctk.CTkLabel(self.sidebar, text="☎ الدليل",
                     font=("Arial",22,"bold"), text_color=COLOR_GOLD).pack(pady=(30,5))
        ctk.CTkLabel(self.sidebar, text=f"مرحباً، {self.user['username']}",
                     font=("Arial",14), text_color=COLOR_TEXT_SEC).pack(pady=(0,30))

        # Sidebar Buttons
        self._side_btn("📋 كل جهات الاتصال", self._show_all)
        if self.user["is_admin"]:
            self._side_btn("➕ إضافة جهة اتصال",  self._open_add)
        self._side_btn("📤 تصدير البيانات",  self._export_csv)
        if self.user["is_admin"]:
            self._side_btn("👤 إدارة المستخدمين", self._manage_users)

        # Theme Toggle Button in Sidebar
        self.theme_btn = ctk.CTkButton(self.sidebar, text="🌓 تبديل المظهر",
                                      fg_color="transparent", hover_color=COLOR_BG,
                                      text_color=COLOR_TEXT_PRI, font=("Arial",13),
                                      command=self._toggle_appearance)
        self.theme_btn.pack(side="bottom", pady=(0, 10), padx=20, fill="x")

        # Logout Button
        ctk.CTkButton(self.sidebar, text="🚪 تسجيل خروج",
                      fg_color="transparent", hover_color=COLOR_RED_LOW,
                      text_color=COLOR_RED, font=("Arial",13, "bold"),
                      command=self._logout).pack(side="bottom", pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.sidebar, text="v3.0", font=("Arial",10),
                     text_color=COLOR_TEXT_SEC).pack(side="bottom", pady=(0,10))

        # ── Content area
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        # Topbar
        topbar = ctk.CTkFrame(self.content, fg_color=COLOR_CARD, height=80,
                              corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        # Search Bar
        self.search_var.trace_add("write", lambda *_: self._search())
        srch = ctk.CTkEntry(topbar, textvariable=self.search_var,
                            placeholder_text="🔍 بحث بالاسم، الرتبة أو القسم...",
                            height=42, width=450, font=("Arial",14),
                            fg_color=COLOR_BG, border_color=COLOR_BORDER,
                            text_color=COLOR_TEXT_PRI, justify="right")
        srch.pack(side="right", padx=25, pady=19)

        self.count_lbl = ctk.CTkLabel(topbar, text="", font=("Arial",14), text_color=COLOR_TEXT_SEC)
        self.count_lbl.pack(side="left", padx=25)

        # Filter bar
        fbar = ctk.CTkFrame(self.content, fg_color="transparent", height=60, corner_radius=0)
        fbar.pack(fill="x", side="top")
        fbar.pack_propagate(False)

        ctk.CTkLabel(fbar, text="تصفية حسب القسم:", font=("Arial",13, "bold"),
                     text_color=COLOR_TEXT_PRI).pack(side="right", padx=(0,25), pady=15)
        self.unit_menu = ctk.CTkOptionMenu(fbar, variable=self.unit_var,
                                           values=["الكل"], width=200, height=35,
                                           fg_color=COLOR_CARD, button_color=COLOR_GOLD,
                                           button_hover_color=COLOR_GOLD_HOV,
                                           dropdown_fg_color=COLOR_CARD,
                                           text_color=COLOR_TEXT_PRI,
                                           anchor="e",
                                           command=self._handle_unit_change)
        self.unit_menu.pack(side="right", padx=10, pady=12)

        # Table header
        # Order: Actions | Phone 2 | Phone 1 | Unit | Rank | Name | #
        COLS = [("هاتف 2",150),("الهاتف الرئيسي",150),
                ("القسم",180),("الرتبة",150),("الاسم",250),("#",60)]

        # Add Actions column only for admins
        if self.user["is_admin"]:
            COLS.insert(0, ("إجراءات",130))

        hdr = ctk.CTkFrame(self.content, fg_color=COLOR_CARD, height=45, corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        hdr.pack(fill="x", side="top", padx=10)
        hdr.pack_propagate(False)
        for txt, w in COLS:
            ctk.CTkLabel(hdr, text=txt, font=("Arial",13,"bold"),
                         text_color=COLOR_GOLD, width=w, anchor="center").pack(side="left", padx=2)

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, side="top", padx=10, pady=(0, 10))

    def _side_btn(self, label, cmd):
        ctk.CTkButton(self.sidebar, text=label, height=45,
                      fg_color="transparent", hover_color=COLOR_BG,
                      text_color=COLOR_TEXT_PRI, font=("Arial",14), anchor="e",
                      command=cmd).pack(padx=15, pady=5, fill="x")

    def _toggle_appearance(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

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
        win.transient(self)      # Make it stay on top of main window
        win.grab_set()           # Make it modal
        self._panel = win

        # Center top level
        self.update_idletasks()
        rx = self.winfo_x() + (self.winfo_width()  - width)  // 2
        ry = self.winfo_y() + (self.winfo_height() - height) // 2
        win.geometry(f"{width}x{height}+{rx}+{ry}")

        win.lift()               # Bring to front
        win.focus_force()        # Take focus

        # Header
        hdr = ctk.CTkFrame(win, fg_color=COLOR_BG, height=60, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=title, font=("Arial",18,"bold"),
                     text_color=COLOR_GOLD).pack(side="right", padx=20, pady=15)
        ctk.CTkButton(hdr, text="إلغاء", width=100, height=35,
                      fg_color=COLOR_RED, hover_color="#B91C1C",
                      text_color="white", font=("Arial",13,"bold"),
                      command=self._close_panel).pack(side="left", padx=15, pady=12)

        body = ctk.CTkScrollableFrame(win, fg_color="transparent", corner_radius=0,
                                      width=width-20, height=height-80)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        return body

    # ── Data ────────────────────────────────────────────
    def _rev_w(self, s):
        """Reverses word order in a string to fix display in some LTR environments."""
        if not s or s == "الكل": return s
        # Split by whitespace and reverse the list of words
        return " ".join(s.split()[::-1])

    def _handle_unit_change(self, val):
        # The value passed is what the user selected (which might be word-reversed)
        # We search using the original value. We'll find it by re-reversing.
        # But we need to make sure search uses the clean value.
        self._search()

    def _load_contacts(self, rows=None):
        if rows is None:
            rows = db_query("SELECT * FROM contacts ORDER BY name")

        # Manually reverse word order for the dropdown to counteract the LTR display issue
        raw_units = sorted({r["unit"] for r in db_query("SELECT DISTINCT unit FROM contacts") if r["unit"]})
        display_units = ["الكل"] + [self._rev_w(u) for u in raw_units]

        self.unit_menu.configure(values=display_units)

        for w in self.scroll.winfo_children():
            w.destroy()

        self.count_lbl.configure(text=f"إجمالي: {len(rows)} جهة اتصال")

        for i, r in enumerate(rows):
            bg = COLOR_CARD if i % 2 == 0 else COLOR_BG
            row_f = ctk.CTkFrame(self.scroll, fg_color=bg, height=55, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
            row_f.pack(fill="x", pady=2, padx=5)
            row_f.pack_propagate(False)

            rid = r["id"]

            # Actions (Only for Admin)
            if self.user["is_admin"]:
                act = ctk.CTkFrame(row_f, fg_color="transparent", width=130)
                act.pack(side="left", padx=5)
                act.pack_propagate(False)

                ctk.CTkButton(act, text="✏", width=40, height=35,
                              fg_color=COLOR_BLUE, hover_color="#1D4ED8",
                              text_color="white", font=("Arial",14),
                              command=lambda i=rid: self._open_edit(i)).pack(side="left", padx=5, pady=10)

                ctk.CTkButton(act, text="🗑", width=40, height=35,
                              fg_color=COLOR_RED, hover_color="#B91C1C",
                              text_color="white", font=("Arial",14),
                              command=lambda i=rid: self._delete(i)).pack(side="left", padx=5, pady=10)

            # Data Columns
            cols_data = [
                (r["phone2"] or "—", 150),
                (r["phone1"],        150),
                (r["unit"] or "—",   180),
                (r["rank"] or "—",   150),
                (r["name"],          250),
                (str(i+1),            60),
            ]

            for val, w in cols_data:
                ctk.CTkLabel(row_f, text=str(val), font=("Arial",14),
                             text_color=COLOR_TEXT_PRI, width=w,
                             anchor="center").pack(side="left", padx=2)

        if not rows:
            ctk.CTkLabel(self.scroll, text="لا توجد نتائج بحث",
                         font=("Arial",16), text_color=COLOR_TEXT_SEC).pack(pady=100)

    def _search(self):
        q = self.search_var.get().strip()

        # Get the value from the menu variable
        unit_disp = self.unit_var.get()

        # If the value in the menu was word-reversed for display, we need the original for the DB.
        # Re-reversing "اللغات معهد" gives back "معهد اللغات".
        unit = self._rev_w(unit_disp)

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

    # ── Add / Edit ───────────────────────────────────────
    def _open_add(self):
        self._contact_form()

    def _open_edit(self, cid):
        rows = db_query("SELECT * FROM contacts WHERE id=?", (cid,))
        if rows:
            self._contact_form(dict(rows[0]))

    def _contact_form(self, data=None):
        title = "➕ إضافة جهة اتصال" if not data else "✏ تعديل جهة الاتصال"
        body = self._make_panel(title, width=500, height=650)

        fields = {}
        specs = [
            ("الاسم الكامل *",        "name"),
            ("الرتبة / الوظيفة",      "rank"),
            ("القسم / الوحدة",        "unit"),
            ("رقم الهاتف الرئيسي *",  "phone1"),
            ("رقم هاتف إضافي",        "phone2"),
            ("ملاحظات",               "notes"),
        ]

        for label, key in specs:
            ctk.CTkLabel(body, text=label, font=("Arial",13,"bold"),
                         text_color=COLOR_TEXT_SEC, anchor="e").pack(fill="x", padx=20, pady=(15,5))
            e = ctk.CTkEntry(body, height=45, font=("Arial",14),
                             fg_color=COLOR_BG, border_color=COLOR_BORDER,
                             text_color=COLOR_TEXT_PRI, justify="right")
            e.pack(fill="x", padx=20)
            if data and data.get(key):
                e.insert(0, data[key])
            fields[key] = e

        err = ctk.CTkLabel(body, text="", font=("Arial",12), text_color=COLOR_RED)
        err.pack(pady=(10,5))

        def save():
            name  = fields["name"].get().strip()
            phone = fields["phone1"].get().strip()
            if not name or not phone:
                err.configure(text="❌ الاسم ورقم الهاتف الرئيسي مطلوبان")
                return
            vals = (
                name,
                fields["rank"].get().strip(),
                fields["unit"].get().strip(),
                phone,
                fields["phone2"].get().strip(),
                fields["notes"].get().strip(),
            )
            if data:
                db_exec("UPDATE contacts SET name=?,rank=?,unit=?,phone1=?,phone2=?,notes=? WHERE id=?",
                        vals + (data["id"],))
                msg = f"✅ تم تعديل '{name}'"
            else:
                db_exec("INSERT INTO contacts (name,rank,unit,phone1,phone2,notes) VALUES (?,?,?,?,?,?)", vals)
                msg = f"✅ تمت إضافة '{name}'"
            self._close_panel()
            self._search()
            messagebox.showinfo("نجاح", msg)

        ctk.CTkButton(body, text="💾 حفظ البيانات", height=50,
                      fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOV,
                      text_color="white", font=("Arial",16,"bold"),
                      command=save).pack(fill="x", padx=20, pady=(10,10))

    # ── Delete ───────────────────────────────────────────
    def _delete(self, cid):
        rows = db_query("SELECT name FROM contacts WHERE id=?", (cid,))
        if rows and messagebox.askyesno("تأكيد الحذف",
                                        f"هل أنت متأكد من حذف '{rows[0]['name']}'؟"):
            db_exec("DELETE FROM contacts WHERE id=?", (cid,))
            self._search()

    # ── Export ───────────────────────────────────────────
    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV","*.csv")],
                                            title="تصدير الدليل")
        if not path:
            return
        rows = db_query("SELECT name,rank,unit,phone1,phone2,notes FROM contacts ORDER BY name")
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["الاسم","الرتبة","القسم","هاتف 1","هاتف 2","ملاحظات"])
                for r in rows:
                    w.writerow(list(r))
            messagebox.showinfo("تم التصدير", f"تم تصدير الدليل بنجاح إلى:\n{path}")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التصدير:\n{e}")

    # ── Users ────────────────────────────────────────────
    def _manage_users(self):
        body = self._make_panel("👤 إدارة المستخدمين", width=500, height=600)

        ctk.CTkLabel(body, text="المستخدمون الحاليون", font=("Arial",14,"bold"),
                     text_color=COLOR_GOLD).pack(pady=(10,10), padx=20, anchor="e")

        list_frame = ctk.CTkFrame(body, fg_color=COLOR_BG, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        list_frame.pack(fill="x", padx=20, pady=(0,20))

        def refresh_list():
            for w in list_frame.winfo_children():
                w.destroy()
            users = db_query("SELECT * FROM users ORDER BY is_admin DESC, username")
            if not users:
                ctk.CTkLabel(list_frame, text="لا يوجد مستخدمون",
                             font=("Arial",13), text_color=COLOR_TEXT_SEC).pack(pady=20)
                return
            for u in users:
                row = ctk.CTkFrame(list_frame, fg_color=COLOR_CARD, corner_radius=8, height=50)
                row.pack(fill="x", padx=10, pady=5)
                row.pack_propagate(False)

                badge = "👑 مدير" if u["is_admin"] else "👤 مستخدم"
                ctk.CTkLabel(row, text=f"{u['username']} ({badge})",
                             font=("Arial",14), text_color=COLOR_TEXT_PRI).pack(side="right", padx=15, pady=10)

                if u["username"] != "admin":
                    def make_del(uid):
                        return lambda: [db_exec("DELETE FROM users WHERE id=?", (uid,)), refresh_list()]
                    ctk.CTkButton(row, text="حذف", width=70, height=32,
                                  fg_color=COLOR_RED, hover_color="#B91C1C",
                                  text_color="white", font=("Arial",12),
                                  command=make_del(u["id"])).pack(side="left", padx=10, pady=9)

        refresh_list()

        ctk.CTkLabel(body, text="إضافة مستخدم جديد", font=("Arial",14,"bold"),
                     text_color=COLOR_GOLD).pack(pady=(10,10), padx=20, anchor="e")

        add_frame = ctk.CTkFrame(body, fg_color=COLOR_BG, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        add_frame.pack(fill="x", padx=20, pady=(0,10))

        ctk.CTkLabel(add_frame, text="اسم المستخدم", font=("Arial",13),
                     text_color=COLOR_TEXT_SEC, anchor="e").pack(fill="x", padx=15, pady=(15,5))
        nu = ctk.CTkEntry(add_frame, height=40, font=("Arial",14),
                          fg_color=COLOR_CARD, border_color=COLOR_BORDER,
                          text_color=COLOR_TEXT_PRI, justify="right")
        nu.pack(fill="x", padx=15)

        ctk.CTkLabel(add_frame, text="كلمة المرور", font=("Arial",13),
                     text_color=COLOR_TEXT_SEC, anchor="e").pack(fill="x", padx=15, pady=(10,5))
        np_ = ctk.CTkEntry(add_frame, height=40, font=("Arial",14), show="●",
                           fg_color=COLOR_CARD, border_color=COLOR_BORDER,
                           text_color=COLOR_TEXT_PRI, justify="right")
        np_.pack(fill="x", padx=15)

        adm_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(add_frame, text="منح صلاحيات مسؤول (مدير)", variable=adm_var,
                        text_color=COLOR_TEXT_PRI, font=("Arial",13)).pack(padx=15, pady=15, anchor="e")

        err_lbl = ctk.CTkLabel(add_frame, text="", font=("Arial",12), text_color=COLOR_RED)
        err_lbl.pack()

        def add_user():
            u2 = nu.get().strip()
            p2 = np_.get().strip()
            if not u2 or not p2:
                err_lbl.configure(text="❌ يرجى إدخال البيانات المطلوبة", text_color=COLOR_RED)
                return
            if len(p2) < 4:
                err_lbl.configure(text="❌ كلمة المرور قصيرة جداً (4 أحرف كحد أدنى)", text_color=COLOR_RED)
                return
            pw2 = hashlib.sha256(p2.encode()).hexdigest()
            try:
                db_exec("INSERT INTO users (username,password,is_admin) VALUES (?,?,?)",
                        (u2, pw2, int(adm_var.get())))
                nu.delete(0, "end")
                np_.delete(0, "end")
                adm_var.set(False)
                err_lbl.configure(text=f"✅ تم إضافة المستخدم '{u2}'", text_color=COLOR_GREEN)
                refresh_list()
            except Exception:
                err_lbl.configure(text="❌ اسم المستخدم موجود بالفعل", text_color=COLOR_RED)

        ctk.CTkButton(add_frame, text="➕ إضافة المستخدم", height=45,
                      fg_color=COLOR_GREEN, hover_color="#166534",
                      text_color="white", font=("Arial",14,"bold"),
                      command=add_user).pack(fill="x", padx=15, pady=(5,20))

    # ── Logout ───────────────────────────────────────────
    def _logout(self):
        if messagebox.askyesno("تسجيل خروج", "هل أنت متأكد من رغبتك في تسجيل الخروج؟"):
            self.destroy()
            main()

# ─── Entry ────────────────────────────────────────────────
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
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        messagebox.showerror("خطأ في البرنامج", f"حدث خطأ غير متوقع:\n{str(e)}\n\nتم حفظ التفاصيل في error_log.txt")

if __name__ == "__main__":
    main()
