# Clinic Appointment Management System

A desktop-based clinic appointment management system developed as a course project.  
The system integrates database design with a graphical user interface to support clinic appointment booking, management, and doctor rating.

---

## 📌 Project Overview

This project simulates a simplified clinic appointment system with two types of users:

- **Client (Patient)**:  
  Patients can browse doctors by department, select available time slots, book appointments, and rate doctors after appointments.

- **Administrator**:  
  Administrators have full control over the system, including managing departments, doctors, patients, and appointment records.

The system focuses on clear data organization, role separation, and intuitive user interaction.

---

## ⚙️ System Features

### Client Features
- Register and login as a patient
- Browse doctors by department
- View doctor information:
  - specialty
  - brief introduction
  - average rating
- Visual time-slot selection (30-minute intervals)
- Book appointments without time conflicts
- Rate doctors after booking
- Automatically refresh rating and appointment data

### Administrator Features
- Login with admin account
- Manage departments, doctors, and patients
- View all appointments
- Edit or delete appointment records when necessary

---

## 🧱 Database Design

The database is designed using a relational model and includes the following main tables:

- `department`
- `doctor`
- `patient`
- `appointment`
- `user_account`

Key design highlights:
- Clear primary and foreign key relationships
- Appointment records link patients, doctors, dates, and time slots
- Constraints prevent double booking of doctors
- Doctor ratings are stored per appointment and aggregated as average ratings

**ER Diagram** is included in the project report as *Figure 1*.

---

## 🖥️ User Interface Design

The system uses a desktop GUI implemented with basic interface components such as buttons, selection boxes, and text fields.

Design considerations:
- Simple and clear layout
- Doctor selection uses card-style blocks with ratings
- Time-slot selection is visual and intuitive
- Interface design references local hospital appointment systems in Wenzhou to improve usability

The goal is to make the booking process easy to understand without unnecessary complexity.

---

## 🛠️ Technologies Used

- **Programming Language**: Python  
- **Database**: MySQL  
- **GUI Framework**: Tkinter  
- **Development Environment**: VS Code  
- **Version Control**: Git / GitHub

---

## ▶️ How to Run the Project

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
