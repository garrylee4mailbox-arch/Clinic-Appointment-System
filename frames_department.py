
"""
frames_department.py
--------------------
Contains the DepartmentFrame class, which manages the `department` table.

This frame is used in the Admin portal to:
- Add / Update / Delete departments
- View all departments in a Treeview
"""

from tkinter import *
from tkinter import ttk, messagebox
from db_config import get_connection


class DepartmentFrame:
    """
    GUI logic for managing the `department` table.
    Includes: add, update, delete, list, and clear form fields.
    """

    def __init__(self, parent):
        # Tkinter variables for form fields
        self.dep_id_var = StringVar()
        self.name_var = StringVar()
        self.min_var = StringVar()
        self.max_var = StringVar()

        # Layout: top form + bottom table
        form_frame = Frame(parent, bg="white")
        form_frame.pack(side=TOP, fill=X)

        # Department ID (read-only, auto-increment)
        Label(form_frame, text="Department ID", bg="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.dep_id_var, width=10, state="readonly").grid(row=0, column=1, padx=5, pady=5)

        # Name
        Label(form_frame, text="Name", bg="white").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.name_var, width=20).grid(row=0, column=3, padx=5, pady=5)

        # Min doctors
        Label(form_frame, text="Min Doctors", bg="white").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.min_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        # Max doctors
        Label(form_frame, text="Max Doctors", bg="white").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        Entry(form_frame, textvariable=self.max_var, width=10).grid(row=1, column=3, padx=5, pady=5)

        # Buttons for actions
        btn_frame = Frame(form_frame, bg="white")
        btn_frame.grid(row=0, column=4, rowspan=2, padx=10, pady=5, sticky="ns")

        Button(btn_frame, text="Add", width=10, command=self.add_department).pack(pady=2)
        Button(btn_frame, text="Update", width=10, command=self.update_department).pack(pady=2)
        Button(btn_frame, text="Delete", width=10, command=self.delete_department).pack(pady=2)
        Button(btn_frame, text="Clear", width=10, command=self.clear_form).pack(pady=2)
        Button(btn_frame, text="Refresh", width=10, command=self.fetch_departments).pack(pady=2)

        # Table for department list
        table_frame = Frame(parent, bg="lightgrey")
        table_frame.pack(fill=BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "name", "min", "max"),
            show="headings"
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("min", text="Min Doctors")
        self.tree.heading("max", text="Max Doctors")

        self.tree.column("id", width=60)
        self.tree.column("name", width=200)
        self.tree.column("min", width=100)
        self.tree.column("max", width=100)

        vsb = Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        # Bind click to load row into form
        self.tree.bind("<ButtonRelease-1>", self.on_row_select)

        # Initial load
        self.fetch_departments()

    # ---------- CRUD operations ----------
    def fetch_departments(self):
        """Fetch all departments from DB and display in the Treeview."""
        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("SELECT department_id, name, min_doctors, max_doctors FROM department")
            rows = cur.fetchall()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                self.tree.insert("", END, values=row)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch departments.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def add_department(self):
        """Insert a new department row into the DB."""
        name = self.name_var.get().strip()
        min_doctors = self.min_var.get().strip()
        max_doctors = self.max_var.get().strip()

        if not name:
            messagebox.showwarning("Warning", "Name cannot be empty.")
            return

        try:
            min_val = int(min_doctors) if min_doctors else 2
            max_val = int(max_doctors) if max_doctors else 5
        except ValueError:
            messagebox.showwarning("Warning", "Min/Max doctors must be integers.")
            return

        try:
            con = get_connection()
            cur = con.cursor()
            sql = "INSERT INTO department (name, min_doctors, max_doctors) VALUES (%s, %s, %s)"
            cur.execute(sql, (name, min_val, max_val))
            con.commit()
            messagebox.showinfo("Success", "Department added successfully.")
            self.fetch_departments()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add department.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def on_row_select(self, event):
        """Load selected row into the form fields."""
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        if not values:
            return

        self.dep_id_var.set(values[0])
        self.name_var.set(values[1])
        self.min_var.set(str(values[2]))
        self.max_var.set(str(values[3]))

    def clear_form(self):
        """Clear the form input fields."""
        self.dep_id_var.set("")
        self.name_var.set("")
        self.min_var.set("")
        self.max_var.set("")

    def update_department(self):
        """Update the selected department row by ID."""
        dep_id = self.dep_id_var.get().strip()
        if not dep_id:
            messagebox.showwarning("Warning", "Select a department to update.")
            return

        name = self.name_var.get().strip()
        min_doctors = self.min_var.get().strip()
        max_doctors = self.max_var.get().strip()

        if not name:
            messagebox.showwarning("Warning", "Name cannot be empty.")
            return

        try:
            min_val = int(min_doctors) if min_doctors else 2
            max_val = int(max_doctors) if max_doctors else 5
        except ValueError:
            messagebox.showwarning("Warning", "Min/Max doctors must be integers.")
            return

        try:
            con = get_connection()
            cur = con.cursor()
            sql = """
                UPDATE department
                SET name = %s, min_doctors = %s, max_doctors = %s
                WHERE department_id = %s
            """
            cur.execute(sql, (name, min_val, max_val, dep_id))
            con.commit()

            if cur.rowcount:
                messagebox.showinfo("Success", "Department updated successfully.")
            else:
                messagebox.showinfo("Info", "No department found with this ID.")

            self.fetch_departments()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update department.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def delete_department(self):
        """Delete the selected department row by ID."""
        dep_id = self.dep_id_var.get().strip()
        if not dep_id:
            messagebox.showwarning("Warning", "Select a department to delete.")
            return

        if not messagebox.askyesno("Confirm", "Delete this department? (may fail if used by a doctor)"):
            return

        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("DELETE FROM department WHERE department_id = %s", (dep_id,))
            con.commit()

            if cur.rowcount:
                messagebox.showinfo("Success", "Department deleted successfully.")
            else:
                messagebox.showinfo("Info", "No department found with this ID.")
            self.fetch_departments()
            self.clear_form()
        except Exception as e:
            messagebox.showerror(
                "Error",
                "Failed to delete department.\n"
                "It might be referenced by some doctors (foreign key constraint).\n\n" + str(e)
            )
        finally:
            try:
                con.close()
            except Exception:
                pass
