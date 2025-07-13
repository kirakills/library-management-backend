import frappe
from frappe.utils import nowdate

@frappe.whitelist()
def execute(filters=None):
    # Define report columns
    columns = [
        {"fieldname": "loan_id", "label": "Loan ID", "fieldtype": "Link", "options": "Loan", "width": 100},
        {"fieldname": "book_title", "label": "Book Title", "fieldtype": "Data", "width": 200},
        {"fieldname": "book_isbn", "label": "ISBN", "fieldtype": "Data", "width": 150},
        {"fieldname": "member_name", "label": "Member Name", "fieldtype": "Data", "width": 200},
        {"fieldname": "member_id", "label": "Membership ID", "fieldtype": "Data", "width": 150},
        {"fieldname": "loan_date", "label": "Loan Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "return_date", "label": "Expected Return Date", "fieldtype": "Date", "width": 150},
        {"fieldname": "days_overdue", "label": "Days Overdue", "fieldtype": "Int", "width": 100},
        {"fieldname": "book_status", "label": "Book Status (at time of report)", "fieldtype": "Data", "width": 200}
    ]

    # Query for overdue loans
    loans = frappe.db.sql(f"""
        SELECT
            l.name AS loan_id,
            b.title AS book_title,
            b.isbn AS book_isbn,
            m.title AS member_name,
            m.membership_id AS member_id,
            l.loan_date,
            l.return_date,
            DATEDIFF('{nowdate()}', l.return_date) AS days_overdue,
            b.status AS book_status
        FROM
            `tabLoan` l
        JOIN
            `tabBook` b ON l.book = b.name
        JOIN
            `tabMember` m ON l.member = m.name
        WHERE
            l.status = 'Active' AND l.return_date < '{nowdate()}'
        ORDER BY
            l.return_date ASC
    """, as_dict=1)

    data = []
    for loan in loans:
        data.append(loan)

    return columns, data
