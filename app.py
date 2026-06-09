import customtkinter as ctk
import sqlite3
import os
import csv
from tkinter import messagebox, filedialog
import hashlib

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DB_PATH = os.path.join(os.path.dirname(__file__), "phonebook.db")

DARK_BG    = "#0D1117"
CARD_BG    = "#161B22"
BORDER     = "#30363D"
GOLD       = "#D4A853"
GOLD_HOVER = "#C49743"
GOLD_DIM   = "#8B6914"
TEXT_PRI   = "#E6EDF3"
TEXT_SEC   = "#8B949E"
GREEN      = "#3FB950"
RED        = "#F85149"
BLUE       = "#58A6FF"

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
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self.logged_user = None
        self._build()
        self.eval('tk::PlaceWindow . center')

    def _build(self):
        ctk.CTkLabel(self, text="☎", font=("Arial", 56), text_color=GOLD).pack(pady=(50,0))
        ctk.CTkLabel(self, text="دليل الهاتف المؤسسي",
                     font=("Arial", 22, "bold"), text_color=TEXT_PRI).pack(pady=(8,4))
        ctk.CTkLabel(self, text="سجّل دخولك للمتابعة",
                     font=("Arial", 13), text_color=TEXT_SEC).pack(pady=(0,30))

        frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        frame.pack(padx=36, fill="x")

        ctk.CTkLabel(frame, text="اسم المستخدم", font=("Arial",13,"bold"),
                     text_color=TEXT_SEC, anchor="e").pack(padx=20, pady=(20,4), fill="x")
        self.user_entry = ctk.CTkEntry(frame, height=40, font=("Arial",14),
                                       fg_color=DARK_BG, border_color=BORDER,
                                       text_color=TEXT_PRI, justify="right")
        self.user_entry.pack(padx=20, fill="x")

        ctk.CTkLabel(frame, text="كلمة المرور", font=("Arial",13,"bold"),
                     text_color=TEXT_SEC, anchor="e").pack(padx=20, pady=(14,4), fill="x")
        self.pass_entry = ctk.CTkEntry(frame, height=40, font=("Arial",14), show="●",
                                       fg_color=DARK_BG, border_color=BORDER,
                                       text_color=TEXT_PRI, justify="right")
        self.pass_entry.pack(padx=20, fill="x")
        self.pass_entry.bind("<Return>", lambda e: self._login())

        self.err_lbl = ctk.CTkLabel(frame, text="", font=("Arial",12), text_color=RED)
        self.err_lbl.pack(pady=(8,0))

        ctk.CTkButton(frame, text="دخول", height=42, font=("Arial",15,"bold"),
                      fg_color=GOLD, hover_color=GOLD_HOVER,
                      text_color="#000000", command=self._login).pack(padx=20, pady=(10,20), fill="x")

        ctk.CTkLabel(self, text="المستخدم الافتراضي: admin  |  كلمة المرور: admin123",
                     font=("Arial",11), text_color=GOLD_DIM).pack(pady=(16,0))

    def _login(self):
        u = self.user_entry.get().strip()
        p = hashlib.sha256(self.pass_entry.get().encode()).hexdigest()
        rows = db_query("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        if rows:
            self.logged_user = dict(rows[0])
            self.destroy()
        else:
            self.err_lbl.configure(text="❌  اسم المستخدم أو كلمة المرور غير صحيحة")

# ─── Main App ─────────────────────────────────────────────
class PhoneBookApp(ctk.CTk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"دليل الهاتف المؤسسي  —  {user['username']}")
        self.geometry("1150x700")
        self.minsize(950, 580)
        self.configure(fg_color=DARK_BG)
        self._panel = None
        self._build()
        self._load_contacts()
        self.eval('tk::PlaceWindow . center')

    def _build(self):
        # ── Sidebar
        self.sidebar = ctk.CTkFrame(self, width=230, fg_color=CARD_BG,
                                    corner_radius=0, border_width=1, border_color=BORDER)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="☎  الدليل",
                     font=("Arial",18,"bold"), text_color=GOLD).pack(pady=(24,4))
        ctk.CTkLabel(self.sidebar, text=f"مرحباً، {self.user['username']}",
                     font=("Arial",12), text_color=TEXT_SEC).pack(pady=(0,20))

        self._side_btn("📋  كل جهات الاتصال", self._show_all)
        self._side_btn("➕  إضافة جهة اتصال",  self._open_add)
        self._side_btn("📤  تصدير Excel / CSV",  self._export_csv)
        if self.user["is_admin"]:
            self._side_btn("👤  إدارة المستخدمين", self._manage_users)

        ctk.CTkButton(self.sidebar, text="🚪  تسجيل خروج",
                      fg_color="transparent", hover_color="#1C2128",
                      text_color=RED, font=("Arial",13),
                      command=self._logout).pack(side="bottom", pady=20, padx=16, fill="x")
        ctk.CTkLabel(self.sidebar, text="v2.2", font=("Arial",10),
                     text_color=BORDER).pack(side="bottom", pady=(0,6))

        # ── Content area
        self.content = ctk.CTkFrame(self, fg_color=DARK_BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        # Topbar
        topbar = ctk.CTkFrame(self.content, fg_color=CARD_BG, height=64,
                              corner_radius=0, border_width=1, border_color=BORDER)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._search())
        srch = ctk.CTkEntry(topbar, textvariable=self.search_var,
                            placeholder_text="🔍  بحث بالاسم أو الرتبة أو القسم...",
                            height=38, width=400, font=("Arial",13),
                            fg_color=DARK_BG, border_color=BORDER,
                            text_color=TEXT_PRI, justify="right")
        srch.pack(side="right", padx=20, pady=13)

        self.count_lbl = ctk.CTkLabel(topbar, text="", font=("Arial",13), text_color=TEXT_SEC)
        self.count_lbl.pack(side="left", padx=20)

        # Filter bar
        fbar = ctk.CTkFrame(self.content, fg_color=DARK_BG, height=46, corner_radius=0)
        fbar.pack(fill="x", side="top")
        fbar.pack_propagate(False)

        ctk.CTkLabel(fbar, text="فلترة حسب القسم:", font=("Arial",12),
                     text_color=TEXT_SEC).pack(side="right", padx=(0,12), pady=10)
        self.unit_var = ctk.StringVar(value="الكل")
        self.unit_menu = ctk.CTkOptionMenu(fbar, variable=self.unit_var,
                                           values=["الكل"], width=180,
                                           fg_color=CARD_BG, button_color=GOLD,
                                           button_hover_color=GOLD_HOVER,
                                           dropdown_fg_color=CARD_BG,
                                           text_color=TEXT_PRI,
                                           command=lambda _: self._search())
        self.unit_menu.pack(side="right", padx=4, pady=6)

        # Table header
        # الأعمدة من اليسار لليمين: إجراءات | هاتف2 | هاتف رئيسي | قسم | رتبة | اسم | #
        COLS = [("إجراءات",120),("هاتف 2",130),("الهاتف الرئيسي",150),
                ("القسم",160),("الرتبة",140),("الاسم",220),("#",50)]
        hdr = ctk.CTkFrame(self.content, fg_color="#1C2128", height=36, corner_radius=0)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)
        for txt, w in COLS:
            ctk.CTkLabel(hdr, text=txt, font=("Arial",12,"bold"),
                         text_color=GOLD, width=w, anchor="center").pack(side="left", padx=2)

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self.content, fg_color=DARK_BG, corner_radius=0)
        self.scroll.pack(fill="both", expand=True, side="top")

    def _side_btn(self, label, cmd):
        ctk.CTkButton(self.sidebar, text=label, height=42,
                      fg_color="transparent", hover_color="#1C2128",
                      text_color=TEXT_PRI, font=("Arial",13), anchor="e",
                      command=cmd).pack(padx=10, pady=3, fill="x")

    # ── Panel (Toplevel مستقل — الحل الأبسط والأموثوق) ──
    def _close_panel(self):
        if self._panel and self._panel.winfo_exists():
            self._panel.destroy()
        self._panel = None

    def _make_panel(self, title, width=460, height=580):
        self._close_panel()

        win = ctk.CTkToplevel(self)
        win.title(title)
        win.configure(fg_color=CARD_BG)
        win.resizable(False, False)
        self._panel = win

        # توسيط النافذة فوق النافذة الرئيسية
        self.update_idletasks()
        rx = self.winfo_x() + (self.winfo_width()  - width)  // 2
        ry = self.winfo_y() + (self.winfo_height() - height) // 2
        win.geometry(f"{width}x{height}+{rx}+{ry}")

        # إظهار النافذة فوق كل شيء مع تأخير بسيط لتجنب الشاشة السوداء
        win.attributes("-topmost", True)
        win.after(150, lambda: win.attributes("-topmost", False))
        win.after(200, win.focus_force)

        # Header
        hdr = ctk.CTkFrame(win, fg_color="#1C2128", height=52, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=title, font=("Arial",15,"bold"),
                     text_color=GOLD).pack(side="right", padx=16, pady=12)
        ctk.CTkButton(hdr, text="✕  إغلاق", width=90, height=32,
                      fg_color=RED, hover_color="#C44040",
                      text_color="white", font=("Arial",12,"bold"),
                      command=self._close_panel).pack(side="left", padx=12, pady=10)

        body = ctk.CTkScrollableFrame(win, fg_color=CARD_BG, corner_radius=0,
                                      width=width-20, height=height-70)
        body.pack(fill="both", expand=True)
        return body

    # ── Data ────────────────────────────────────────────
    def _load_contacts(self, rows=None):
        if rows is None:
            rows = db_query("SELECT * FROM contacts ORDER BY name")

        units = ["الكل"] + sorted({r["unit"] for r in db_query("SELECT DISTINCT unit FROM contacts") if r["unit"]})
        self.unit_menu.configure(values=units)

        for w in self.scroll.winfo_children():
            w.destroy()

        self.count_lbl.configure(text=f"إجمالي: {len(rows)} جهة اتصال")

        for i, r in enumerate(rows):
            bg = CARD_BG if i % 2 == 0 else "#111820"
            row_f = ctk.CTkFrame(self.scroll, fg_color=bg, height=48, corner_radius=0)
            row_f.pack(fill="x", pady=1)
            row_f.pack_propagate(False)

            rid = r["id"]

            # إجراءات (أقصى اليسار)
            act = ctk.CTkFrame(row_f, fg_color="transparent", width=120)
            act.pack(side="left", padx=6)
            act.pack_propagate(False)
            ctk.CTkButton(act, text="✏", width=36, height=30,
                          fg_color=BLUE, hover_color="#3A7FCC",
                          text_color="white", font=("Arial",13),
                          command=lambda i=rid: self._open_edit(i)).pack(side="left", padx=3, pady=9)
            ctk.CTkButton(act, text="🗑", width=36, height=30,
                          fg_color=RED, hover_color="#C44040",
                          text_color="white", font=("Arial",13),
                          command=lambda i=rid: self._delete(i)).pack(side="left", padx=3, pady=9)

            # البيانات من اليسار: هاتف2 | هاتف1 | قسم | رتبة | اسم | #
            for val, w in [
                (r["phone2"] or "—", 130),
                (r["phone1"],        150),
                (r["unit"] or "—",   160),
                (r["rank"] or "—",   140),
                (r["name"],          220),
                (str(i+1),            50),
            ]:
                ctk.CTkLabel(row_f, text=str(val), font=("Arial",13),
                             text_color=TEXT_PRI, width=w,
                             anchor="center").pack(side="left", padx=2)

        if not rows:
            ctk.CTkLabel(self.scroll, text="لا توجد نتائج",
                         font=("Arial",15), text_color=TEXT_SEC).pack(pady=60)

    def _search(self):
        q = self.search_var.get().strip()
        unit = self.unit_var.get()
        params = []
        sql = "SELECT * FROM contacts WHERE 1=1"
        if q:
            sql += " AND (name LIKE ? OR rank LIKE ? OR unit LIKE ? OR phone1 LIKE ?)"
            params += [f"%{q}%"] * 4
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
        title = "➕  إضافة جهة اتصال" if not data else "✏  تعديل جهة الاتصال"
        body = self._make_panel(title, width=460, height=590)

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
            ctk.CTkLabel(body, text=label, font=("Arial",12,"bold"),
                         text_color=TEXT_SEC, anchor="e").pack(fill="x", padx=16, pady=(12,3))
            e = ctk.CTkEntry(body, height=38, font=("Arial",13),
                             fg_color=DARK_BG, border_color=BORDER,
                             text_color=TEXT_PRI, justify="right")
            e.pack(fill="x", padx=16)
            if data and data.get(key):
                e.insert(0, data[key])
            fields[key] = e

        err = ctk.CTkLabel(body, text="", font=("Arial",12), text_color=RED)
        err.pack(pady=(8,4))

        def save():
            name  = fields["name"].get().strip()
            phone = fields["phone1"].get().strip()
            if not name or not phone:
                err.configure(text="❌  الاسم ورقم الهاتف الرئيسي مطلوبان")
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
                msg = f"✅  تم تعديل  '{name}'"
            else:
                db_exec("INSERT INTO contacts (name,rank,unit,phone1,phone2,notes) VALUES (?,?,?,?,?,?)", vals)
                msg = f"✅  تمت إضافة  '{name}'"
            self._close_panel()
            self._search()
            self.count_lbl.configure(text=msg)

        ctk.CTkButton(body, text="💾  حفظ", height=44,
                      fg_color=GOLD, hover_color=GOLD_HOVER,
                      text_color="#000", font=("Arial",14,"bold"),
                      command=save).pack(fill="x", padx=16, pady=(4,6))

        ctk.CTkButton(body, text="إلغاء", height=36,
                      fg_color="transparent", hover_color="#1C2128",
                      text_color=TEXT_SEC, font=("Arial",13),
                      command=self._close_panel).pack(fill="x", padx=16, pady=(0,16))

    # ── Delete ───────────────────────────────────────────
    def _delete(self, cid):
        rows = db_query("SELECT name FROM contacts WHERE id=?", (cid,))
        if rows and messagebox.askyesno("تأكيد الحذف",
                                        f"هل تريد حذف  '{rows[0]['name']}'  من الدليل؟"):
            db_exec("DELETE FROM contacts WHERE id=?", (cid,))
            self._close_panel()
            self._search()

    # ── Export ───────────────────────────────────────────
    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV","*.csv")],
                                            title="حفظ الدليل")
        if not path:
            return
        rows = db_query("SELECT name,rank,unit,phone1,phone2,notes FROM contacts ORDER BY name")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["الاسم","الرتبة","القسم","هاتف 1","هاتف 2","ملاحظات"])
            for r in rows:
                w.writerow(list(r))
        messagebox.showinfo("تم التصدير", f"تم حفظ الملف:\n{path}")

    # ── Users ────────────────────────────────────────────
    def _manage_users(self):
        body = self._make_panel("👤  إدارة المستخدمين", width=460, height=560)

        ctk.CTkLabel(body, text="المستخدمون الحاليون", font=("Arial",13,"bold"),
                     text_color=GOLD).pack(pady=(12,6), padx=16, anchor="e")

        list_frame = ctk.CTkFrame(body, fg_color=DARK_BG, corner_radius=8)
        list_frame.pack(fill="x", padx=16, pady=(0,10))

        def refresh_list():
            for w in list_frame.winfo_children():
                w.destroy()
            users = db_query("SELECT * FROM users ORDER BY is_admin DESC, username")
            if not users:
                ctk.CTkLabel(list_frame, text="لا يوجد مستخدمون",
                             font=("Arial",12), text_color=TEXT_SEC).pack(pady=10)
                return
            for u in users:
                row = ctk.CTkFrame(list_frame, fg_color=CARD_BG, corner_radius=6)
                row.pack(fill="x", padx=8, pady=3)
                badge = "👑 مدير" if u["is_admin"] else "👤 مستخدم"
                ctk.CTkLabel(row, text=f"{u['username']}  ({badge})",
                             font=("Arial",13), text_color=TEXT_PRI).pack(side="right", padx=10, pady=8)
                if u["username"] != "admin":
                    def make_del(uid):
                        return lambda: [db_exec("DELETE FROM users WHERE id=?", (uid,)), refresh_list()]
                    ctk.CTkButton(row, text="🗑 حذف", width=70, height=28,
                                  fg_color=RED, hover_color="#C44040",
                                  text_color="white", font=("Arial",11),
                                  command=make_del(u["id"])).pack(side="left", padx=8, pady=6)

        refresh_list()

        ctk.CTkLabel(body, text="إضافة مستخدم جديد", font=("Arial",13,"bold"),
                     text_color=GOLD).pack(pady=(16,6), padx=16, anchor="e")

        add_frame = ctk.CTkFrame(body, fg_color=DARK_BG, corner_radius=8)
        add_frame.pack(fill="x", padx=16, pady=(0,10))

        ctk.CTkLabel(add_frame, text="اسم المستخدم", font=("Arial",12),
                     text_color=TEXT_SEC, anchor="e").pack(fill="x", padx=12, pady=(12,3))
        nu = ctk.CTkEntry(add_frame, height=36, font=("Arial",13),
                          fg_color=CARD_BG, border_color=BORDER,
                          text_color=TEXT_PRI, justify="right")
        nu.pack(fill="x", padx=12)

        ctk.CTkLabel(add_frame, text="كلمة المرور", font=("Arial",12),
                     text_color=TEXT_SEC, anchor="e").pack(fill="x", padx=12, pady=(10,3))
        np_ = ctk.CTkEntry(add_frame, height=36, font=("Arial",13), show="●",
                           fg_color=CARD_BG, border_color=BORDER,
                           text_color=TEXT_PRI, justify="right")
        np_.pack(fill="x", padx=12)

        adm_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(add_frame, text="منح صلاحية المدير", variable=adm_var,
                        text_color=TEXT_PRI, font=("Arial",12)).pack(padx=12, pady=10, anchor="e")

        err_lbl = ctk.CTkLabel(add_frame, text="", font=("Arial",11), text_color=RED)
        err_lbl.pack()

        def add_user():
            u2 = nu.get().strip()
            p2 = np_.get().strip()
            if not u2 or not p2:
                err_lbl.configure(text="❌  أدخل اسم المستخدم وكلمة المرور", text_color=RED)
                return
            if len(p2) < 4:
                err_lbl.configure(text="❌  كلمة المرور 4 أحرف على الأقل", text_color=RED)
                return
            pw2 = hashlib.sha256(p2.encode()).hexdigest()
            try:
                db_exec("INSERT INTO users (username,password,is_admin) VALUES (?,?,?)",
                        (u2, pw2, int(adm_var.get())))
                nu.delete(0, "end")
                np_.delete(0, "end")
                adm_var.set(False)
                err_lbl.configure(text=f"✅  تمت إضافة '{u2}'", text_color=GREEN)
                refresh_list()
            except Exception:
                err_lbl.configure(text="❌  اسم المستخدم موجود مسبقاً", text_color=RED)

        ctk.CTkButton(add_frame, text="➕  إضافة المستخدم", height=38,
                      fg_color=GREEN, hover_color="#2EA043",
                      text_color="white", font=("Arial",13,"bold"),
                      command=add_user).pack(fill="x", padx=12, pady=(4,14))

    # ── Logout ───────────────────────────────────────────
    def _logout(self):
        if messagebox.askyesno("تسجيل خروج", "هل تريد تسجيل الخروج؟"):
            self.destroy()
            main()

# ─── Entry ────────────────────────────────────────────────
def main():
    init_db()
    login = LoginWindow()
    login.mainloop()
    if login.logged_user:
        app = PhoneBookApp(login.logged_user)
        app.mainloop()

if __name__ == "__main__":
    main()
