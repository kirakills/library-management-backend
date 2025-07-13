import frappe

@frappe.whitelist() # <--- THIS LINE IS CRUCIAL! ADD IT HERE.
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
        {"fieldname": "book_status", "label": "Book Status (at time of report)", "fieldtype": "Data", "width": 200}
    ]

    # Query for active loans
    loans = frappe.db.sql("""
        SELECT
            l.name AS loan_id,
            b.title AS book_title,
            b.isbn AS book_isbn,
            m.title AS member_name,
            m.membership_id AS member_id,
            l.loan_date,
            l.return_date,
            b.status AS book_status
        FROM
            `tabLoan` l
        JOIN
            `tabBook` b ON l.book = b.name
        JOIN
            `tabMember` m ON l.member = m.name
        WHERE
            l.status = 'Active'
        ORDER BY
            l.loan_date DESC
    """, as_dict=1)

    data = []
    for loan in loans:
        data.append(loan)

    # Return columns and data
    return columns, data