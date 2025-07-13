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

fixtures = ["DocType"]
