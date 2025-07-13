import frappe

def on_reservation_submit(doc, method):
    frappe.log_error(f"on_reservation_submit hook for Reservation '{doc.name}' triggered. Book: {doc.book}, Member: {doc.member}", "Reservation Hook Fired")

    # Get current book status before update
    current_book_status = frappe.db.get_value("Book", doc.book, "status")
    frappe.log_error(f"Book '{doc.book}' status before update in on_submit: {current_book_status}", "Reservation Hook Debug")

    # When a reservation is submitted, update the book status to Reserved
    frappe.db.set_value("Book", doc.book, "status", "Reserved")
    frappe.db.set_value("Book", doc.book, "current_reservation", doc.name) # Link reservation to book
    frappe.log_error(f"Attempted to set Book '{doc.book}' status to 'Reserved' and current_reservation to '{doc.name}'", "Reservation Hook Debug")

    frappe.db.commit()
    frappe.log_error(f"frappe.db.commit() called after on_reservation_submit for '{doc.name}'.", "Reservation Hook Fired")

def on_reservation_cancel(doc, method):
    frappe.log_error(f"on_reservation_cancel hook for Reservation '{doc.name}' triggered.", "Reservation Hook Fired")

    # When a reservation is cancelled, check if the book can be set back to Available
    book_doc = frappe.get_doc("Book", doc.book)
    frappe.log_error(f"Book '{doc.book}' current status in on_cancel: {book_doc.status}, current_reservation: {book_doc.current_reservation}", "Reservation Hook Debug")

    if book_doc.status == "Reserved" and book_doc.current_reservation == doc.name:
        # Only change status if this specific reservation was the active one
        frappe.db.set_value("Book", doc.book, "status", "Available")
        frappe.db.set_value("Book", doc.book, "current_reservation", None)
        frappe.log_error(f"Book '{doc.book}' status set to 'Available' after cancelation of '{doc.name}'", "Reservation Hook Debug")
    else:
        frappe.log_error(f"Book '{doc.book}' status not changed (not Reserved by this reservation or already available) on cancel of '{doc.name}'", "Reservation Hook Debug")

    frappe.db.commit()
    frappe.log_error(f"frappe.db.commit() called after on_reservation_cancel for '{doc.name}'.", "Reservation Hook Fired")
