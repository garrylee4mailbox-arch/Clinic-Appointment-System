
"""
frames_rating_client.py
-----------------------
Client-side "Rate Doctor" tab.

Purpose:
    Allow a client (bound to one patient_id) to rate doctors for completed visits,
    WITHOUT requiring a separate "Completed" status workflow.

Design:
    - Shows this patient's appointment history (with department + doctor).
    - Allows rating ONLY when doctor_rating is NULL.
    - Rating options: 5.0 down to 1.0 in steps of 0.5 (matches your UI requirement).
    - On submit:
        1) Update appointment.doctor_rating
        2) Recompute doctor.avg_rating from appointment table (AVG of non-NULL ratings)

Database assumptions:
    - appointment has column doctor_rating DECIMAL(2,1) NULL
    - doctor has column avg_rating DECIMAL(3,2) NULL
"""

from __future__ import annotations

from tkinter import *
from tkinter import ttk, messagebox

from db_config import get_connection


class RatingClientFrame:
    """A tab for clients to rate their appointments."""

    def __init__(self, parent, patient_id: int):
        self.patient_id = patient_id

        # -------------------- UI variables --------------------
        self.selected_appt_id = StringVar()
        self.selected_doctor_id = StringVar()
        self.selected_doctor_display = StringVar()
        self.selected_date = StringVar()
        self.selected_time = StringVar()
        self.selected_current_rating = StringVar()

        self.new_rating_var = StringVar()

        # -------------------- Layout --------------------------
        root = Frame(parent, bg="white")
        root.pack(fill=BOTH, expand=True)

        header = Frame(root, bg="white")
        header.pack(fill=X, padx=12, pady=(10, 6))

        Label(header, text="Rate Doctor", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        Label(
            header,
            text="Tip: Only appointments without a rating can be rated.",
            bg="white",
            fg="gray",
        ).pack(anchor="w")

        # Top form (details + rating)
        form = Frame(root, bg="white")
        form.pack(fill=X, padx=12, pady=6)

        Label(form, text="Appointment ID", bg="white").grid(row=0, column=0, sticky="w")
        Entry(form, textvariable=self.selected_appt_id, width=12, state="readonly").grid(row=0, column=1, padx=6, sticky="w")

        Label(form, text="Doctor", bg="white").grid(row=0, column=2, sticky="w")
        Entry(form, textvariable=self.selected_doctor_display, width=28, state="readonly").grid(row=0, column=3, padx=6, sticky="w")

        Label(form, text="Date", bg="white").grid(row=1, column=0, sticky="w", pady=(8, 0))
        Entry(form, textvariable=self.selected_date, width=14, state="readonly").grid(row=1, column=1, padx=6, sticky="w", pady=(8, 0))

        Label(form, text="Time", bg="white").grid(row=1, column=2, sticky="w", pady=(8, 0))
        Entry(form, textvariable=self.selected_time, width=10, state="readonly").grid(row=1, column=3, padx=6, sticky="w", pady=(8, 0))

        Label(form, text="Current Rating", bg="white").grid(row=2, column=0, sticky="w", pady=(8, 0))
        Entry(form, textvariable=self.selected_current_rating, width=12, state="readonly").grid(row=2, column=1, padx=6, sticky="w", pady=(8, 0))

        Label(form, text="New Rating", bg="white").grid(row=2, column=2, sticky="w", pady=(8, 0))
        rating_values = [f"{x/2:.1f}" for x in range(10, 1, -1)]  # 5.0, 4.5, ..., 1.0
        self.rating_combo = ttk.Combobox(form, textvariable=self.new_rating_var, state="readonly", width=10, values=rating_values)
        self.rating_combo.grid(row=2, column=3, padx=6, sticky="w", pady=(8, 0))

        btns = Frame(form, bg="white")
        btns.grid(row=0, column=4, rowspan=3, padx=(18, 0), sticky="n")

        Button(btns, text="Submit Rating", width=14, command=self.submit_rating).pack(pady=2)
        Button(btns, text="Refresh", width=14, command=self.refresh).pack(pady=2)
        Button(btns, text="Clear", width=14, command=self.clear_selection).pack(pady=2)

        # Table (appointment list)
        table = Frame(root, bg="white")
        table.pack(fill=BOTH, expand=True, padx=12, pady=(6, 12))

        self.tree = ttk.Treeview(
            table,
            columns=("appt_id", "department", "doctor", "date", "time", "rating"),
            show="headings",
        )
        self.tree.heading("appt_id", text="Appointment ID")
        self.tree.heading("department", text="Department")
        self.tree.heading("doctor", text="Doctor")
        self.tree.heading("date", text="Date")
        self.tree.heading("time", text="Time")
        self.tree.heading("rating", text="Doctor Rating")

        self.tree.column("appt_id", width=110)
        self.tree.column("department", width=160)
        self.tree.column("doctor", width=220)
        self.tree.column("date", width=110)
        self.tree.column("time", width=90)
        self.tree.column("rating", width=110)

        vsb = Scrollbar(table, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Initial load
        self.refresh()

    # =========================================================
    # Data loading
    # =========================================================
    def refresh(self) -> None:
        """Reload this patient's appointments into the table."""
        try:
            con = get_connection()
            cur = con.cursor()
            cur.execute(
                """
                SELECT a.appointment_id,
                       dep.name AS department_name,
                       CONCAT(d.doctor_id, ' - ', d.first_name, ' ', d.last_name) AS doctor_display,
                       a.appointment_date,
                       a.appointment_time,
                       a.doctor_rating,
                       d.doctor_id
                FROM appointment a
                JOIN doctor d ON a.doctor_id = d.doctor_id
                JOIN department dep ON d.department_id = dep.department_id
                WHERE a.patient_id = %s
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                """,
                (self.patient_id,),
            )
            rows = cur.fetchall()

            # clear table
            for item in self.tree.get_children():
                self.tree.delete(item)

            # insert rows; keep doctor_id hidden via tags/values mapping
            for r in rows:
                appt_id, dep_name, doctor_display, appt_date, appt_time, doctor_rating, doctor_id = r
                rating_text = "" if doctor_rating is None else f"{float(doctor_rating):.1f}"
                time_text = str(appt_time)[:5]
                self.tree.insert("", END, values=(appt_id, dep_name, doctor_display, str(appt_date), time_text, rating_text), tags=(str(doctor_id),))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load appointments.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass

    def force_refresh(self) -> None:
        """Allow parent tabs to force a refresh when the tab is shown."""
        self.refresh()
        self.clear_selection()

    # =========================================================
    # Selection handling
    # =========================================================
    def clear_selection(self) -> None:
        """Clear selection + disable rating when not applicable."""
        self.selected_appt_id.set("")
        self.selected_doctor_id.set("")
        self.selected_doctor_display.set("")
        self.selected_date.set("")
        self.selected_time.set("")
        self.selected_current_rating.set("")
        self.new_rating_var.set("")

        # By default allow choosing a new rating, but submit will validate selection.
        self.rating_combo.configure(state="readonly")

    def on_select(self, _event) -> None:
        """Populate details when selecting a row."""
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        vals = self.tree.item(item_id, "values")
        tags = self.tree.item(item_id, "tags")

        appt_id, dep_name, doctor_display, appt_date, appt_time, rating_text = vals
        doctor_id = tags[0] if tags else ""

        self.selected_appt_id.set(str(appt_id))
        self.selected_doctor_id.set(str(doctor_id))
        self.selected_doctor_display.set(str(doctor_display))
        self.selected_date.set(str(appt_date))
        self.selected_time.set(str(appt_time))
        self.selected_current_rating.set(rating_text)

        # If already rated, lock the rating combobox to prevent edits
        if rating_text.strip() != "":
            self.rating_combo.configure(state="disabled")
            self.new_rating_var.set("")
        else:
            self.rating_combo.configure(state="readonly")

    # =========================================================
    # Submit rating
    # =========================================================
    def submit_rating(self) -> None:
        """Submit a doctor rating for the selected appointment (only if unrated)."""
        appt_id = self.selected_appt_id.get().strip()
        doctor_id = self.selected_doctor_id.get().strip()
        current_rating = self.selected_current_rating.get().strip()
        new_rating = self.new_rating_var.get().strip()

        if not appt_id:
            messagebox.showwarning("Missing", "Please select an appointment first.")
            return
        if current_rating != "":
            messagebox.showwarning("Not Allowed", "This appointment is already rated.")
            return
        if not new_rating:
            messagebox.showwarning("Missing", "Please choose a new rating (5.0 ~ 1.0).")
            return
        if not doctor_id:
            messagebox.showerror("Error", "Internal error: doctor_id not found for selected row.")
            return

        try:
            con = get_connection()
            cur = con.cursor()

            # 1) Update the appointment rating
            cur.execute(
                """
                UPDATE appointment
                SET doctor_rating = %s
                WHERE appointment_id = %s AND patient_id = %s AND doctor_rating IS NULL
                """,
                (new_rating, appt_id, self.patient_id),
            )

            # 2) Recompute doctor's avg_rating from all ratings
            cur.execute(
                """
                UPDATE doctor d
                SET d.avg_rating = (
                    SELECT AVG(a.doctor_rating)
                    FROM appointment a
                    WHERE a.doctor_id = d.doctor_id AND a.doctor_rating IS NOT NULL
                )
                WHERE d.doctor_id = %s
                """,
                (doctor_id,),
            )

            con.commit()
            messagebox.showinfo("Success", "Rating submitted and doctor average updated.")

            # Refresh UI
            self.refresh()
            self.clear_selection()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit rating.\n\n{e}")
        finally:
            try:
                con.close()
            except Exception:
                pass
