import frappe

def before_loan_save(doc, method):
    # This hook is intended for availability check, but its primary function is now in api.py
    frappe.log_error(f"before_loan_save hook for Loan '{doc.name}' triggered. Status: {doc.status}", "Loan Hook Fired (from original location)")

def on_loan_submit(doc, method):
    # This hook is intended for status update, but its primary function is now in api.py
    frappe.log_error(f"on_loan_submit hook for Loan '{doc.name}' triggered.", "Loan Hook Fired (from original location)")

def on_loan_cancel_or_return(doc, method):
    # This hook is intended for status update, but its primary function is now in api.py
    frappe.log_error(f"on_loan_cancel_or_return hook for Loan '{doc.name}' triggered. Status: {doc.status}", "Loan Hook Fired (from original location)")