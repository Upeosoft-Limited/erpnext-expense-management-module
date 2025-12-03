# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class ExpenseReport(Document):
    def validate(self):
        """
        Valida que los gastos en el reporte no estén ya incluidos en otro
        reporte de gastos activo.
        """
        for detail in self.get("expense"):
            if not detail.expense_id:
                continue


            existing_report = frappe.db.get_value(
                "Expense Detail",
                filters={
                    "expense_id": detail.expense_id,
                    "parent": ["!=", self.name],
                    "docstatus": ["!=", 2],
                },
                fieldname="parent"
            )

            if existing_report:
                frappe.throw(f"El gasto <b>{detail.expense_id}</b> "
                             f"ya está incluido en el Reporte de Gastos <b>{existing_report}</b>.")


    def on_cancel(self) -> None:
        """Cancela el Asiento Contable asociado cuando se cancela el Reporte de Gastos"""
        # Si existe un Journal Entry vinculado, cancelarlo
        # Usar get() para compatibilidad con documentos antiguos
        journal_entry = self.get("journal_entry")
        if journal_entry:
            try:
                je_doc = frappe.get_doc('Journal Entry', journal_entry)
                if je_doc.docstatus == 1:  # Solo si está enviado
                    # Ignorar validación de links para evitar dependencia circular
                    je_doc.flags.ignore_links = True
                    je_doc.cancel()
                    frappe.msgprint(f"El Asiento Contable {journal_entry} ha sido cancelado")
            except Exception as e:
                frappe.log_error(f"Error cancelando Asiento Contable {journal_entry}: {str(e)}")
                frappe.throw(f"No se pudo cancelar el Asiento Contable {journal_entry}. Por favor cancélelo manualmente.")
        self.journal_entry = None
        frappe.db.set_value(self.doctype, self.name, "journal_entry", None, update_modified=False)


@frappe.whitelist()
def create_journal_entries(report: str) -> Dict[str, Any]:
    """
    Crea los asientos contables (Journal Entry) para un Expense Report aprobado

    Args:
        report (str): Nombre del Expense Report
    """
    jv = None
    try:
        expense_report = _get_expense_report_data(report)

        if not expense_report.paying_account:
            frappe.throw("Debe seleccionar una Cuenta de Pago antes de crear los asientos contables")

        expense_total = _calculate_expense_total(report)

        if expense_total <= 0:
            frappe.throw("El total de gastos debe ser mayor a cero")

        expense_accounts = _get_expense_accounts(report)

        if not expense_accounts:
            frappe.throw("No se encontraron cuentas de gasto. Verifique que los gastos tengan categorías asignadas.")

        jv = _create_journal_entry_doc(expense_report, report, expense_total)

        _add_expense_account_entries(jv, expense_accounts)

        jv.save()
        jv.submit()

        _update_expense_report(report, jv.name)

        return {"success": True, "journal_entry": jv.name}

    except Exception as e:
        if jv and jv.name and frappe.db.exists("Journal Entry", jv.name):
            try:
                frappe.delete_doc("Journal Entry", jv.name, force=True)
            except:
                pass

        frappe.log_error(
            f"Ocurrió un error al crear los asientos contables: {str(e)}",
            "Expense Report - Create Journal Entry Error"
        )
        frappe.throw(f"Error al crear el Asiento Contable: {str(e)}")


def _get_expense_report_data(report: str) -> Dict[str, Any]:
    """Obtiene los datos básicos del Expense Report"""
    fields = ['company', 'paying_account']
    return frappe.db.get_all(
        'Expense Report',
        filters={'name': report},
        fields=fields
    )[0]





def _calculate_expense_total(report: str) -> float:
    """Calcula el total de gastos del reporte"""
    expenses = frappe.db.get_all(
        'Expense Detail',
        filters={'parent': report},
        fields=['expense_id', 'subtotal', 'description']
    )

    return sum(item.subtotal for item in expenses)


def _get_expense_accounts(report: str) -> List[Dict[str, Any]]:
    """Obtiene las cuentas de gasto por categoría"""
    sql = f"""
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
    return frappe.db.sql(sql, as_dict=True)


def _create_journal_entry_doc(expense_report: Dict[str, Any], report_name: str,
                               expense_total: float) -> Document:
    """Crea el documento Journal Entry con datos básicos"""
    jv = frappe.new_doc('Journal Entry')
    jv.voucher_type = 'Journal Entry'
    jv.naming_series = 'ACC-JV-.YYYY.-'
    jv.posting_date = nowdate()
    jv.company = expense_report.company
    jv.remark = f"Expense Report: {report_name}"

    # Entrada al lado del Crédito (cuenta pagadora)
    jv.append('accounts', {
        'account': expense_report.paying_account,
        'credit': float(expense_total),
        'debit': float(0),
        'debit_in_account_currency': float(0),
        'credit_in_account_currency': float(expense_total),
    })

    return jv


def _add_expense_account_entries(jv: Document, expense_accounts: List[Dict[str, Any]]) -> None:
    """Agrega las entradas de débito para cada cuenta de gasto"""
    for acc in expense_accounts:
        if not acc.expense_account:
            frappe.throw(
                f"Una de las categorías de gasto no tiene una cuenta asignada. "
                f"Por favor configure las cuentas en las Categorías de Gasto."
            )

        jv.append('accounts', {
            'account': acc.expense_account,
            'debit': float(acc.subtotal),
            'credit': float(0),
            'credit_in_account_currency': float(0),
            'debit_in_account_currency': float(acc.subtotal)
        })





def _update_expense_report(report_name: str, journal_entry_name: str) -> None:
    """Actualiza el Expense Report con la referencia al Journal Entry"""
    doc = frappe.get_doc('Expense Report', report_name)
    doc.journal_entry = journal_entry_name
    doc.workflow_state = 'Journals Created'
    doc.save()


@frappe.whitelist()
def get_account_from_mode_of_payment(mode_of_payment: str, company: str) -> Optional[str]:
    """
    Obtiene la cuenta por defecto de un Modo de Pago para una compañía específica.
    Esta función se ejecuta con permisos de administrador para leer el DocType hijo.
    """
    if not mode_of_payment or not company:
        return None

    account = frappe.db.get_value(
        "Mode of Payment Account",
        filters={
            "parent": mode_of_payment,
            "company": company,
        },
        fieldname="default_account",
        ignore=True
    )
    return account
