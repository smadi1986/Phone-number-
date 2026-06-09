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

        self._side_btn("\u202b📋 كل جهات الاتصال\u202c", self._show_all)
        if self.user["is_admin"]:
            self._side_btn("\u202b➕ إضافة جهة اتصال\u202c",  self._open_add)
            self._side_btn("\u202b📥 استيراد من Excel\u202c", self._import_excel)
        self._side_btn("\u202b📤 تصدير البيانات\u202c",  self._export_csv)
        if self.user["is_admin"]:
            self._side_btn("\u202b💾 نسخة احتياطية\u202c", self._manage_backup)
            self._side_btn("\u202b👤 إدارة المستخدمين\u202c", self._manage_users)

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

        ctk.CTkLabel(fbar, text="\u202bتصفية حسب القسم:\u202c", font=("Arial",13, "bold"),
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

        COLS = [("هاتف 2",150),("الهاتف الرئيسي",150),
                ("القسم",180),("الرتبة",150),("الاسم",250),("#",60)]
        if self.user["is_admin"]:
            COLS.insert(0, ("إجراءات",130))

        hdr = ctk.CTkFrame(self.content, fg_color=COLOR_CARD, height=45, corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        hdr.pack(fill="x", side="top", padx=10)
        hdr.pack_propagate(False)
        for txt, w in COLS:
            ctk.CTkLabel(hdr, text=txt, font=("Arial",13,"bold"),
                         text_color=COLOR_GOLD, width=w, anchor="center").pack(side="left", padx=2)

        self.scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, side="top", padx=10, pady=(0, 10))

    def _side_btn(self, label, cmd):
        ctk.CTkButton(self.sidebar, text=label, height=45,
                      fg_color="transparent", hover_color=COLOR_BG,
                      text_color=COLOR_TEXT_PRI, font=("Arial",14), anchor="e",
                      command=cmd).pack(padx=15, pady=5, fill="x")

    def _toggle_appearance(self):
        ctk.set_appearance_mode("Light" if ctk.get_appearance_mode() == "Dark" else "Dark")

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

        # Use RLM marker (\u200f) at the beginning for better Arabic rendering in the dropdown
        raw_units = sorted({r["unit"] for r in db_query("SELECT DISTINCT unit FROM contacts") if r["unit"]})
        display_units = ["الكل"] + [f"\u200f{u}" for u in raw_units]
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
            if self.user["is_admin"]:
                act = ctk.CTkFrame(row_f, fg_color="transparent", width=130)
                act.pack(side="left", padx=5)
                act.pack_propagate(False)
                ctk.CTkButton(act, text="✏", width=40, height=35, fg_color=COLOR_BLUE, hover_color="#1D4ED8",
                              text_color="white", font=("Arial",14), command=lambda i=rid: self._open_edit(i)).pack(side="left", padx=5, pady=10)
                ctk.CTkButton(act, text="🗑", width=40, height=35, fg_color=COLOR_RED, hover_color="#B91C1C",
                              text_color="white", font=("Arial",14), command=lambda i=rid: self._delete(i)).pack(side="left", padx=5, pady=10)

            cols_data = [(r["phone2"] or "—", 150), (r["phone1"], 150), (r["unit"] or "—", 180),
                         (r["rank"] or "—", 150), (r["name"], 250), (str(i+1), 60)]
            for val, w in cols_data:
                ctk.CTkLabel(row_f, text=str(val), font=("Arial",14), text_color=COLOR_TEXT_PRI, width=w, anchor="center").pack(side="left", padx=2)

        if not rows:
            ctk.CTkLabel(self.scroll, text="لا توجد نتائج بحث", font=("Arial",16), text_color=COLOR_TEXT_SEC).pack(pady=100)

    def _search(self):
        q = self.search_var.get().strip()
        # Clean direction marks for database query
        unit_raw = self.unit_var.get()
        unit = unit_raw.replace("\u202b", "").replace("\u202c", "").replace("\u200f", "").replace("\u200e", "")

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
                            str(row.get("القسم", "")).strip() if pd.notna(row.get("القسم")) else "",
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
                w.writerow(["الاسم","الرتبة","القسم","هاتف 1","هاتف 2","ملاحظات"])
                for r in rows: w.writerow(list(r))
            messagebox.showinfo("نجاح", "تم التصدير بنجاح.")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل التصدير: {e}")

    # ── Backup ───────────────────────────────────────────
    def _manage_backup(self):
        # Apply RLE marker (\u202b) to fix Arabic word order on buttons and titles
        body = self._make_panel("\u202b💾 النسخ الاحتياطي\u202c", width=500, height=400)
        ctk.CTkLabel(body, text="\u202bحماية البيانات\u202c", font=("Arial", 16, "bold"), text_color=COLOR_GOLD).pack(pady=20)
        ctk.CTkButton(body, text="\u202b💾 إنشاء نسخة احتياطية\u202c", height=50, fg_color=COLOR_GREEN, command=self._backup_db).pack(fill="x", padx=40, pady=10)
        ctk.CTkFrame(body, height=2, fg_color=COLOR_BORDER).pack(fill="x", padx=20, pady=30)
        ctk.CTkButton(body, text="\u202b🔄 استعادة نسخة احتياطية\u202c", height=50, fg_color=COLOR_RED, command=self._restore_db).pack(fill="x", padx=40, pady=10)

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
        title = "➕ إضافة" if not data else "✏ تعديل"
        body = self._make_panel(title, width=500, height=650)
        fields = {}
        specs = [("الاسم الكامل *", "name"), ("الرتبة", "rank"), ("القسم", "unit"), ("هاتف رئيسي *", "phone1"), ("هاتف إضافي", "phone2"), ("ملاحظات", "notes")]
        for lbl, key in specs:
            ctk.CTkLabel(body, text=lbl, font=("Arial",12,"bold"), text_color=COLOR_TEXT_SEC, anchor="e").pack(fill="x", padx=20, pady=(15,5))
            e = ctk.CTkEntry(body, height=45, font=("Arial",14), fg_color=COLOR_BG, border_color=COLOR_BORDER, text_color=COLOR_TEXT_PRI, justify="right")
            e.pack(fill="x", padx=20)
            if data and data.get(key): e.insert(0, data[key])
            fields[key] = e
        def save():
            name, p1 = fields["name"].get().strip(), fields["phone1"].get().strip()
            if not name or not p1: return
            vals = (name, fields["rank"].get().strip(), fields["unit"].get().strip(), p1, fields["phone2"].get().strip(), fields["notes"].get().strip())
            if data: db_exec("UPDATE contacts SET name=?,rank=?,unit=?,phone1=?,phone2=?,notes=? WHERE id=?", vals + (data["id"],))
            else: db_exec("INSERT INTO contacts (name,rank,unit,phone1,phone2,notes) VALUES (?,?,?,?,?,?)", vals)
            self._close_panel(); self._search()
        ctk.CTkButton(body, text="💾 حفظ", height=50, fg_color=COLOR_GOLD, command=save).pack(fill="x", padx=20, pady=20)

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
