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

        # Get all the expense IDs for the expenses in the report
        report_expenses = frappe.db.get_all('Expense Detail', filters={'parent': report}, fields=['expense_id'])

        # Dictionary to store tax amounts for each tax type
        tax_amounts = {}

        # Iterate through each expense to calculate tax amounts
        for report_expense in report_expenses:
            expense_vat = frappe.db.get_all('Expense Splitting Detail', filters={'parent': report_expense.expense_id}, fields=['vat', 'vat_amount'])

            for tax_exists in expense_vat:
                if tax_exists.vat_amount > 0:
                    # Get the tax account associated with the tax found
                    tax_account = frappe.db.get_value('Expense Taxes', tax_exists.vat, ['tax_account'])

                    # Add tax amount to the corresponding tax type in the dictionary
                    if tax_account not in tax_amounts:
                        tax_amounts[tax_account] = 0
                    tax_amounts[tax_account] += tax_exists.vat_amount

        # Get the associated expense value from the expenses child table
        expense = frappe.db.get_all('Expense Detail', filters={'parent': report}, fields=['expense_id', 'subtotal', 'description'])

        expense_total = 0
        for item in expense:
            expense_total += item.subtotal

        # Create the journal entries
        jv = frappe.new_doc('Journal Entry')
        jv.voucher_type = 'Journal Entry'
        jv.naming_series = 'ACC-JV-.YYYY.-'
        jv.posting_date = nowdate()
        jv.company = expense_report.company
        jv.remark = expense_report.description

        # Entry to the Credit Side
        jv.append('accounts', {
            'account': expense_report.paying_account,
            'credit': float(expense_total),
            'debit': float(0),
            'debit_in_account_currency': float(0),
            'credit_in_account_currency': float(expense_total),
        })

        # Entry to the Debit Side for each expense category
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
            amount_less_tax = acc.subtotal - sum(tax_amounts.values())
            # Entry to the Debit Side
            jv.append('accounts', {
                'account': acc.expense_account,
                'debit': float(amount_less_tax),
                'credit': float(0),
                'credit_in_account_currency': float(0),
                'debit_in_account_currency': float(amount_less_tax)
            })

        # Entry to the tax accounts
        for tax_account, tax_amount in tax_amounts.items():
            jv.append('accounts', {
                'account': tax_account,
                'debit': float(tax_amount),
                'credit': float(0),
                'credit_in_account_currency': float(0),
                'debit_in_account_currency': float(tax_amount)
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
