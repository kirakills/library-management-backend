import frappe
import csv
from io import StringIO

# --- IMPORTANT: These imports must be correct and point to your report files ---
# Ensure these import paths match your actual structure (no second library_management here):
# library_management/report/books_on_loan/books_on_loan.py
# library_management/report/overdue_books/overdue_books.py
from library_management.report.books_on_loan.books_on_loan import execute as books_on_loan_execute
from library_management.report.overdue_books.overdue_books import execute as overdue_books_execute


@frappe.whitelist() # This decorator is crucial for API access
def update_book_status_after_transaction(book_name, status, member_name=None, reservation_name=None):
    """
    Custom API method to update book status after a loan or reservation.
    Includes availability check logic.
    """
    frappe.log_error(f"WORKAROUND: API Method called - Book: {book_name}, Target Status: {status}", "API Status Update Debug")

    # --- START US-04 Availability Check Logic ---
    if status == "On Loan" or status == "Reserved": # Only check availability if trying to loan or reserve
        if not frappe.db.exists("Book", book_name):
            frappe.throw(f"Book '{book_name}' does not exist.")

        current_book_status_raw = frappe.db.get_value("Book", book_name, "status")
        current_book_status = current_book_status_raw.strip() if current_book_status_raw else ""
        frappe.log_error(f"Book '{book_name}' current status from DB for API validation: '{current_book_status}'", "API Status Update Debug")

        if current_book_status == "On Loan": # Comparison with cleaned string
            frappe.throw(f"Book '{book_name}' is already on loan and cannot be loaned again.")
        elif current_book_status == "Reserved" and status == "On Loan":
            if member_name: # Check if the reservation is for the current member attempting to loan
                reservations_for_member = frappe.get_all("Reservation",
                                                        filters={"book": book_name, "member": member_name, "status": "Pending"},
                                                        limit=1)
                if not reservations_for_member:
                    frappe.throw(f"Book '{book_name}' is reserved by another member and cannot be loaned.")
            else: # If no member_name provided for loan, and it's reserved, throw
                frappe.throw(f"Book '{book_name}' is reserved and cannot be loaned without a member context.")
        elif current_book_status == "Reserved" and status == "Reserved":
            pass # Allow multiple reservations for now


    # --- END US-04 Availability Check Logic ---

    if not frappe.has_permission("Book", "write", user=frappe.session.user):
        frappe.throw("No permission to update book status via API.")

    frappe.db.set_value("Book", book_name, "status", status)
    
    if status == "On Loan":
        frappe.db.set_value("Book", book_name, "current_borrower", member_name)
        reservations_to_fulfill = []
        try:
            reservations_to_fulfill = frappe.get_all("Reservation", filters={"book": book_name, "member": member_name, "status": "Pending"}, limit=1)
            if reservations_to_fulfill:
                frappe.db.set_value("Reservation", reservations_to_fulfill[0].name, "status", "Fulfilled")
        except Exception as e:
            frappe.log_error(f"Error trying to fulfill reservation for Book '{book_name}': {e}", "API Status Update Error")

    elif status == "Reserved":
        frappe.db.set_value("Book", book_name, "current_reservation", reservation_name)
    elif status == "Available":
        frappe.db.set_value("Book", book_name, "current_borrower", None)
        frappe.db.set_value("Book", book_name, "current_reservation", None)

    frappe.db.commit()
    frappe.log_error(f"Book '{book_name}' status updated to '{status}' via API - COMMIT OK.", "API Status Update Debug")
    return {"status": "success", "book_name": book_name, "new_status": status}


