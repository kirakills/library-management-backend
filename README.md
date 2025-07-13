# Simple Library Management System

This project implements a web-based Library Management System with a custom API backend built on the Frappe Framework (version 15) and a standalone React frontend. It addresses the requirements of the "Coding Challenge – Simple Library Management System with Custom API."

## Table of Contents

1.  [Purpose](#1-purpose)
2.  [Features Implemented (User Stories)](#2-features-implemented-user-stories)
3.  [Technical Stack](#3-technical-stack)
4.  [Setup Instructions](#4-setup-instructions)
    * [Prerequisites](#prerequisites)
    * [Backend Setup (Frappe Bench)](#backend-setup-frappe-bench)
    * [Frontend Setup (React App)](#frontend-setup-react-app)
5.  [Running the Application](#5-running-the-application)
6.  [Architectural Decisions](#6-architectural-decisions)
7.  [Known Issues & Trade-offs](#7-known-issues--trade-offs)
8.  [Future Improvements](#8-future-improvements)
9.  [Submission Checklist](#9-submission-checklist)

---

## 1. Purpose

To build a small web application that allows authenticated users to manage books, members, and loans in a library, featuring a custom REST API and a custom frontend.

## 2. Features Implemented (User Stories)

All "MUST complete" user stories from the challenge have been implemented and verified.

* **US-01: Book CRUD:** Create, View, Edit, Delete Books via custom React frontend.
* **US-02: Member CRUD:** Create, View, Edit, Delete Members via custom React frontend.
* **US-03: Loan Creation:** Create Loan records, tracking book, member, loan date, and return date.
* **US-04: Availability Check:** Prevent duplicate loans for books already "On Loan" or "Reserved."
* **US-05: Reservation Queue:** Allow members to reserve unavailable books.
* **US-06: Overdue Notifications:** Automated daily email reminders for overdue books.
* **US-07: Reports:** Generate reports for "Books on Loan" and "Overdue Books."
* **US-08: REST API:** Secure API endpoints for all CRUD operations and custom functionalities.
* **US-09: Authentication & Roles:** User registration (via Frappe Desk initially), login, logout, and role-based access control (Administrator, Librarian, Member).
* **US-10: Custom Front-End UI:** A standalone React web interface, not relying on Frappe Desk for user-facing CRUD.

**Stretch Story (NICE to attempt):**
* **SS-03: Export Member's Loan History as CSV:** Implemented a feature to export a member's loan history to a CSV file.

## 3. Technical Stack

* **Backend:** Frappe Framework v15 (Python, MariaDB, Redis)
    * Custom Frappe App: `library_management`
    * DocTypes: `Book`, `Member`, `Loan`, `Reservation` (definitions exported to files)
    * Custom Whitelisted API Methods (Python in `api.py`)
    * Scheduler (Python)
* **Frontend:** React (TypeScript)
    * `axios` for API requests
    * `js-cookie` for session management
    * Custom CSS for UI/UX
* **Development Environment:** Windows Subsystem for Linux (WSL) with Ubuntu 22.04 LTS

## 4. Setup Instructions

### Prerequisites

1.  **Windows Subsystem for Linux (WSL):** Ensure WSL (preferably WSL2) with Ubuntu 22.04 LTS is installed and configured on your Windows machine.
2.  **Node.js & npm/yarn:** Node.js (v18 or v20 recommended) and npm (or yarn) installed in your WSL environment.
    * `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash`
    * `source ~/.bashrc` (or `~/.profile`)
    * `nvm install 18 && nvm use 18`
    * `npm install -g yarn`
3.  **Python 3.11+:** Installed and set as default in WSL.
    * `sudo add-apt-repository ppa:deadsnakes/ppa -y && sudo apt update`
    * `sudo apt install python3.11 python3.11-venv python3.11-dev -y`
    * `sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && sudo update-alternatives --config python3`
4.  **MariaDB & Redis:** Installed and running in WSL.
    * `sudo apt install mariadb-server mariadb-client redis-server -y`
    * `sudo mysql_secure_installation` (set root password)
    * Configure MariaDB: Add `character-set-client-handshake = FALSE`, `character-set-server = utf8mb4`, `collation-server = utf8mb4_unicode_ci` under `[mysqld]` and `default-character-set = utf8mb4` under `[mysql]` in `/etc/mysql/my.cnf`. Then `sudo service mysql restart`.
5.  **wkhtmltopdf:** `sudo apt install xvfb libfontconfig wkhtmltopdf -y`
6.  **Frappe Bench CLI:** `sudo pip3 install frappe-bench`
7.  **VS Code:** Installed on Windows with the "WSL" extension.

### Backend Setup (Frappe Bench)

1.  **Clone this backend repository** into your WSL home directory (e.g., `~/library-management-backend`).
2.  **Initialize Frappe Bench:**
    ```bash
    cd ~/frappe-bench # Or your preferred location for the bench
    bench init frappe-bench --python python3.11 --frappe-branch version-15
    ```
    * Remember the Frappe Administrator password you set here.
3.  **Attach your custom app:**
    * Copy the `library_management` app folder from the cloned backend repository (e.g., `~/library-management-backend/library_management`) into `~/frappe-bench/apps/`.
    * Ensure the structure is `~/frappe-bench/apps/library_management/library_management/` (the second `library_management` is the Python package root).
4.  **Install your custom app on your site:**
    ```bash
    cd ~/frappe-bench
    bench new-site mysite.localhost # Create a new site (if you don't have one, or if current is corrupted)
    bench use mysite.localhost # Set it as default
    bench --site mysite.localhost install-app library_management
    ```
5.  **Configure DocTypes in Frappe Desk:**
    * Log into `http://localhost:8000` as `Administrator`.
    * Go to `DocType List`. Verify `Book`, `Member`, `Loan`, `Reservation` DocTypes are present under `Library Management` module.
    * **Crucial for Member:** Ensure `Member` DocType has a field `title` (Field Name: `title`, Type: `Data`, Mandatory: Checked) and in `Settings`, `Autoname` is `field:membership_id` and `Title Field` is `title`.
6.  **Configure Roles & Permissions:**
    * Go to `Role List`. Ensure `Librarian` and `Member` roles exist.
    * Go to `Role Permissions Manager`.
        * **For DocType `User`:**
            * Select `Role: Administrator`. Ensure `Read`, `Write`, `Create`, `Delete` are checked.
            * Select `Role: Librarian`. Ensure `Read` is checked.
        * **For your custom DocTypes (Book, Member, Loan, Reservation):**
            * **Administrator:** Full CRUD (Read, Write, Create, Delete).
            * **Librarian:** Full CRUD on Book, Member, Loan, Reservation.
            * **Member:** Read on Book, Member, Loan. Read & Create on Reservation.
7.  **Configure Email Account for Overdue Notifications:**
    * Go to `Email Account List`. Click `+ Add Email Account`.
    * Fill in your outgoing SMTP details (e.g., `smtp.gmail.com`, port `587`, `Use TLS`).
    * For Gmail, generate an [App Password](https://myaccount.google.com/apppasswords) (requires 2-Step Verification). Use this App Password in Frappe.
    * Check `Set as Default Outgoing`. Save.
8.  **Enable Scheduler:**
    * Go to `System Settings` -> `Advanced` tab.
    * Set "Run Jobs Daily if Inactive For (Days)" to `0`. Save.
9.  **Create Reports in Frappe Desk:**
    * Go to `Report List`.
    * Create `Books On Loan`: Name: `Books On Loan`, Type: `Script Report`, Module: `Library Management`, Ref DocType: `Loan`, Reference: `library_management.report.books_on_loan.books_on_loan.execute`. Save.
    * Create `Overdue Books`: Name: `Overdue Books`, Type: `Script Report`, Module: `Library Management`, Ref DocType: `Loan`, Reference: `library_management.report.overdue_books.overdue_books.execute`. Save.
10. **Export DocType Definitions to Files (for Git):**
    ```bash
    cd ~/frappe-bench/apps/library_management/library_management/
    mkdir -p doctype/book doctype/member doctype/loan doctype/reservation # Create folders
    bench export-json Book doctype/book/book.json
    bench export-json Member doctype/member/member.json
    bench export-json Loan doctype/loan/loan.json
    bench export-json Reservation doctype/reservation/reservation.json
    ```
11. **Final Backend Build & Restart:**
    ```bash
    cd ~/frappe-bench
    bench migrate
    bench restart
    ```

### Frontend Setup (React App)

1.  **Clone this frontend repository** into a separate directory (e.g., `~/library-frontend`).
2.  **Install Node.js dependencies:**
    ```bash
    cd ~/library-frontend
    npm install # or yarn install
    npm i --save-dev @types/js-cookie # For TypeScript types
    ```
3.  **Update API Secrets:**
    * Log into Frappe Desk as `Administrator`. Go to `User List` -> `Administrator` -> `API Access` -> `Generate Keys`.
    * Copy the new 16-character API Secret.
    * Update `FRAPPE_API_SECRET` in **ALL** of these files with this new secret:
        * `src/components/BookForm.tsx`
        * `src/components/BookList.tsx`
        * `src/components/MemberForm.tsx`
        * `src/components/MemberList.tsx`
        * `src/components/LoanAndReservationForm.tsx`
        * `src/components/ReportViewer.tsx`
        * `src/context/AuthContext.tsx`
    * **Save all these files.**
4.  **Add Font Awesome CDN:**
    * Open `public/index.html`.
    * Add this line inside the `<head>` section:
        `<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" integrity="sha512-iBBXm8fW90+nuLcSKlbmrPcLa0ot92xO1BIsZ+ywDWZCvqsWgccV3gFoRBv0z+8dLJgyAHIhR35VZc2oM/gI1w==" crossorigin="anonymous" referrerpolicy="no-referrer" />`
    * Save.

## 5. Running the Application

1.  **Start Frappe Backend:**
    ```bash
    cd ~/frappe-bench
    bench start
    ```
    * Keep this terminal running.
2.  **Start React Frontend:**
    ```bash
    cd ~/library-frontend
    npm start # or yarn start
    ```
    * This will open your app in the browser at `http://localhost:3000`.
3.  **Log in:** Use `Administrator` or a test user (e.g., `librarian@example.com`, `member@example.com`) with their respective passwords.

## 6. Architectural Decisions

* **Frappe as Backend:** Leverages Frappe's robust DocType system for data modeling (Books, Members, Loans, Reservations), built-in database (MariaDB), and real-time capabilities (Redis).
* **Separate Frontend (React):** Provides a completely custom and independent user interface, fulfilling the challenge's requirement to not rely on Frappe Desk for user-facing CRUD. This allows for full control over UI/UX.
* **REST API Communication:** All frontend-backend communication is done via Frappe's REST API endpoints (`/api/resource/` for standard CRUD, `/api/method/` for custom logic).
* **Custom Whitelisted Methods:** For complex transactions (Loan/Reservation creation with availability checks) and data fetching (Reports, CSV Export), custom whitelisted Python methods were created in `api.py`. This ensures atomicity and backend control over business logic.
* **Role-Based Access Control:** Frontend UI elements and backend API calls are conditionally rendered/authorized based on the user's assigned roles (Administrator, Librarian, Member), ensuring appropriate access levels.
* **Modular Frontend Components:** React components are organized (`BookForm`, `BookList`, `MemberForm`, `MemberList`, `LoanAndReservationForm`, `ReportViewer`, `Login`, `Sidebar`) for better maintainability and reusability.
* **Centralized Interfaces:** TypeScript interfaces are defined in `src/interfaces.ts` for consistent data typing across the frontend.

## 7. Known Issues & Trade-offs

This project faced several challenging and persistent environment-specific issues during development in WSL that required workarounds and led to certain trade-offs:

* **Administrator Role Corruption (Major Issue):**
    * **Problem:** The `Administrator` role in the Frappe Desk Role Permissions Manager was corrupted, preventing explicit permissions from being set for the `User` DocType. This led to `403 FORBIDDEN` errors when the frontend tried to fetch user details (email, full name, roles) via `/api/resource/User/username` after login. This also caused Frappe to issue `sid=Guest` cookies, breaking session persistence on page reload.
    * **Trade-off/Workaround:** Instead of recreating the entire Frappe site (which would lose all data and was avoided due to deadline), the `AuthContext.tsx` was modified to:
        * **Bypass the problematic `/api/resource/User` API call** after login.
        * **Reconstruct the `user` object (username, full_name, roles, email) directly in the frontend** based on the username returned by `/api/method/frappe.auth.get_logged_user` and hardcoded assumptions for common roles (Administrator, Librarian, Member).
        * **Use `localStorage` to store the `last_logged_username`** to persist the assumed user identity across page reloads.
    * **Impact:** The core Frappe backend corruption remains, but the frontend provides a functional and persistent login experience.

* **Frappe Hooks Not Reliably Firing (Major Issue):**
    * **Problem:** Standard Frappe DocType event hooks (`before_save`, `on_submit`) for `Loan` and `Reservation` were not reliably firing, preventing automatic updates to `Book` status and availability checks.
    * **Trade-off/Workaround:** The core logic for `Book` status updates (US-03, US-05) and Availability Checks (US-04) was moved into **custom whitelisted API methods** (`create_loan_transaction`, `create_reservation_transaction` in `api.py`). The frontend now calls these atomic transaction methods directly after a successful loan/reservation creation.
    * **Impact:** Functionality is achieved, but it bypasses Frappe's intended hook system for these specific actions.

* **Non-Standard Python Module Path:**
    * **Problem:** The Frappe app's Python package structure required a shorter import path (e.g., `library_management.module.file` instead of `library_management.library_management.module.file`) to resolve `ModuleNotFoundError` for whitelisted methods and report imports.
    * **Trade-off:** All backend Python code and frontend API calls use this shorter path.

* **UI Polish:**
    * **Trade-off:** Due to time constraints and prioritizing core functionality, the UI is functional and responsive but lacks the very high level of aesthetic detail (e.g., custom illustrations, intricate animations) seen in the provided UI examples.

## 8. Future Improvements

* **Return Book Functionality:** Implement a "Return Book" feature, which would update the Loan status to "Returned" and the Book status back to "Available."
* **User Registration:** Allow public user registration directly from the frontend (requires whitelisting `frappe.core.doctype.user.user.create_user` and careful permission handling).
* **Member Self-Service:** Allow members to view/manage only their own loans and reservations.
* **Advanced Report Filters:** Add more filtering options to the reports.
* **Enhanced UI/UX:** Further polish the visual design, add animations, and improve user feedback.
* **Comprehensive Testing:** Implement automated unit and integration tests for both frontend and backend.
* **Production Deployment:** Set up a production environment (e.g., using Frappe Docker or Ansible).

## 9. Submission Checklist

* [ ] Repo pushed to GitHub/GitLab.
* [ ] README.md covering setup, run, architectural decisions, and shortcuts/trade-offs.
* [ ] Final commit tagged submission.
* [ ] Reply to the original email with a short cover note, the repo link, and a screen-recording demo.
