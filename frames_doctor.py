
"""
frames_doctor.py
----------------
Contains the DoctorFrame class, which manages the `doctor` table.

This frame is used in the Admin portal to:
- Add / Update / Delete doctors
- View all doctors (with department name) in a Treeview
"""

from tkinter import *
from tkinter import ttk, messagebox
from db_config import get_connection


class DoctorFrame:
    """
    GUI logic for managing the `doctor` table.
    Includes foreign key to `department`.
    """

    def __init__(self, parent):
        # Variables
        self.doctor_id_var = StringVar()
        self.first_name_var = StringVar()
        self.last_name_var = StringVar()
        self.department_var = StringVar()  # store "id - name" string
        self.phone_var = StringVar()
        self.email_var = StringVar()
        self.avg_rating_var = StringVar()

        # Department choices cache: list of (id, name)
        self.dep_choices = []

        # Form layout
        form_frame = Frame(parent, bg="white")
        form_frame.pack(side=TOP, fill=X)

        # Doctor ID
        Label(form_frame, text="Doctor ID", bg="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.doctor_id_var, width=10, state="readonly").grid(row=0, column=1, padx=5, pady=5)

        # First name
        Label(form_frame, text="First Name", bg="white").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.first_name_var, width=15).grid(row=0, column=3, padx=5, pady=5)

        # Last name
        Label(form_frame, text="Last Name", bg="white").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.last_name_var, width=15).grid(row=0, column=5, padx=5, pady=5)

        # Department (Combo)
        Label(form_frame, text="Department", bg="white").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.dep_combo = ttk.Combobox(form_frame, textvariable=self.department_var, width=20, state="readonly")
        self.dep_combo.grid(row=1, column=1, padx=5, pady=5)

        # Phone
        Label(form_frame, text="Phone", bg="white").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.phone_var, width=15).grid(row=1, column=3, padx=5, pady=5)

        # Email
        Label(form_frame, text="Email", bg="white").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.email_var, width=20).grid(row=1, column=5, padx=5, pady=5)

        # Avg rating (read-only, normally computed from appointments)
        Label(form_frame, text="Avg Rating", bg="white").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.avg_rating_var, width=8, state="readonly").grid(row=0, column=7, padx=5, pady=5)

        # Buttons
        btn_frame = Frame(form_frame, bg="white")
        btn_frame.grid(row=0, column=8, rowspan=2, padx=10, pady=5, sticky="ns")

        Button(btn_frame, text="Add", width=10, command=self.add_doctor).pack(pady=2)
        Button(btn_frame, text="Update", width=10, command=self.update_doctor).pack(pady=2)
        Button(btn_frame, text="Delete", width=10, command=self.delete_doctor).pack(pady=2)
        Button(btn_frame, text="Clear", width=10, command=self.clear_form).pack(pady=2)
        Button(btn_frame, text="Refresh", width=10, command=self.fetch_doctors).pack(pady=2)

        # Table
        table_frame = Frame(parent, bg="lightgrey")
        table_frame.pack(fill=BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "first", "last", "department", "phone", "email", "avg"),
            show="headings"
        )

        headings = [
            ("id", "ID", 60),
            ("first", "First Name", 100),
            ("last", "Last Name", 100),
            ("department", "Department", 140),
            ("phone", "Phone", 100),
            ("email", "Email", 160),
            ("avg", "Avg Rating", 80),
        ]
        for col, text, width in headings:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width)

        vsb = Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        self.tree.bind("<ButtonRelease-1>", self.on_row_select)

        # Initial data
        self.refresh_department_choices()
        self.fetch_doctors()

    # ---------- Helper: load departments ----------
    def refresh_department_choices(self):
        """Load all departments and prepare choices for combo box."""
        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("SELECT department_id, name FROM department ORDER BY name")
            self.dep_choices = cur.fetchall()
            display_values = [f"{row[0]} - {row[1]}" for row in self.dep_choices]
            self.dep_combo["values"] = display_values
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load departments.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def _parse_department_id(self):
        """Extract department_id from combo string 'id - name'."""
        val = self.department_var.get().strip()
        if not val:
            return None
        try:
            dep_id_str = val.split("-", 1)[0].strip()
            return int(dep_id_str)
        except Exception:
            return None

    # ---------- CRUD operations ----------
    def fetch_doctors(self):
        """Fetch all doctors (with department name) and show them in the table."""
        self.refresh_department_choices()

        try:
            con = get_connection()
            cur = con.cursor()
            sql = """
                SELECT d.doctor_id,
                       d.first_name,
                       d.last_name,
                       CONCAT(d.department_id, ' - ', dept.name) AS dep_display,
                       d.phone,
                       d.email,
                       d.avg_rating
                FROM doctor d
                JOIN department dept ON d.department_id = dept.department_id
            """
            cur.execute(sql)
            rows = cur.fetchall()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                self.tree.insert("", END, values=row)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch doctors.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def add_doctor(self):
        """Insert a new doctor row."""
        first = self.first_name_var.get().strip()
        last = self.last_name_var.get().strip()
        dep_id = self._parse_department_id()
        phone = self.phone_var.get().strip() or None
        email = self.email_var.get().strip() or None

        if not first or not last or not dep_id:
            messagebox.showwarning("Warning", "First name, last name, and department are required.")
            return

        try:
            con = get_connection()
            cur = con.cursor()
            sql = "INSERT INTO doctor (first_name, last_name, department_id, phone, email) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(sql, (first, last, dep_id, phone, email))
            con.commit()
            messagebox.showinfo("Success", "Doctor added successfully.")
            self.fetch_doctors()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add doctor.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def on_row_select(self, event):
        """Load selected doctor into the form."""
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        if not values:
            return

        self.doctor_id_var.set(values[0])
        self.first_name_var.set(values[1])
        self.last_name_var.set(values[2])
        self.department_var.set(values[3])
        self.phone_var.set(values[4] if values[4] else "")
        self.email_var.set(values[5] if values[5] else "")
        self.avg_rating_var.set(values[6] if values[6] is not None else "")

    def clear_form(self):
        """Clear the doctor form fields."""
        self.doctor_id_var.set("")
        self.first_name_var.set("")
        self.last_name_var.set("")
        self.department_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.avg_rating_var.set("")

    def update_doctor(self):
        """Update selected doctor row by ID."""
        did = self.doctor_id_var.get().strip()
        if not did:
            messagebox.showwarning("Warning", "Select a doctor to update.")
            return

        first = self.first_name_var.get().strip()
        last = self.last_name_var.get().strip()
        dep_id = self._parse_department_id()
        phone = self.phone_var.get().strip() or None
        email = self.email_var.get().strip() or None

        if not first or not last or not dep_id:
            messagebox.showwarning("Warning", "First name, last name, and department are required.")
            return

        try:
            con = get_connection()
            cur = con.cursor()
            sql = """
                UPDATE doctor
                SET first_name = %s,
                    last_name = %s,
                    department_id = %s,
                    phone = %s,
                    email = %s
                WHERE doctor_id = %s
            """
            cur.execute(sql, (first, last, dep_id, phone, email, did))
            con.commit()

            if cur.rowcount:
                messagebox.showinfo("Success", "Doctor updated successfully.")
            else:
                messagebox.showinfo("Info", "No doctor found with this ID.")

            self.fetch_doctors()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update doctor.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def delete_doctor(self):
        """Delete selected doctor (may fail if referenced by appointments)."""
        did = self.doctor_id_var.get().strip()
        if not did:
            messagebox.showwarning("Warning", "Select a doctor to delete.")
            return

        if not messagebox.askyesno("Confirm", "Delete this doctor? (may fail if there are appointments)"):
            return

        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("DELETE FROM doctor WHERE doctor_id = %s", (did,))
            con.commit()

            if cur.rowcount:
                messagebox.showinfo("Success", "Doctor deleted successfully.")
            else:
                messagebox.showinfo("Info", "No doctor found with this ID.")

            self.fetch_doctors()
            self.clear_form()
        except Exception as e:
            messagebox.showerror(
                "Error",
                "Failed to delete doctor.\n"
                "It might be referenced by some appointments (foreign key constraint).\n\n" + str(e)
            )
        finally:
            try:
                con.close()
            except Exception:
                pass
