
"""
frames_patient.py
-----------------
Contains the PatientFrame class, which manages the `patient` table.

This frame is used in the Admin portal to:
- Add / Update / Delete patients
- View all patients in a Treeview
"""

from tkinter import *
from tkinter import ttk, messagebox
from db_config import get_connection


class PatientFrame:
    """
    GUI logic for managing the `patient` table.
    Includes simple CRUD and listing.
    """

    def __init__(self, parent):
        # Variables
        self.patient_id_var = StringVar()
        self.first_name_var = StringVar()
        self.last_name_var = StringVar()
        self.gender_var = StringVar()
        self.phone_var = StringVar()
        self.email_var = StringVar()

        # Form layout
        form_frame = Frame(parent, bg="white")
        form_frame.pack(side=TOP, fill=X)

        # Patient ID (read-only)
        Label(form_frame, text="Patient ID", bg="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.patient_id_var, width=10, state="readonly").grid(row=0, column=1, padx=5, pady=5)

        # First name
        Label(form_frame, text="First Name", bg="white").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.first_name_var, width=15).grid(row=0, column=3, padx=5, pady=5)

        # Last name
        Label(form_frame, text="Last Name", bg="white").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.last_name_var, width=15).grid(row=0, column=5, padx=5, pady=5)

        # Gender (Combobox)
        Label(form_frame, text="Gender", bg="white").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        gender_combo = ttk.Combobox(form_frame, textvariable=self.gender_var, state="readonly", width=12)
        gender_combo["values"] = ("Male", "Female", "")
        gender_combo.grid(row=1, column=1, padx=5, pady=5)
        gender_combo.current(2)  # default empty

        # Phone
        Label(form_frame, text="Phone", bg="white").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.phone_var, width=15).grid(row=1, column=3, padx=5, pady=5)

        # Email
        Label(form_frame, text="Email", bg="white").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.email_var, width=20).grid(row=1, column=5, padx=5, pady=5)

        # Buttons
        btn_frame = Frame(form_frame, bg="white")
        btn_frame.grid(row=0, column=6, rowspan=2, padx=10, pady=5, sticky="ns")

        Button(btn_frame, text="Add", width=10, command=self.add_patient).pack(pady=2)
        Button(btn_frame, text="Update", width=10, command=self.update_patient).pack(pady=2)
        Button(btn_frame, text="Delete", width=10, command=self.delete_patient).pack(pady=2)
        Button(btn_frame, text="Clear", width=10, command=self.clear_form).pack(pady=2)
        Button(btn_frame, text="Refresh", width=10, command=self.fetch_patients).pack(pady=2)

        # Table
        table_frame = Frame(parent, bg="lightgrey")
        table_frame.pack(fill=BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "first", "last", "gender", "phone", "email"),
            show="headings"
        )
        for col, text, width in [
            ("id", "ID", 60),
            ("first", "First Name", 100),
            ("last", "Last Name", 100),
            ("gender", "Gender", 80),
            ("phone", "Phone", 100),
            ("email", "Email", 160),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width)

        vsb = Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        self.tree.bind("<ButtonRelease-1>", self.on_row_select)

        # Initial load
        self.fetch_patients()

    # ---------- CRUD operations ----------
    def fetch_patients(self):
        """Fetch all patients and show them in the table."""
        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("SELECT patient_id, first_name, last_name, gender, phone, email FROM patient")
            rows = cur.fetchall()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                self.tree.insert("", END, values=row)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch patients.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def add_patient(self):
        """Insert a new patient row."""
        first = self.first_name_var.get().strip()
        last = self.last_name_var.get().strip()
        gender = self.gender_var.get().strip() or None
        phone = self.phone_var.get().strip() or None
        email = self.email_var.get().strip() or None

        if not first or not last:
            messagebox.showwarning("Warning", "First and last name are required.")
            return

        try:
            con = get_connection()
            cur = con.cursor()
            sql = """
                INSERT INTO patient (first_name, last_name, gender, phone, email)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(sql, (first, last, gender, phone, email))
            con.commit()
            messagebox.showinfo("Success", "Patient added successfully.")
            self.fetch_patients()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add patient.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def on_row_select(self, event):
        """Load selected patient into the form."""
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        if not values:
            return

        self.patient_id_var.set(values[0])
        self.first_name_var.set(values[1])
        self.last_name_var.set(values[2])
        self.gender_var.set(values[3] if values[3] else "")
        self.phone_var.set(values[4] if values[4] else "")
        self.email_var.set(values[5] if values[5] else "")

    def clear_form(self):
        """Clear the input fields."""
        self.patient_id_var.set("")
        self.first_name_var.set("")
        self.last_name_var.set("")
        self.gender_var.set("")
        self.phone_var.set("")
        self.email_var.set("")

    def update_patient(self):
        """Update selected patient row by ID."""
        pid = self.patient_id_var.get().strip()
        if not pid:
            messagebox.showwarning("Warning", "Select a patient to update.")
            return

        first = self.first_name_var.get().strip()
        last = self.last_name_var.get().strip()
        gender = self.gender_var.get().strip() or None
        phone = self.phone_var.get().strip() or None
        email = self.email_var.get().strip() or None

        if not first or not last:
            messagebox.showwarning("Warning", "First and last name are required.")
            return

        try:
            con = get_connection()
            cur = con.cursor()
            sql = """
                UPDATE patient
                SET first_name = %s, last_name = %s, gender = %s, phone = %s, email = %s
                WHERE patient_id = %s
            """
            cur.execute(sql, (first, last, gender, phone, email, pid))
            con.commit()

            if cur.rowcount:
                messagebox.showinfo("Success", "Patient updated successfully.")
            else:
                messagebox.showinfo("Info", "No patient found with this ID.")

            self.fetch_patients()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update patient.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def delete_patient(self):
        """Delete selected patient row by ID (may fail if referenced by appointments)."""
        pid = self.patient_id_var.get().strip()
        if not pid:
            messagebox.showwarning("Warning", "Select a patient to delete.")
            return

        if not messagebox.askyesno("Confirm", "Delete this patient? (may fail if there are appointments)"):
            return

        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("DELETE FROM patient WHERE patient_id = %s", (pid,))
            con.commit()

            if cur.rowcount:
                messagebox.showinfo("Success", "Patient deleted successfully.")
            else:
                messagebox.showinfo("Info", "No patient found with this ID.")

            self.fetch_patients()
            self.clear_form()
        except Exception as e:
            messagebox.showerror(
                "Error",
                "Failed to delete patient.\n"
                "It might be referenced by some appointments (foreign key constraint).\n\n" + str(e)
            )
        finally:
            try:
                con.close()
            except Exception:
                pass
