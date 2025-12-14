"""
frames_appointment_admin.py
---------------------------
Admin appointment management
- Department -> Doctor cascading filter (card grid)
- Full CRUD with slot grid + min rating filter
"""

from tkinter import *
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
from db_config import get_connection


class AppointmentAdminFrame:
    """Admin-facing appointment CRUD with doctor card grid + slot grid."""

    def __init__(self, parent):
        # Form variables
        self.appointment_id_var = StringVar()
        self.department_var = StringVar()
        self.patient_var = StringVar()
        self.date_var = StringVar()
        self.time_var = StringVar()
        self.status_var = StringVar(value="Scheduled")
        self.doctor_rating_var = StringVar()
        self.notes_var = StringVar()

        # Doctor grid state
        self.min_rating_var = StringVar(value="All")
        self.selected_doctor_id = None
        self.selected_doctor_display = ""
        self.selected_doctor_card = None
        self.selected_slot_btn = None
        self.current_row_doctor_id = None
        self.doctor_grid_frame = None

        # Cached lists
        self.departments = []
        self.doctors = []
        self.patients = []

        # ------------------- Layout: header + form -------------------
        header = Frame(parent, bg="white")
        header.pack(fill=X, padx=10, pady=(8, 4))
        Label(
            header,
            text="Admin Appointment Management",
            font=("Arial", 12, "bold"),
            bg="white",
        ).pack(anchor="w")

        form = Frame(parent, bg="white")
        form.pack(fill=X, padx=10, pady=5)

        # Row 0
        Label(form, text="Appointment ID", bg="white").grid(row=0, column=0, sticky="w")
        Entry(form, textvariable=self.appointment_id_var, width=12, state="readonly").grid(row=0, column=1, padx=4, pady=2, sticky="w")

        Label(form, text="Patient", bg="white").grid(row=0, column=2, sticky="w")
        self.patient_combo = ttk.Combobox(form, textvariable=self.patient_var, state="readonly", width=28)
        self.patient_combo.grid(row=0, column=3, padx=4, pady=2, sticky="w")

        Label(form, text="Department", bg="white").grid(row=0, column=4, sticky="w")
        self.dept_combo = ttk.Combobox(form, textvariable=self.department_var, state="readonly", width=25)
        self.dept_combo.grid(row=0, column=5, padx=4, pady=2, sticky="w")
        self.dept_combo.bind("<<ComboboxSelected>>", self.on_department_change)

        # Row 1
        Label(form, text="Date", bg="white").grid(row=1, column=0, sticky="w")
        self.date_combo = ttk.Combobox(form, textvariable=self.date_var, state="readonly", width=18)
        self.date_combo.grid(row=1, column=1, padx=4, pady=2, sticky="w")
        self.date_combo.bind("<<ComboboxSelected>>", self.on_date_change)

        Label(form, text="Time", bg="white").grid(row=1, column=2, sticky="w")
        self.time_entry = Entry(form, textvariable=self.time_var, state="readonly", width=18)
        self.time_entry.grid(row=1, column=3, padx=4, pady=2, sticky="w")

        Label(form, text="Status", bg="white").grid(row=1, column=4, sticky="w")
        self.status_combo = ttk.Combobox(form, textvariable=self.status_var, state="readonly", width=18,
                                         values=["Scheduled", "Completed", "Cancelled"])
        self.status_combo.grid(row=1, column=5, padx=4, pady=2, sticky="w")

        # Row 2
        Label(form, text="Doctor Rating", bg="white").grid(row=2, column=0, sticky="w")
        rating_values = [""] + [f"{x/2:.1f}" for x in range(10, 1, -1)]  # "", 5.0, 4.5, ..., 1.0
        self.doctor_rating_combo = ttk.Combobox(form, textvariable=self.doctor_rating_var,
                                                state="readonly", width=10, values=rating_values)
        self.doctor_rating_combo.grid(row=2, column=1, padx=4, pady=2, sticky="w")

        Label(form, text="Notes", bg="white").grid(row=2, column=2, sticky="w")
        Entry(form, textvariable=self.notes_var, width=55).grid(row=2, column=3, columnspan=3, padx=4, pady=2, sticky="w")

        # Buttons
        btn_frame = Frame(form, bg="white")
        btn_frame.grid(row=0, column=6, rowspan=3, padx=(12, 0), sticky="ns")
        Button(btn_frame, text="Add", width=12, command=self.add_appointment).pack(pady=2)
        Button(btn_frame, text="Update", width=12, command=self.update_appointment).pack(pady=2)
        Button(btn_frame, text="Delete", width=12, command=self.delete_selected).pack(pady=2)
        Button(btn_frame, text="Clear", width=12, command=self.clear_form).pack(pady=2)

        # ----------- doctor grid + rating filter -----------
        self.doctor_container = Frame(parent, bg="white")
        self.doctor_container.pack(fill=X, padx=10, pady=(5, 0), anchor="w")

        # ----------- slot container under doctor grid -----------
        self.slot_container = Frame(parent, bg="white")
        self.slot_container.pack(fill=X, padx=10, pady=(5, 0), anchor="w")

        # ----------- appointment table -----------
        table = Frame(parent, bg="white")
        table.pack(fill=BOTH, expand=True, padx=10, pady=8)

        self.tree = ttk.Treeview(
            table,
            columns=("appt_id", "patient", "department", "doctor", "date", "time", "status", "rating", "notes"),
            show="headings",
        )
        for col, text, width in [
            ("appt_id", "ID", 70),
            ("patient", "Patient", 170),
            ("department", "Department", 150),
            ("doctor", "Doctor", 190),
            ("date", "Date", 100),
            ("time", "Time", 80),
            ("status", "Status", 100),
            ("rating", "Rating", 70),
            ("notes", "Notes", 200),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")

        vsb = Scrollbar(table, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_row)

        # Initial loads
        self.init_dates()
        self.load_departments()
        self.load_patients()
        self.render_doctors()
        self.render_slots()
        self.refresh_table()

    # ---------------- helpers ----------------

    def init_dates(self):
        today = date.today()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(4)]
        self.date_combo["values"] = dates
        self.date_var.set(dates[0])

    def load_departments(self):
        con = get_connection()
        cur = con.cursor()
        cur.execute("SELECT department_id, name FROM department")
        self.departments = cur.fetchall()
        con.close()
        self.dept_combo["values"] = [f"{d[0]} - {d[1]}" for d in self.departments]

    def load_patients(self):
        con = get_connection()
        cur = con.cursor()
        cur.execute("SELECT patient_id, first_name, last_name FROM patient")
        self.patients = cur.fetchall()
        con.close()
        self.patient_combo["values"] = [f"{p[0]} - {p[1]} {p[2]}" for p in self.patients]

    def load_doctors_for_department(self, dept_id):
        """Load doctors for a department including specialty, bio, and rating."""
        con = get_connection()
        cur = con.cursor()
        cur.execute("""
            SELECT doctor_id, first_name, last_name, specialty, bio, avg_rating
            FROM doctor
            WHERE department_id=%s
        """, (dept_id,))
        self.doctors = cur.fetchall()
        con.close()

    def on_department_change(self, _):
        """Handle department selection: load doctors, reset selections, refresh UI."""
        try:
            dept_id = int(self.department_var.get().split("-")[0].strip())
        except Exception:
            return
        self.load_doctors_for_department(dept_id)
        self.min_rating_var.set("All")
        self.clear_doctor_selection()
        self.render_doctors()
        self.render_slots()

    def on_min_rating_change(self, _):
        """Update doctor grid based on rating filter and clear selections if needed."""
        filtered_ids = {doc[0] for doc in self.get_filtered_doctors()}
        if self.selected_doctor_id and self.selected_doctor_id not in filtered_ids:
            self.clear_doctor_selection()
        self.render_doctors()
        self.render_slots()

    def on_date_change(self, _):
        self.clear_time_selection()
        self.render_slots()

    def clear_doctor_selection(self):
        """Reset doctor selection and slot highlight."""
        self.selected_doctor_id = None
        self.selected_doctor_display = ""
        if self.selected_doctor_card:
            self.reset_card_style(self.selected_doctor_card)
        self.selected_doctor_card = None
        self.clear_time_selection()

    def clear_time_selection(self):
        """Reset chosen time and selected slot highlight."""
        self.time_var.set("")
        if self.selected_slot_btn:
            self.selected_slot_btn.config(relief=RAISED, bd=2)
            self.selected_slot_btn = None

    def render_doctors(self):
        """Render doctor cards with rating filter and selection highlight."""
        for child in self.doctor_container.winfo_children():
            child.destroy()
        self.selected_doctor_card = None
        self.doctor_grid_frame = None

        # Rating filter bar
        filter_frame = Frame(self.doctor_container, bg="white")
        filter_frame.pack(anchor="w", pady=(0, 5), fill=X)
        Label(filter_frame, text="Min Rating", bg="white").pack(side=LEFT)
        rating_combo = ttk.Combobox(filter_frame, textvariable=self.min_rating_var,
                                    state="readonly", width=8,
                                    values=["All", "5.0", "4.5", "4.0", "3.5", "3.0", "2.5", "2.0", "1.5", "1.0"])
        rating_combo.pack(side=LEFT, padx=5)
        rating_combo.bind("<<ComboboxSelected>>", self.on_min_rating_change)

        if not self.department_var.get():
            Label(self.doctor_container, text="Select department to view doctors",
                  bg="white", fg="gray").pack(anchor="w")
            return

        filtered = self.get_filtered_doctors()
        if not filtered:
            Label(self.doctor_container, text="No doctors match the selected filters",
                  bg="white", fg="gray").pack(anchor="w")
            return

        grid = Frame(self.doctor_container, bg="white")
        grid.pack(anchor="w", fill=X)
        self.doctor_grid_frame = grid

        for idx, doc in enumerate(filtered):
            doctor_id, first, last, specialty, bio, avg_rating = doc
            display = f"{doctor_id} - {first} {last}"
            rating_text = "N/A" if avg_rating is None else f"{avg_rating:.1f}"

            card = Frame(grid, bd=2, relief=RIDGE, bg="white", padx=8, pady=6, width=220)
            Label(card, text=display, font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
            Label(card, text=f"Specialty: {specialty}", bg="white", fg="black").pack(anchor="w")
            Label(card, text=f"Bio: {bio}", bg="white", wraplength=200, justify=LEFT).pack(anchor="w")
            Label(card, text=f"Avg Rating: {rating_text}", bg="white", fg="blue").pack(anchor="w")

            card.bind("<Button-1>", lambda e, d_id=doctor_id, disp=display, c=card: self.select_doctor(d_id, disp, c))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, d_id=doctor_id, disp=display, c=card: self.select_doctor(d_id, disp, c))

            row, col = divmod(idx, 3)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Re-apply highlight if this doctor is currently selected
            if self.selected_doctor_id == doctor_id:
                self.highlight_selected_card(card)

        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)

    def get_filtered_doctors(self):
        """Return doctors filtered by the current minimum rating."""
        value = self.min_rating_var.get()
        min_rating = 0 if value == "All" else float(value)
        filtered = []
        for doc in self.doctors:
            avg_rating = doc[5] or 0
            if avg_rating >= min_rating:
                filtered.append(doc)
        return filtered

    def select_doctor(self, doctor_id, display, card_widget):
        """Handle doctor card click: mark selection, clear time, refresh slots."""
        self.selected_doctor_id = doctor_id
        self.selected_doctor_display = display
        self.highlight_selected_card(card_widget)
        self.clear_time_selection()
        self.render_slots()

    def highlight_selected_card(self, card_widget):
        """Highlight chosen doctor card and reset the previous one."""
        if self.selected_doctor_card and self.selected_doctor_card != card_widget:
            self.reset_card_style(self.selected_doctor_card)
        self.selected_doctor_card = card_widget
        card_widget.config(bg="#d6e9ff")
        for child in card_widget.winfo_children():
            child.config(bg="#d6e9ff")

    def reset_card_style(self, card_widget):
        """Return doctor card to default style."""
        card_widget.config(bg="white")
        for child in card_widget.winfo_children():
            child.config(bg="white")

    def render_slots(self):
        """Render inline slot grid or hint based on doctor/date selection."""
        for child in self.slot_container.winfo_children():
            child.destroy()
        self.selected_slot_btn = None

        if not self.selected_doctor_id or not self.date_var.get():
            Label(self.slot_container, text="Select doctor and date to view available slots",
                  bg="white", fg="gray").pack(anchor="w")
            return

        exclude_appt_id = None
        if self.appointment_id_var.get().isdigit():
            exclude_appt_id = int(self.appointment_id_var.get())
        booked_slots = self.fetch_booked_slots(self.selected_doctor_id, self.date_var.get(), exclude_appt_id)

        slot_frame = Frame(self.slot_container, bg="white", padx=2, pady=2)
        slot_frame.pack(anchor="w")

        slots = self.build_slots()
        for idx, (start, end) in enumerate(slots):
            text = f"{start}~{end}\n{self.selected_doctor_display}"
            is_booked = start in booked_slots
            btn = Button(slot_frame, text=text, width=20, justify=CENTER)
            if is_booked:
                btn.config(state=DISABLED, bg="black", fg="white", disabledforeground="white")
            else:
                btn.config(bg="green", activebackground="darkgreen",
                           command=lambda s=start, b=btn: self.set_time_and_highlight(s, b))
                if self.time_var.get() == start:
                    self._highlight_selected_button(btn)
            row, col = divmod(idx, 3)
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

        for col in range(3):
            slot_frame.grid_columnconfigure(col, weight=1)

    def build_slots(self):
        """Return list of (start, end) strings for allowed 30-minute slots."""
        fmt = "%H:%M"
        slots = []
        start = datetime.strptime("09:00", fmt)
        noon = datetime.strptime("12:00", fmt)
        while start < noon:
            end = start + timedelta(minutes=30)
            slots.append((start.strftime(fmt), end.strftime(fmt)))
            start = end

        start = datetime.strptime("13:00", fmt)
        close = datetime.strptime("16:00", fmt)
        while start < close:
            end = start + timedelta(minutes=30)
            slots.append((start.strftime(fmt), end.strftime(fmt)))
            start = end
        return slots

    def fetch_booked_slots(self, doctor_id, appointment_date, exclude_appt_id=None):
        """Fetch booked start times (HH:MM) for the doctor on the given date."""
        con = get_connection()
        cur = con.cursor()
        query = """
            SELECT appointment_time
            FROM appointment
            WHERE doctor_id=%s AND appointment_date=%s
        """
        params = [doctor_id, appointment_date]
        if exclude_appt_id:
            query += " AND appointment_id<>%s"
            params.append(exclude_appt_id)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        con.close()

        booked = set()
        for (time_value,) in rows:
            if hasattr(time_value, "strftime"):
                formatted = time_value.strftime("%H:%M")
            else:
                formatted = str(time_value)[:5]
            booked.add(formatted)
        return booked

    def _highlight_selected_button(self, btn):
        if self.selected_slot_btn and self.selected_slot_btn != btn:
            self.selected_slot_btn.config(relief=RAISED, bd=2)
        self.selected_slot_btn = btn
        self.selected_slot_btn.config(relief=SUNKEN, bd=3)

    def set_time_and_highlight(self, start_time, btn):
        self.time_var.set(start_time)
        self._highlight_selected_button(btn)

    # ---------------- CRUD ----------------

    def refresh_table(self):
        """Load all appointments into the table."""
        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("""
                SELECT a.appointment_id,
                       CONCAT(p.patient_id, ' - ', p.first_name, ' ', p.last_name) AS patient_display,
                       CONCAT(dep.department_id, ' - ', dep.name) AS department_display,
                       CONCAT(d.doctor_id, ' - ', d.first_name, ' ', d.last_name) AS doctor_display,
                       a.appointment_date,
                       a.appointment_time,
                       a.status,
                       a.doctor_rating,
                       COALESCE(a.notes, ''),
                       d.doctor_id,
                       dep.department_id
                FROM appointment a
                JOIN patient p ON a.patient_id = p.patient_id
                JOIN doctor d ON a.doctor_id = d.doctor_id
                JOIN department dep ON d.department_id = dep.department_id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """)
            rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load appointments.\n\n{e}")
            return
        finally:
            try:
                con.close()
            except Exception:
                pass

        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in rows:
            (appt_id, patient_display, dept_display, doctor_display,
             appt_date, appt_time, status, doctor_rating, notes, doctor_id, dept_id) = r
            rating_text = "" if doctor_rating is None else f"{float(doctor_rating):.1f}"
            time_text = str(appt_time)[:5]
            self.tree.insert(
                "",
                END,
                values=(appt_id, patient_display, dept_display, doctor_display, str(appt_date), time_text, status, rating_text, notes),
                tags=(f"doctor:{doctor_id}", f"dept:{dept_id}"),
            )

    def on_select_row(self, _):
        """Populate form fields when selecting a row in the table."""
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        vals = self.tree.item(item_id, "values")
        tags = self.tree.item(item_id, "tags")
        if not vals:
            return

        (appt_id, patient_display, dept_display, doctor_display,
         appt_date, appt_time, status, rating_text, notes_text) = vals

        doctor_id = None
        dept_id = None
        for tag in tags:
            if tag.startswith("doctor:"):
                doctor_id = int(tag.split(":", 1)[1])
            elif tag.startswith("dept:"):
                dept_id = int(tag.split(":", 1)[1])

        self.appointment_id_var.set(str(appt_id))
        self.patient_var.set(patient_display)
        self.department_var.set(dept_display)
        self.date_var.set(str(appt_date))
        self.time_var.set(str(appt_time)[:5])
        self.status_var.set(status)
        self.doctor_rating_var.set(rating_text)
        self.notes_var.set(notes_text)

        self.current_row_doctor_id = doctor_id

        if dept_id:
            self.load_doctors_for_department(dept_id)
            self.min_rating_var.set("All")
            self.render_doctors()

        if doctor_id:
            self.selected_doctor_id = doctor_id
            self.selected_doctor_display = doctor_display
            if self.doctor_grid_frame:
                for card in self.doctor_grid_frame.winfo_children():
                    if card.winfo_children():
                        first_label = card.winfo_children()[0]
                        if doctor_display == first_label.cget("text"):
                            self.highlight_selected_card(card)
                            break

        self.render_slots()

    def clear_form(self):
        """Clear form fields and selections."""
        self.appointment_id_var.set("")
        self.patient_var.set("")
        self.department_var.set("")
        self.date_var.set(self.date_combo["values"][0] if self.date_combo["values"] else "")
        self.time_var.set("")
        self.status_var.set("Scheduled")
        self.doctor_rating_var.set("")
        self.notes_var.set("")
        self.min_rating_var.set("All")
        self.current_row_doctor_id = None
        self.clear_doctor_selection()
        self.render_doctors()
        self.render_slots()
        self.tree.selection_remove(self.tree.selection())

    def add_appointment(self):
        patient_display = self.patient_var.get().strip()
        if not patient_display or not self.selected_doctor_id or not self.date_var.get() or not self.time_var.get():
            messagebox.showwarning("Missing", "Please choose patient, doctor, date, and time.")
            return
        try:
            patient_id = int(patient_display.split("-")[0].strip())
        except Exception:
            messagebox.showwarning("Error", "Invalid patient selection.")
            return

        doctor_rating = self.doctor_rating_var.get().strip() or None

        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("""
                INSERT INTO appointment (patient_id, doctor_id, appointment_date, appointment_time, status, doctor_rating, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (patient_id, self.selected_doctor_id,
                  self.date_var.get(), self.time_var.get(),
                  self.status_var.get(), doctor_rating, self.notes_var.get()))

            if doctor_rating is not None:
                self.recompute_avg_for_doctor(cur, self.selected_doctor_id)

            con.commit()
            messagebox.showinfo("Success", "Appointment added.")
            self.refresh_table()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            try:
                con.close()
            except Exception:
                pass

    def update_appointment(self):
        appt_id = self.appointment_id_var.get().strip()
        if not appt_id:
            messagebox.showwarning("Missing", "Select an appointment to update.")
            return
        patient_display = self.patient_var.get().strip()
        if not patient_display or not self.selected_doctor_id or not self.date_var.get() or not self.time_var.get():
            messagebox.showwarning("Missing", "Please choose patient, doctor, date, and time.")
            return
        try:
            patient_id = int(patient_display.split("-")[0].strip())
        except Exception:
            messagebox.showwarning("Error", "Invalid patient selection.")
            return

        doctor_rating = self.doctor_rating_var.get().strip() or None
        old_doctor_id = self.current_row_doctor_id

        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("""
                UPDATE appointment
                SET patient_id=%s, doctor_id=%s, appointment_date=%s,
                    appointment_time=%s, status=%s, doctor_rating=%s, notes=%s
                WHERE appointment_id=%s
            """, (patient_id, self.selected_doctor_id, self.date_var.get(),
                  self.time_var.get(), self.status_var.get(), doctor_rating, self.notes_var.get(), appt_id))

            if old_doctor_id:
                self.recompute_avg_for_doctor(cur, old_doctor_id)
            self.recompute_avg_for_doctor(cur, self.selected_doctor_id)

            con.commit()
            messagebox.showinfo("Success", "Appointment updated.")
            self.refresh_table()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            try:
                con.close()
            except Exception:
                pass

    def delete_selected(self):
        appt_id = self.appointment_id_var.get().strip()
        if not appt_id:
            messagebox.showwarning("Missing", "Select an appointment to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete this appointment?"):
            return

        doctor_id = self.selected_doctor_id or self.current_row_doctor_id
        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute("DELETE FROM appointment WHERE appointment_id=%s", (appt_id,))
            if doctor_id:
                self.recompute_avg_for_doctor(cur, doctor_id)
            con.commit()
            messagebox.showinfo("Deleted", "Appointment deleted.")
            self.refresh_table()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            try:
                con.close()
            except Exception:
                pass

    def recompute_avg_for_doctor(self, cursor, doctor_id):
        """Recompute doctor.avg_rating from appointment ratings."""
        cursor.execute("""
            UPDATE doctor d
            SET d.avg_rating = (
                SELECT AVG(a.doctor_rating)
                FROM appointment a
                WHERE a.doctor_id = d.doctor_id AND a.doctor_rating IS NOT NULL
            )
            WHERE d.doctor_id = %s
        """, (doctor_id,))
