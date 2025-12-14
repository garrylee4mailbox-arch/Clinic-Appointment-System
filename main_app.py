"""
main_app.py (v4 - Clean Register + No Bind Patient)
---------------------------------------------------
Login:
    - username + password
    - admin → AdminPortal
    - client → ClientPortal (bound patient_id)

Register:
    - User fills patient info + username + password
    - System automatically:
        1. Create patient
        2. Get patient_id
        3. Create user_account with role='client'

NO MORE: Bind Patient dropdown
"""

from tkinter import *
from tkinter import ttk, messagebox
from db_config import get_connection
from admin_portal import AdminPortal
from client_portal import ClientPortal


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Clinic Management System - Login / Register")
        self.root.geometry("450x450+300+100")
        self.root.configure(bg="white")

        self.username_var = StringVar()
        self.password_var = StringVar()

        # Variables for registration
        self.reg_first_var = StringVar()
        self.reg_last_var = StringVar()
        self.reg_gender_var = StringVar()
        self.reg_phone_var = StringVar()
        self.reg_email_var = StringVar()
        self.reg_user_var = StringVar()
        self.reg_pass_var = StringVar()

        # UI
        self.build_login_ui()

    # ---------------- LOGIN UI ----------------
    def build_login_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        Label(self.root, text="Clinic Management System",
              bg="#1AAECB", fg="white",
              font=("Arial", 16, "bold")).pack(fill=X)

        frame = Frame(self.root, bg="white")
        frame.pack(pady=40)

        Label(frame, text="Username", bg="white").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        Entry(frame, textvariable=self.username_var, width=25).grid(row=0, column=1)

        Label(frame, text="Password", bg="white").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        Entry(frame, textvariable=self.password_var, width=25, show="*").grid(row=1, column=1)

        # Buttons in one row
        btn_row = Frame(self.root, bg="white")
        btn_row.pack(pady=20)

        Button(btn_row, text="Login", width=12,
               command=self.handle_login).grid(row=0, column=0, padx=10)

        Button(btn_row, text="Register", width=12,
               command=self.build_register_ui).grid(row=0, column=1, padx=10)

        Button(btn_row, text="Quit", width=12,
               command=self.root.destroy).grid(row=0, column=2, padx=10)


    # ---------------- REGISTER UI ----------------
    def build_register_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        Label(self.root, text="Register New Client",
              bg="#1AAECB", fg="white",
              font=("Arial", 16, "bold")).pack(fill=X)

        frame = Frame(self.root, bg="white")
        frame.pack(pady=15)

        fields = [
            ("First Name", self.reg_first_var),
            ("Last Name", self.reg_last_var),
            ("Gender (Male/Female)", self.reg_gender_var),
            ("Phone", self.reg_phone_var),
            ("Email", self.reg_email_var),
            ("Username", self.reg_user_var),
            ("Password", self.reg_pass_var),
        ]

        for i, (label, var) in enumerate(fields):
            Label(frame, text=label, bg="white").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            Entry(frame, textvariable=var, width=25).grid(row=i, column=1, padx=5)

        Button(frame, text="Submit", width=12, command=self.handle_register).grid(row=10, column=0, pady=15)
        Button(frame, text="Back", width=12, command=self.build_login_ui).grid(row=10, column=1, pady=15)

    # ---------------- LOGIN LOGIC ----------------
    def handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showwarning("Warning", "Enter username and password.")
            return

        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("""
                SELECT user_id, username, password, role, patient_id
                FROM user_account WHERE username=%s
            """, (username,))
            row = cur.fetchone()
        except Exception as e:
            messagebox.showerror("Error", f"Database query failed:\n{e}")
            return

        if not row or row[2] != password:
            messagebox.showerror("Error", "Invalid username or password.")
            return

        role = row[3]
        user_info = {
            "user_id": row[0],
            "username": row[1],
            "role": role,
            "patient_id": row[4],
        }

        if role == "admin":
            win = Toplevel(self.root)
            AdminPortal(win)
        else:
            win = Toplevel(self.root)
            ClientPortal(win, user_info)

    # ---------------- REGISTER LOGIC ----------------
    def handle_register(self):
        data = {
            "first": self.reg_first_var.get().strip(),
            "last": self.reg_last_var.get().strip(),
            "gender": self.reg_gender_var.get().strip(),
            "phone": self.reg_phone_var.get().strip(),
            "email": self.reg_email_var.get().strip(),
            "username": self.reg_user_var.get().strip(),
            "password": self.reg_pass_var.get().strip(),
        }

        if not all(data.values()):
            messagebox.showwarning("Warning", "All fields are required.")
            return

        try:
            con = get_connection()
            cur = con.cursor()

            # 1. Insert patient
            cur.execute("""
                INSERT INTO patient(first_name, last_name, gender, phone, email)
                VALUES (%s, %s, %s, %s, %s)
            """, (data["first"], data["last"], data["gender"], data["phone"], data["email"]))
            patient_id = cur.lastrowid

            # 2. Insert into user_account
            cur.execute("""
                INSERT INTO user_account(username, password, role, patient_id)
                VALUES (%s, %s, 'client', %s)
            """, (data["username"], data["password"], patient_id))

            con.commit()
            messagebox.showinfo("Success", "Registration successful!")
            self.build_login_ui()

        except Exception as e:
            messagebox.showerror("Error", f"Registration failed:\n{e}")


if __name__ == "__main__":
    root = Tk()
    MainApp(root)
    root.mainloop()
