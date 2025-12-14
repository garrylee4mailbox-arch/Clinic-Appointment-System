"""
frames_appointment_client.py
----------------------------
Client appointment booking frame
- Department -> Doctor cascading filter
- Client bound to ONE patient_id
"""

from tkinter import *
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
from db_config import get_connection


class AppointmentClientFrame:

    def __init__(self, parent, patient_id):
        self.patient_id = patient_id

        self.department_var = StringVar()
        self.date_var = StringVar()
        self.time_var = StringVar()
        self.notes_var = StringVar()
        self.rating_var = StringVar(value="All")
        self.selected_slot_btn = None
        self.selected_doctor_id = None
        self.selected_doctor_display = ""
        self.selected_doctor_card = None

        self.departments = []
        self.doctors = []

        # ----------- top form: department/date/time/notes -----------
        form = Frame(parent, bg="white")
        form.pack(fill=X, padx=10, pady=5)

        Label(form, text="Client Appointment Booking",
              font=("Arial", 12, "bold"),
              bg="white").grid(row=0, column=0, columnspan=6, sticky="w")

        # Department
        Label(form, text="Department", bg="white").grid(row=1, column=0, sticky="w")
        self.dept_combo = ttk.Combobox(form, textvariable=self.department_var,
                                       state="readonly", width=25)
        self.dept_combo.grid(row=1, column=1, padx=5)
        self.dept_combo.bind("<<ComboboxSelected>>", self.on_department_change)

        # Date
        Label(form, text="Date", bg="white").grid(row=2, column=0, sticky="w")
        self.date_combo = ttk.Combobox(form, textvariable=self.date_var,
                                       state="readonly", width=18)
        self.date_combo.grid(row=2, column=1)
        self.date_combo.bind("<<ComboboxSelected>>", self.on_date_change)

        # Time
        Label(form, text="Time", bg="white").grid(row=2, column=2, sticky="w")
        self.time_entry = Entry(form, textvariable=self.time_var,
                                state="readonly", width=18)
        self.time_entry.grid(row=2, column=3)

        # Notes
        Label(form, text="Notes", bg="white").grid(row=3, column=0, sticky="w")
        Entry(form, textvariable=self.notes_var, width=60).grid(row=3, column=1, columnspan=4, sticky="w")

        Button(form, text="Book", width=12, command=self.add_appointment).grid(row=1, column=5, rowspan=2)

        # ----------- doctor grid + rating filter -----------
        self.doctor_container = Frame(parent, bg="white")
        self.doctor_container.pack(fill=X, padx=10, pady=(5, 0), anchor="w")

        # ----------- slot container under doctor grid -----------
        self.slot_container = Frame(parent, bg="white")
        self.slot_container.pack(fill=X, padx=10, pady=(5, 0), anchor="w")

        self.init_dates()
        self.load_departments()
        self.render_doctors()
        self.render_slots()

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

    def on_department_change(self, _):
        """Handle department selection: load doctors, reset selections, and refresh UI."""
        dept_id = int(self.department_var.get().split("-")[0])
        self.load_doctors_for_department(dept_id)
        self.rating_var.set("All")
        self.selected_doctor_id = None
        self.selected_doctor_display = ""
        self.selected_doctor_card = None
        self.clear_time_selection()
        self.render_doctors()
        self.render_slots()

    def on_date_change(self, _):
        self.clear_time_selection()
        self.render_slots()

    def clear_time_selection(self):
        """Reset chosen time and selected slot highlight."""
        self.time_var.set("")
        if self.selected_slot_btn:
            self.selected_slot_btn.config(relief=RAISED, bd=2)
            self.selected_slot_btn = None

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

    def render_doctors(self):
        """Render doctor cards with rating filter and selection highlight."""
        for child in self.doctor_container.winfo_children():
            child.destroy()

        # Rating filter bar
        filter_frame = Frame(self.doctor_container, bg="white")
        filter_frame.pack(anchor="w", pady=(0, 5), fill=X)
        Label(filter_frame, text="Min Rating", bg="white").pack(side=LEFT)
        rating_combo = ttk.Combobox(filter_frame, textvariable=self.rating_var,
                                    state="readonly", width=8,
                                    values=["All", "5.0", "4.5", "4.0", "3.5", "3.0", "2.5", "2.0", "1.5", "1.0"])
        rating_combo.pack(side=LEFT, padx=5)
        rating_combo.bind("<<ComboboxSelected>>", self.on_rating_change)

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

    def on_rating_change(self, _):
        """Update doctor grid based on rating filter and clear selections if needed."""
        filtered_ids = {doc[0] for doc in self.get_filtered_doctors()}
        if self.selected_doctor_id and self.selected_doctor_id not in filtered_ids:
            self.selected_doctor_id = None
            self.selected_doctor_display = ""
            self.selected_doctor_card = None
            self.clear_time_selection()
        self.render_doctors()
        self.render_slots()

    def get_filtered_doctors(self):
        """Return doctors filtered by the current minimum rating."""
        value = self.rating_var.get()
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

        if not self.selected_doctor_id or not self.date_var.get():
            Label(self.slot_container, text="Select doctor and date to view available slots",
                  bg="white", fg="gray").pack(anchor="w")
            return

        booked_slots = self.fetch_booked_slots(self.selected_doctor_id, self.date_var.get())

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

    def fetch_booked_slots(self, doctor_id, appointment_date):
        """Fetch booked start times (HH:MM) for the doctor on the given date."""
        con = get_connection()
        cur = con.cursor()
        cur.execute("""
            SELECT appointment_time
            FROM appointment
            WHERE doctor_id=%s AND appointment_date=%s
        """, (doctor_id, appointment_date))
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

    def add_appointment(self):
        if not self.selected_doctor_id or not self.time_var.get():
            messagebox.showwarning("Missing", "Please complete all fields")
            return

        con = get_connection()
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO appointment (patient_id, doctor_id, appointment_date, appointment_time, notes)
                VALUES (%s,%s,%s,%s,%s)
            """, (self.patient_id, self.selected_doctor_id,
                  self.date_var.get(), self.time_var.get(),
                  self.notes_var.get()))
            con.commit()
            messagebox.showinfo("Success", "Appointment booked")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            con.close()
