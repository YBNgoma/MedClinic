# MedClinic: Web-Based Clinic Management System

MedClinic is a comprehensive, Flask-based web application designed to streamline the daily operations of a medical clinic. It provides modules for managing patients, appointments, medical records, and staff, all accessible through an intuitive web interface.

## Features

-   **User Authentication**: Secure login, logout, and session management with password hashing.
-   **Role-Based Access Control**: Differentiated access levels for 'admin' and 'doctor' roles, ensuring data security and appropriate functionality.
-   **Patient Management**:
    -   Register new patients with detailed information (demographics, contact, medical history).
    -   View, edit, and search for patient records.
    -   Comprehensive patient profiles including appointments and medical history.
-   **Appointment Scheduling**:
    -   Schedule new appointments, linking patients with doctors.
    -   View appointments by date, status, or doctor.
    -   Update appointment details and status (e.g., scheduled, completed, canceled).
    -   Dashboard view of today's appointments.
-   **Medical Records**:
    -   Create and manage medical records for patient visits.
    -   Record symptoms, diagnosis, treatment, and prescriptions.
    -   View patient medical history chronologically.
-   **Staff Management (Admin)**:
    -   Add, view, and edit staff (user) accounts.
    -   Manage user roles and credentials.
-   **Reporting Module**:
    -   Generate reports on appointments (filterable by date range, status, doctor).
    -   View patient demographic statistics (e.g., gender distribution, new patients over time).
-   **User Profile Management**: Staff can update their own profile information and password.
-   **SQLite Database**: Utilizes SQLite for a lightweight and file-based database solution.
-   **Dashboard**: At-a-glance overview of key clinic metrics like total patients and today's appointments.

---
## Screenshots

Below are some anticipated screenshots of the application in action:

**Login Page**
![Screenshot_20250604_130730](https://github.com/user-attachments/assets/cf1d53ae-2e53-4e14-a5d1-a696e55d4a45)



**Dashboard**
*(Placeholder for Dashboard Screenshot: e.g., `![dashboard](link_to_dashboard_screenshot.png)`)*

**Patient Management**
*(Placeholder for Patient List Screenshot: e.g., `![patient-list](link_to_patient_list_screenshot.png)`)*

**Appointment Scheduling**
*(Placeholder for Appointment Calendar/List Screenshot: e.g., `![appointments](link_to_appointments_screenshot.png)`)*

---

## Setup Instructions

### Prerequisites

Ensure you have the following installed:

-   Python 3.7+
-   Pip (Python package manager)
-   Virtual environment manager (optional but recommended)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/YBNgoma/MedClinic.git
    cd MedClinic
    ```

2.  **Set Up a Virtual Environment**
    (Optional but recommended)
    ```bash
    python3 -m venv venv
    source venv/bin/activate      # On macOS/Linux
    venv\Scripts\activate         # On Windows
    ```

3.  **Install Dependencies**
    Create a `requirements.txt` file with the following content:
    ```
    Flask
    Werkzeug
    ```
    Then install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Initialization**
    The application will automatically create and initialize the `clinic.db` SQLite database file in the root directory when you first run `app.py` if it doesn't already exist. An initial admin user (`admin`/`admin123`) will also be created.

5.  **Secret Key (Optional Enhancement)**
    The `app.secret_key` is currently hardcoded in `app.py`. For production environments, it's recommended to set this as an environment variable.
    ```bash
    export SECRET_KEY="your_very_secret_key"      # On macOS/Linux
    set SECRET_KEY="your_very_secret_key"         # On Windows
    ```
    And modify `app.py` to use `os.environ.get('SECRET_KEY')`.

---

### Running the Application

1.  **Start the Flask Application**
    ```bash
    python app.py
    ```

2.  **Access the Web Interface**
    Open your browser and navigate to:
    ```
    http://0.0.0.0:3456/
    ```
    Or, if running on `127.0.0.1`:
    ```
    http://127.0.0.1:3456/
    ```

---

## Cross-Platform Deployment

### Windows
-   Run the application directly with Python as described above.
-   Consider creating a batch file for ease of execution.

### macOS/Linux
-   Use the terminal to execute the Python script.
-   For production use, deploy with a WSGI server like Gunicorn or uWSGI and a process manager like `supervisord` or `systemd`.

### Docker (Optional)
1.  **Create a `Dockerfile`**
    ```dockerfile
    FROM python:3.9-slim
    WORKDIR /app
    COPY requirements.txt requirements.txt
    RUN pip install -r requirements.txt
    COPY . .
    ENV FLASK_APP=app.py
    ENV FLASK_RUN_HOST=0.0.0.0
    ENV FLASK_RUN_PORT=3456
    EXPOSE 3456
    CMD ["flask", "run"]
    ```

2.  **Build Docker Image**
    ```bash
    docker build -t MedClinic:latest .
    ```

3.  **Run the Container**
    ```bash
    docker run -p 3456:3456 MedClinic:latest
    ```

---

## Directory Structure

(Assuming standard Flask project structure alongside your `app.py`)
