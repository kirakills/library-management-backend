app_name = "library_management"
app_title = "Library Management"
app_publisher = "MyKey"
app_description = "Simple Library Management System for Coding Challenge"
app_email = "michaelmitiku0@gmail.com"
app_license = "mit"

# Document Events
# ---------------
# Hook on document methods and events
# These hooks are defined here but their primary functions are now handled by API methods
doctype_events = {
    "Loan": {
        "before_save": "library_management.doc_events.loan.before_loan_save",
        "on_submit": "library_management.doc_events.loan.on_loan_submit",
        "on_cancel": "library_management.doc_events.loan.on_loan_cancel_or_return"
    },
    "Reservation": {
        "on_submit": "library_management.doc_events.reservation.on_reservation_submit",
        "on_cancel": "library_management.doc_events.reservation.on_reservation_cancel"
    }
}

# Scheduled Tasks
# ---------------
scheduler_events = {
    "daily": [
        "library_management.utils.scheduler_jobs.send_overdue_reminders"
    ]
}

# Testing
# -------
# You can uncomment and use other hooks as needed for your app.
# The remaining content of hooks.py is standard boilerplate.