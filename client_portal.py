
"""
client_portal.py (v2 - bound to logged-in user)
-----------------------------------------------
Defines the ClientPortal window.

ClientPortal now receives `user_info` from MainApp, which includes:
    - username
    - role ('client')
    - patient_id (the bound patient)

We pass the patient_id to AppointmentClientFrame so that:
    - Patient is fixed (no drop-down)
    - Client can only see and manage their own appointments.
"""

from tkinter import *
from tkinter import ttk
from frames_appointment_client import AppointmentClientFrame
from frames_rating_client import RatingClientFrame


class ClientPortal:
    """
    Client portal main GUI: simple appointment booking interface.
    It is bound to a single patient (the logged-in client).
    """

    def __init__(self, root, user_info):
        self.root = root
        self.user_info = user_info
        self.patient_id = user_info.get("patient_id")

        self.root.title(f"Clinic Client Portal - {user_info.get('username', '')}")
        self.root.geometry("900x550+100+60")
        self.root.configure(bg="white")

        title = Label(
            root,
            text="Client Portal - Book an Appointment",
            bg="#1AAECB",
            fg="white",
            font=("Arial", 14, "bold"),
        )
        title.pack(fill=X)
        # Return to Login Button
        Button(root, text="Return to Login", bg="#FF6666", fg="white",
               command=root.destroy).pack(side=TOP, anchor="ne", padx=10, pady=5)

        main_frame = Frame(root, bg="white")
        main_frame.pack(fill=BOTH, expand=True)

        # Notebook holds Appointments and Rate Doctor tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True)
        self.notebook = notebook

        appointment_tab = Frame(notebook, bg="white")
        rate_tab = Frame(notebook, bg="white")

        notebook.add(appointment_tab, text="Appointments")
        notebook.add(rate_tab, text="Rate Doctor")

        # Tab content
        AppointmentClientFrame(appointment_tab, patient_id=self.patient_id)
        # Keep reference so we can trigger a refresh when the tab is shown
        self.rate_frame = RatingClientFrame(rate_tab, patient_id=self.patient_id)

        # Auto-refresh the rating tab when the user switches to it
        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        """Refresh the Rate Doctor tab when it becomes active."""
        selected = event.widget.select()
        tab_text = event.widget.tab(selected, "text")
        if tab_text == "Rate Doctor":
            self.rate_frame.force_refresh()
