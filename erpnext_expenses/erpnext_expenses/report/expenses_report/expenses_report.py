# Copyright (c) 2025, Karani Geoffrey and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_expense_data(filters)

	if not data:
		return columns, [], None, None, []

	totals = calculate_totals(data)
	report_summary = get_report_summary(totals)
	return columns, data, None, None, report_summary


def get_columns():
	"""
	Define las columnas para el Reporte de Gastos.
	"""
	return [
		{"label": _("Compañía"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": "auto"},
		{"label": _("Fecha"), "fieldname": "expense_date", "fieldtype": "Date", "width": "auto"},
		{"label": _("Nombre del Gasto"), "fieldname": "expense_id", "fieldtype": "Link", "options": "Expense", "width": "auto"},
		{"label": _("Reporte de Gasto"), "fieldname": "expense_report", "fieldtype": "Link", "options": "Expense Report", "width": "auto"},
		{"label": _("Cuenta de Pago"), "fieldname": "paying_account", "fieldtype": "Link", "options": "Account", "width": "auto"},
		{"label": _("Asiento Contable"), "fieldname": "journal_entry", "fieldtype": "Link", "options": "Journal Entry", "width": "auto"},
		{"label": _("Categoría"), "fieldname": "expense_category", "fieldtype": "Link", "options": "Expense Category", "width": "auto"},
		{"label": _("Descripción"), "fieldname": "description", "fieldtype": "Data", "width": "auto"},
		{"label": _("Monto de Gasto"), "fieldname": "amount", "fieldtype": "Currency", "width": "auto"},
	]

def get_expense_data(filters):
	"""
	Obtiene los datos de los gastos basándose en los filtros proporcionados.
	"""
	conditions = get_conditions(filters)

	data = frappe.db.sql(f"""
		SELECT
			er.company,
			er.name as expense_report,
			er.paying_account,
			er.journal_entry,
			ed.expense_date,
			ed.expense_id,
			ed.category as expense_category,
			ed.description,
			ed.subtotal as amount
		FROM
		`tabExpense Report` er JOIN `tabExpense Detail` ed ON er.name = ed.parent
		WHERE
			er.docstatus = 1
			{conditions}
		ORDER BY
			ed.expense_date
	""", filters, as_dict=1)

	return data

def get_conditions(filters):
	"""
	Construye las condiciones SQL a partir de los filtros.
	"""
	conditions = ""
	if filters.get("company"):
		conditions += " AND er.company = %(company)s"

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND ed.expense_date BETWEEN %(from_date)s AND %(to_date)s"

	return conditions

def calculate_totals(data: list[dict]) -> dict:
	"""
	Calcula los totales para el resumen del reporte.
	"""
	if not data:
		return {}

	total_amount = sum(row.get("amount", 0) for row in data)

	return {
		"amount": total_amount,
	}

def get_report_summary(totals: dict) -> list[dict]:
	"""
	Genera el resumen para la parte superior del reporte.
	"""
	if not totals:
		return []

	return [
		{
			"value": totals.get("amount", 0),
			"label": _("Monto Total de Gastos"),
			"datatype": "Currency",
			"indicator": "Green"
		}
	]