@frappe.whitelist()
def create_loan_transaction(book_name, member_name, loan_date, return_date):
    """
    Creates a Loan, performs availability check, and updates book status in a single transaction.
    """
    frappe.log_error(f"API: create_loan_transaction called for Book: {book_name}, Member: {member_name}", "Loan Transaction Fired")

    # 1. Availability Check (US-04) - BEFORE creating the loan
    if not frappe.db.exists("Book", book_name):
        frappe.throw(f"Book '{book_name}' does not exist.")

    current_book_status_raw = frappe.db.get_value("Book", book_name, "status")
    current_book_status = current_book_status_raw.strip() if current_book_status_raw else ""
    frappe.log_error(f"Book '{book_name}' status for Loan transaction validation (cleaned): '{current_book_status}'", "Loan Transaction Debug")

    if current_book_status == "On Loan": # Comparison with cleaned string
        frappe.throw(f"Book '{book_name}' is already on loan and cannot be loaned again.")
    elif current_book_status == "Reserved":
        reservations_for_member = frappe.get_all("Reservation",
                                                filters={"book": book_name, "member": member_name, "status": "Pending"},
                                                limit=1)
        if not reservations_for_member:
            frappe.throw(f"Book '{book_name}' is reserved by another member and cannot be loaned.")

    # 2. Check Permissions for Loan & Book update
    if not frappe.has_permission("Loan", "create", user=frappe.session.user):
        frappe.throw("No permission to create Loan.")
    if not frappe.has_permission("Book", "write", user=frappe.session.user):
        frappe.throw("No permission to update book status.")

    # 3. Create Loan Document
    loan_doc = frappe.new_doc("Loan")
    loan_doc.book = book_name
    loan_doc.member = member_name
    loan_doc.loan_date = loan_date
    loan_doc.return_date = return_date
    loan_doc.status = "Active" # Initial status
    
    try:
        loan_doc.insert()
        loan_doc.submit()
        frappe.log_error(f"Loan '{loan_doc.name}' inserted and submitted.", "Loan Transaction Debug")
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error inserting/submitting Loan '{loan_doc.name}': {e}", "Loan Transaction Error")
        frappe.throw(f"Failed to create loan document: {e}")

    # 4. Update Book Status (US-03) and Fulfill Reservation (US-05)
    frappe.db.set_value("Book", book_name, "status", "On Loan")
    frappe.db.set_value("Book", book_name, "current_borrower", member_name)
    frappe.log_error(f"Book '{book_name}' status set to 'On Loan' and borrower '{member_name}' within transaction.", "Loan Transaction Debug")

    if current_book_status == "Reserved" and reservations_for_member:
        frappe.db.set_value("Reservation", reservations_for_member[0].name, "status", "Fulfilled")
        frappe.log_error(f"Fulfilled Reservation {reservations_for_member[0].name} for Book '{book_name}' within transaction.", "Loan Transaction Debug")

    frappe.db.commit()
    frappe.log_error(f"Loan transaction completed successfully for '{loan_doc.name}'.", "Loan Transaction Fired")
    return {"status": "success", "loan_name": loan_doc.name, "book_name": book_name, "new_book_status": "On Loan"}


@frappe.whitelist()
def create_reservation_transaction(book_name, member_name, reservation_date):
    """
    Creates a Reservation and updates book status in a single transaction.
    """
    frappe.log_error(f"API: create_reservation_transaction called for Book: {book_name}, Member: {member_name}", "Reservation Transaction Fired")

    # 1. Availability Check
    if not frappe.db.exists("Book", book_name):
        frappe.throw(f"Book '{book_name}' does not exist.")

    current_book_status_raw = frappe.db.get_value("Book", book_name, "status")
    current_book_status = current_book_status_raw.strip() if current_book_status_raw else ""
    frappe.log_error(f"Book '{book_name}' status for Reservation transaction validation (cleaned): '{current_book_status}'", "Reservation Transaction Debug")

    if current_book_status == "On Loan":
        frappe.throw(f"Book '{book_name}' is currently on loan and cannot be reserved.")
    # Optional: Add logic to prevent same user from reserving same book multiple times

    # 2. Check Permissions for Reservation & Book update
    if not frappe.has_permission("Reservation", "create", user=frappe.session.user):
        frappe.throw("No permission to create Reservation.")
    if not frappe.has_permission("Book", "write", user=frappe.session.user):
        frappe.throw("No permission to update book status.")

    # 3. Create Reservation Document
    reservation_doc = frappe.new_doc("Reservation")
    reservation_doc.book = book_name
    reservation_doc.member = member_name
    reservation_doc.reservation_date = reservation_date
    reservation_doc.status = "Pending"
    
    try:
        reservation_doc.insert()
        reservation_doc.submit()
        frappe.log_error(f"Reservation '{reservation_doc.name}' inserted and submitted.", "Reservation Transaction Debug")
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error inserting/submitting Reservation '{reservation_doc.name}': {e}", "Reservation Transaction Error")
        frappe.throw(f"Failed to create reservation document: {e}")

    # 4. Update Book Status (US-05)
    frappe.db.set_value("Book", book_name, "status", "Reserved")
    frappe.db.set_value("Book", book_name, "current_reservation", reservation_doc.name)
    frappe.log_error(f"Book '{book_name}' status set to 'Reserved' and reservation '{reservation_doc.name}' within transaction.", "Reservation Transaction Debug")

    frappe.db.commit()
    frappe.log_error(f"Reservation transaction completed successfully for '{reservation_doc.name}'.", "Reservation Transaction Fired")
    return {"status": "success", "reservation_name": reservation_doc.name, "book_name": book_name, "new_book_status": "Reserved"}


