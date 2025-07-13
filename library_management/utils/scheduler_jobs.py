import frappe
from frappe.utils import nowdate, add_days

def send_overdue_reminders():
    # Get all active loans where return_date is in the past
    overdue_loans = frappe.get_all("Loan",
                                   filters={
                                       "status": "Active",
                                       "return_date": ["<", nowdate()]
                                   },
                                   fields=["name", "book", "member", "return_date"])

    if not overdue_loans:
        frappe.msgprint("No overdue loans found.")
        return

    frappe.msgprint(f"Checking {len(overdue_loans)} overdue loans...")

    for loan in overdue_loans:
        member_email = frappe.db.get_value("Member", loan.member, "email")
        book_title = frappe.db.get_value("Book", loan.book, "title")

        if member_email and book_title:
            subject = f"Overdue Book Reminder: '{book_title}'"
            message = f"""
            Dear {loan.member},

            This is a reminder that the book "{book_title}" (Loan ID: {loan.name})
            was due on {loan.return_date} and is now overdue.

            Please return the book as soon as possible.

            Thank you,
            Your Library Management System
            """
            frappe.sendmail(
                recipients=member_email,
                subject=subject,
                message=message,
                now=True # Send immediately
            )
            frappe.log_error(f"Sent overdue reminder for Loan: {loan.name} to {member_email}", "Overdue Reminder Sent")
        else:
            frappe.log_error(f"Could not send reminder for Loan: {loan.name}. Missing member email or book title.", "Overdue Reminder Failed")

    frappe.msgprint("Overdue reminder process completed.")
