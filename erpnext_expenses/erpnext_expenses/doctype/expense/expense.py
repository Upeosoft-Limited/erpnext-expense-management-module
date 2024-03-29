# Copyright (c) 2024, Karani Geoffrey and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class Expense(Document):
	pass



@frappe.whitelist()
def get_logged_in_employee():
	try:
		# Get the logged in user
		user = frappe.session.user

		# Get the employee based on the logged in user
		employee, employee_name = frappe.db.get_value('Employee', {'user_id': user}, ['name', 'employee_name'])

		# Build a context dictionary for the results
		context = {
			'employee': employee,
			'employee_name': employee_name
		}

		# Return the context dictionary
		return context

	except Exception as e:
		# Return None if the logged user does not have an associated employee
		return None
	

@frappe.whitelist()
def create_expense_report(expense, details=None):
	try:
		fields = [
			'expense_description',
			'category',
			'total',
			'employee',
			'expense_date',
			'company',
			'paid_by'
		]

		# Get the data from the Expense doctype
		expense_data = frappe.db.get_all('Expense', filters={'name': expense}, fields=fields)[0]

		# Create a record in the Expense report doctype
		report = frappe.get_doc({
			'doctype': 'Expense Report',
			'employee': expense_data.employee,
			'paid_by': expense_data.paid_by,
			'company': expense_data.company,
		})

		if report.insert():

			if details:
				for detail in details:
					report_detail = frappe.get_doc({
						'doctype': 'Expense Detail',
						'parent': report.name,
						'parentfield': 'expense',
						'parenttype': 'Expense Report',
						'expense_id': detail['expense_id'],
						'expense_date': detail['expense_date'],
						'category': detail['category'],
						'description': detail['description'],
						'subtotal': detail['subtotal']
					})
					
					report_detail.insert()
					frappe.db.commit()

					# Change the workflow state of the Expense to Submitted
					doc = frappe.get_doc('Expense', detail['expense_id'])
					doc.workflow_state = 'Submitted'
					doc.save()
					frappe.db.commit()

			else:
				report_detail = frappe.get_doc({
					'doctype': 'Expense Detail',
					'parent': report.name,
					'parentfield': 'expense',
					'parenttype': 'Expense Report',
					'expense_id': expense,
					'expense_date': expense_data.expense_date,
					'category': expense_data.category,
					'description': expense_data.expense_description,
					'subtotal': expense_data.total
				})
				report_detail.insert()

				# Change the workflow state of the Expense to Submitted
				doc = frappe.get_doc('Expense', expense)
				doc.workflow_state = 'Submitted'
				doc.save()
				frappe.db.commit()

				# Create the context dictionary

			context = {
				'response': 'Success',
				'expense': report.name
			}

	except Exception as e:
		# Log the error to the Frappe error log document
		frappe.log_error(f"An error occurred: {str(e)}")
		frappe.delete_doc('Expense Report', report.name)

		context = {
			'response': 'Error',
		}

	# Export the context ductionary
	return context


@frappe.whitelist()
def create_bulk_expense_report(selected):
	# Parse the JSON array into a Python list of dictionaries
	json_list = json.loads(selected)

	# Loop over the list and print each dictionary
	details = []

	for expense in json_list:
		details.append({
			'expense_id': expense['name'],
			'expense_date': expense['expense_date'],
			'category': expense['category'],
			'description': expense['expense_description'],
			'subtotal': expense['total']
		})

	# Pass the information for processing
	create_expense_report(expense['name'], details)