# --- Report Fetching Methods (US-07) ---
@frappe.whitelist()
def get_books_on_loan_report():
    """
    Custom API method to fetch Books On Loan report data.
    Bypasses standard Report API due to loading issues.
    """
    frappe.log_error("API: get_books_on_loan_report called", "Report API Debug")
    if not frappe.has_permission("Report", "read", user=frappe.session.user):
        frappe.throw("No permission to read Books On Loan report via API.")

    # Call the execute function from your report file directly
    columns, data = books_on_loan_execute()
    return {"columns": columns, "result": data}


@frappe.whitelist()
def get_overdue_books_report():
    """
    Custom API method to fetch Overdue Books report data.
    Bypasses standard Report API due to loading issues.
    """
    frappe.log_error("API: get_overdue_books_report called", "Report API Debug")
    if not frappe.has_permission("Report", "read", user=frappe.session.user):
        frappe.throw("No permission to read Overdue Books report via API.")

    # Call the execute function from your report file directly
    columns, data = overdue_books_execute()
    return {"columns": columns, "result": data}


# --- CSV Export Method (SS-03) ---
@frappe.whitelist()
def get_member_loan_history_csv(member_name):
    """
    Fetches a member's loan history and returns it as a CSV string.
    """
    if not member_name:
        frappe.throw("Member name is required to fetch loan history.")

    if not frappe.has_permission("Report", "read", user=frappe.session.user): # Or Loan/Member read permission
        frappe.throw("No permission to read loan history.")

    loans = frappe.db.sql("""
        SELECT
            l.name AS loan_id,
            b.title AS book_title,
            b.isbn AS book_isbn,
            l.loan_date,
            l.return_date,
            l.actual_return_date,
            l.status AS loan_status
        FROM
            `tabLoan` l
        JOIN
            `tabBook` b ON l.book = b.name
        WHERE
            l.member = %s
        ORDER BY
            l.loan_date DESC
    """, (member_name,), as_dict=1)

    if not loans:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Loan ID", "Book Title", "ISBN", "Loan Date", "Expected Return Date", "Actual Return Date", "Loan Status"])
        frappe.log_error(f"API: No loan history found for member {member_name}.", "CSV Export Debug")
        return output.getvalue()

    headers = ["Loan ID", "Book Title", "ISBN", "Loan Date", "Expected Return Date", "Actual Return Date", "Loan Status"]
    csv_data = []
    for loan in loans:
        csv_data.append([
            loan.loan_id,
            loan.book_title,
            loan.book_isbn,
            str(loan.loan_date), # Convert date objects to strings
            str(loan.return_date),
            str(loan.actual_return_date) if loan.actual_return_date else '', # Handle None for actual_return_date
            loan.loan_status
        ])

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(csv_data)

    frappe.log_error(f"API: Exported loan history for member {member_name}.", "CSV Export Debug")
    return output.getvalue()