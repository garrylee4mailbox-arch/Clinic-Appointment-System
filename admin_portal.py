
"""
admin_portal.py
----------------
Defines the AdminPortal window.

AdminPortal uses ttk.Notebook with the following tabs:
    - Departments
    - Patients
    - Doctors
    - Appointments (read-only overview)

Each tab is implemented by a separate frame class imported from:
    - frames_department
    - frames_patient
    - frames_doctor
    - frames_appointment_admin
"""

from tkinter import *
from tkinter import ttk

from frames_department import DepartmentFrame
from frames_patient import PatientFrame
from frames_doctor import DoctorFrame
from frames_appointment_admin import AppointmentAdminFrame


class AdminPortal:
    """
    Admin portal main GUI: manages all backend data.
    This window is typically opened from MainApp via a Toplevel.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Clinic Admin Portal")
        self.root.geometry("1200x650+80+40")
        self.root.configure(bg="white")

        title = Label(
            root,
            text="Admin Portal - Departments / Patients / Doctors / Appointments",
            bg="#1AAECB",
            fg="white",
            font=("Arial", 14, "bold"),
        )
        title.pack(fill=X)
        Button(root, text="Return to Login", bg="#FF6666", fg="white",
            command=root.destroy).pack(side=TOP, anchor="ne", padx=10, pady=5)

        notebook = ttk.Notebook(root)
        notebook.pack(fill=BOTH, expand=True)

        dept_tab = Frame(notebook, bg="white")
        patient_tab = Frame(notebook, bg="white")
        doctor_tab = Frame(notebook, bg="white")
        appointment_tab = Frame(notebook, bg="white")

        notebook.add(dept_tab, text="Departments")
        notebook.add(patient_tab, text="Patients")
        notebook.add(doctor_tab, text="Doctors")
        notebook.add(appointment_tab, text="Appointments")

        # Attach functional frames
        DepartmentFrame(dept_tab)
        PatientFrame(patient_tab)
        DoctorFrame(doctor_tab)
        AppointmentAdminFrame(appointment_tab)
