# Copyright (c) 2024, Karani Geoffrey and contributors
# For license information, please see license.txt

from typing import Optional, Dict, List, Any
import frappe
from frappe.model.document import Document
import json


class Expense(Document):
    pass


@frappe.whitelist()
def get_logged_in_employee() -> Optional[Dict[str, str]]:
    try:
        user = frappe.session.user

        employee, employee_name = frappe.db.get_value(
            'Employee',
            {'user_id': user},
            ['name', 'employee_name']
        )

        context = {
            'employee': employee,
            'employee_name': employee_name
        }

        return context

    except Exception as e:
        return None


@frappe.whitelist()
def create_expense_report(
    expense: str,
    details: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Crea un Expense Report desde uno o varios Expenses

    Args:
        expense (str): ID del Expense principal
        details (list, optional): Lista de detalles de gastos adicionales

    Returns:
        dict: {'response': 'Success'/'Error', 'expense': report_name}
    """
    report = None
    try:
        _validate_expense_not_in_active_report(expense)

        expense_data = _get_expense_data(expense)

        report = _create_expense_report_doc(expense_data)

        if details:
            for detail in details:
                _add_expense_detail(
                    report,
                    detail['expense_id'],
                    detail['expense_date'],
                    detail['category'],
                    detail['description'],
                    detail['subtotal'],
                    detail['total_exchange'],
                    detail['spending_currency'],
                    detail['exchange_rate'],
                    detail.get('reference_no')
                )
                _mark_expense_as_submitted(detail['expense_id'])
        else:
            _add_expense_detail(
                report,
                expense,
                expense_data.expense_date,
                expense_data.category,
                expense_data.expense_description,
                expense_data.total,
               expense_data.total_exchange,
               expense_data.spending_currency,
               expense_data.exchange_rate,
               expense_data.reference_no
            )
            _mark_expense_as_submitted(expense)

        return {
            'response': 'Success',
            'expense': report.name
        }

    except Exception as e:
        frappe.log_error(
            title="Error al crear el reporte de gastos",
            message=f"Ocurrió un error: {str(e)}"
        )

        if report and report.name:
            frappe.delete_doc('Expense Report', report.name)

        return {'response': 'Error'}


def _validate_expense_not_in_active_report(expense: str) -> None:
    """Valida que el Expense no esté ya en un Expense Report activo"""
    expense_details = frappe.db.get_all(
        'Expense Detail',
        filters={'expense_id': expense},
        fields=['parent'],
        pluck='parent'
    )

    if expense_details:
        for report_name in expense_details:
            report = frappe.get_doc('Expense Report', report_name)

            if report.docstatus != 2:
                frappe.throw(
                    f"Este gasto ya está incluido en el Reporte de Gastos <b>{report_name}</b>. "
                    f"Cancele ese reporte primero si desea crear uno nuevo.",
                    title="Gasto Ya Reportado"
                )


def _get_expense_data(expense: str) -> Dict[str, Any]:
    """Obtiene los datos del Expense"""
    fields = [
        'expense_description',
        'category',
        'total',
        'employee',
        'expense_date',
        'company',
        'total_exchange',
        'spending_currency',
        'exchange_rate',
        'paid_by',
        'reference_no'
    ]
    return frappe.db.get_all(
        'Expense',
        filters={'name': expense},
        fields=fields
    )[0]


def _create_expense_report_doc(expense_data: Dict[str, Any]) -> Document:
    """Crea el documento Expense Report"""
    report = frappe.get_doc({
        'doctype': 'Expense Report',
        'employee': expense_data.employee,
        'paid_by': expense_data.paid_by,
        'company': expense_data.company,
    })
    report.insert()
    return report


def _add_expense_detail(
        report: Document,
    expense_id: str,
    expense_date: str,
    category: str,
    description: str,
    subtotal: float,
    total_exchange: float,
    spending_currency: str,
    exchange_rate: float,
    reference_no: Optional[str] = None
) -> None:

    """Agrega un Expense Detail al reporte"""
    report_detail = frappe.get_doc({
        'doctype': 'Expense Detail',
        'parent': report.name,
        'parentfield': 'expense',
        'parenttype': 'Expense Report',
        'expense_id': expense_id,
        'expense_date': expense_date,
        'category': category,
        'description': description,
        'subtotal': subtotal,
        'total': total_exchange,
        'currency_reference': spending_currency,
        'exchange_rate': exchange_rate,
        'reference_no': reference_no
    })
    report_detail.insert()


def _mark_expense_as_submitted(expense_id: str) -> None:
    """Marca el Expense como Submitted"""
    doc = frappe.get_doc('Expense', expense_id)
    doc.workflow_state = 'Submitted'
    doc.save()
    frappe.db.commit()


@frappe.whitelist()
def create_bulk_expense_report(selected: str) -> Dict[str, str]:
    json_list = json.loads(selected)

    if not json_list:
        frappe.throw("No se seleccionaron gastos para crear el reporte")

    details = []
    first_expense_id = json_list[0]['name']

    for expense in json_list:
        details.append({
            'expense_id': expense['name'],
            'expense_date': expense['expense_date'],
            'category': expense['category'],
            'description': expense['expense_description'],
            'subtotal': expense['total'],
            'total_exchange': expense['total_exchange'],
            'spending_currency': expense['spending_currency'],
            'reference_no': expense.get('reference_no')
        })

    return create_expense_report(first_expense_id, details)


@frappe.whitelist()
def get_exchange_rate(from_currency: str, to_currency: str, date: str) -> Optional[float]:
    """
    Busca la tasa de cambio más relevante para la moneda del gasto.

    """
    if not all([from_currency, to_currency, date]):
        return None

    exact_rate = frappe.db.get_value(
        "Currency Exchange",
        {"from_currency": from_currency, "to_currency": to_currency, "date": date},
        "exchange_rate",
    )
    if exact_rate:
        return exact_rate

    future_rate = frappe.db.get_value(
        "Currency Exchange",
        {"from_currency": from_currency, "to_currency": to_currency, "date": (">", date)},
        "exchange_rate",
        order_by="date asc",
    )
    if future_rate:
        return future_rate

    return frappe.db.get_value(
        "Currency Exchange",
        {"from_currency": from_currency, "to_currency": to_currency, "date": ("<", date)},
        "exchange_rate",
        order_by="date desc",
    )
