import frappe

def before_loan_save(doc, method):
    # This hook is intended for availability check, but it was not reliably firing.
    # The primary availability check is now in update_book_status_after_transaction.
    # Keep this here for completeness or if it starts working later.
    frappe.log_error(f"before_loan_save hook for Loan '{doc.name}' triggered. Status: {doc.status}", "Loan Hook Fired (from original location)")

    if doc.status == "Active":
        if not frappe.db.exists("Book", doc.book):
            frappe.throw(f"Book '{doc.book}' does not exist.")

        book_status = frappe.db.get_value("Book", doc.book, "status")
        frappe.log_error(f"Book '{doc.book}' current status for validation (original hook): {book_status}", "Loan Hook Debug (original location)")

        if book_status == "On Loan":
            frappe.throw(f"Book '{doc.book}' is already on loan and cannot be loaned again. (Original hook)")
        elif book_status == "Reserved":
            reservations = frappe.get_all("Reservation",
                                        filters={"book": doc.book, "member": doc.member, "status": "Pending"},
                                        limit=1)
            if not reservations:
                frappe.throw(f"Book '{doc.book}' is reserved by another member and cannot be loaned. (Original hook)")
    frappe.log_error(f"before_loan_save hook for Loan '{doc.name}' finished validation (original location).", "Loan Hook Fired (from original location)")


def on_loan_submit(doc, method):
    # This hook is intended for status update, but it was not reliably firing.
    # The primary status update is now in update_book_status_after_transaction.
    # Keep this here for completeness or if it starts working later.
    frappe.log_error(f"on_loan_submit hook for Loan '{doc.name}' triggered (original location). Book: {doc.book}, Member: {doc.member}", "Loan Hook Fired (from original location)")

    current_book_status = frappe.db.get_value("Book", doc.book, "status")
    frappe.log_error(f"Book '{doc.book}' status before update in on_submit (original hook): {current_book_status}", "Loan Hook Debug (original location)")

    frappe.db.set_value("Book", doc.book, "status", "On Loan")
    frappe.db.set_value("Book", doc.book, "current_borrower", doc.member)

    try:
        reservations = frappe.get_all("Reservation", filters={"book": doc.book, "member": doc.member, "status": "Pending"}, limit=1)
        if reservations:
            frappe.db.set_value("Reservation", reservations[0].name, "status", "Fulfilled")
            frappe.log_error(f"Fulfilled Reservation {reservations[0].name} for Book '{doc.book}' (original hook)", "Loan Hook Debug (original location)")
    except Exception as e:
        frappe.log_error(f"Error fulfilling reservation for Book '{doc.book}' (original hook): {e}", "Loan Hook Error (original location)")

    frappe.db.commit()
    frappe.log_error(f"frappe.db.commit() called after on_loan_submit for '{doc.name}' (original location).", "Loan Hook Fired (from original location)")


def on_loan_cancel_or_return(doc, method):
    # This hook is intended for status update, but it was not reliably firing.
    # Keep this here for completeness or if it starts working later.
    frappe.log_error(f"on_loan_cancel_or_return hook for Loan '{doc.name}' triggered (original location). Status: {doc.status}", "Loan Hook Fired (from original location)")

    frappe.db.set_value("Book", doc.book, "status", "Available")
    frappe.db.set_value("Book", doc.book, "current_borrower", None)
    frappe.db.set_value("Book", doc.book, "current_reservation", None)
    frappe.log_error(f"Attempted to set Book '{doc.book}' status to 'Available' (original hook)", "Loan Hook Debug (original location)")

    frappe.db.commit()
    frappe.log_error(f"frappe.db.commit() called after on_loan_cancel_or_return for '{doc.name}' (original location).", "Loan Hook Fired (from original location)")


@frappe.whitelist() # This decorator is crucial for API access
def update_book_status_after_transaction(book_name, status, member_name=None, reservation_name=None):
    """
    Custom API method to update book status after a loan or reservation.
    Includes availability check logic.
    """
    frappe.log_error(f"WORKAROUND: API Method called - Book: {book_name}, Target Status: {status}", "API Status Update Debug")

    # --- START US-04 Availability Check Logic ---
    # This logic runs *before* setting the status, effectively preventing re-loaning
    if status == "On Loan" or status == "Reserved": # Only check availability if trying to loan or reserve
        if not frappe.db.exists("Book", book_name):
            frappe.throw(f"Book '{book_name}' does not exist.")

        current_book_status = frappe.db.get_value("Book", book_name, "status")
        frappe.log_error(f"Book '{book_name}' current status from DB for API validation: {current_book_status}", "API Status Update Debug")

        if current_book_status == "On Loan":
            frappe.throw(f"Book '{book_name}' is already on loan and cannot be loaned again.")
        elif current_book_status == "Reserved" and status == "On Loan":
            if member_name: # Check if the reservation is for the current member attempting to loan
                reservations = frappe.get_all("Reservation",
                                            filters={"book": book_name, "member": member_name, "status": "Pending"},
                                            limit=1)
                if not reservations:
                    frappe.throw(f"Book '{book_name}' is reserved by another member and cannot be loaned.")
            else: # If no member_name provided for loan, and it's reserved, throw
                frappe.throw(f"Book '{book_name}' is reserved and cannot be loaned without a member context.")
        elif current_book_status == "Reserved" and status == "Reserved":
            # Allow multiple reservations (queue functionality). Logic for queue processing
            # will be outside this simple check. For now, simply allow to reserve an already
            # reserved book. You could add a check to prevent same user from reserving twice.
            pass


    # --- END US-04 Availability Check Logic ---

    # Check permissions after validation, but before DB write
    if not frappe.has_permission("Book", "write", user=frappe.session.user):
        frappe.throw("No permission to update book status via API.")

    # Perform the status update
    frappe.db.set_value("Reservation", reservations[0].name, "status", "Fulfilled")
    
    if status == "On Loan":
        frappe.db.set_value("Book", book_name, "current_borrower", member_name)
        reservations = frappe.get_all("Reservation", filters={"book": book_name, "member": member_name, "status": "Pending"}, limit=1)
        if reservations:
            frappe.db.set_value("Reservation", reservations[0].name,)