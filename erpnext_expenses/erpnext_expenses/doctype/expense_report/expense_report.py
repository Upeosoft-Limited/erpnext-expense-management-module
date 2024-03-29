# Copyright (c) 2024, Karani Geoffrey and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class ExpenseReport(Document):
    pass


@frappe.whitelist()
def create_journal_entries(report):
    try:
        fields = [
            'company',
            'paying_account'
        ]

        expense_report = frappe.db.get_all('Expense Report', filters={'name': report}, fields=fields)[0]


        # Get the associated expense value from the expenses child table
        expense = frappe.db.get_all('Expense Detail', filters={'parent': report}, fields=['expense_id', 'subtotal', 'description'])

        expense_total = 0
        for item in expense:
            expense_total = expense_total + item.subtotal


        # Create the journal entries
        jv = frappe.new_doc('Journal Entry')
        jv.voucher_type = 'Journal Entry'
        jv.naming_series = 'ACC-JV-.YYYY.-'
        jv.posting_date = nowdate()
        jv.company = expense_report.company
        jv.remark = expense_report.description

        #Entry to the Credit Side
        jv.append('accounts', {
            'account': expense_report.paying_account,
            'credit' : float(expense_total),
            'debit' : float(0),
            'debit_in_account_currency' : float(0),
            'credit_in_account_currency' : float(expense_total),
        })


        # Get the account associated with the expense category
        expense_account_sql = f"""
            SELECT
                ec.expense_account,
                ed.subtotal
            FROM 
                `tabExpense Category` ec
            JOIN 
                `tabExpense` e 
            ON 
                ec.name = e.category
            JOIN 
                `tabExpense Detail` ed 
            ON 
                e.name = ed.expense_id
            WHERE 
                ed.parent = '{report}';
        """

        expense_account = frappe.db.sql(expense_account_sql, as_dict=True)
        

        for acc in expense_account:
            #Entry to the Debit Side
            jv.append('accounts', {
                'account': acc.expense_account,
                'debit' : float(acc.subtotal),
                'credit' : float(0),
                'credit_in_account_currency': float(0),
                'debit_in_account_currency': float(acc.subtotal)
            })

        jv.save()
        jv.submit()

        # Change the workflow state of the Expense Report to Submitted
        doc = frappe.get_doc('Expense Report', report)
        doc.workflow_state = 'Journals Created'
        doc.save()
        frappe.db.commit()

    except Exception as e:
        # Log the error to the Frappe error log document
        frappe.log_error(f"An error occurred: {str(e)}")