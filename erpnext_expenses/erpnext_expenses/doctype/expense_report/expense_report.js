// Copyright (c) 2024, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Report", {
  refresh(frm) {
    if (
      frm.doc.workflow_state == "Approved" &&
      frappe.user.has_role("Accounts User")
    ) {
      frm.add_custom_button(__("Create Journal Entries"), function () {
        if (!frm.doc.paying_account) {
          frappe.throw("Debe seleccionar una Cuenta de Pago");
        } else {
          frappe.dom.freeze("Generando Asientos Contables...");
          frappe.call({
            method:
              "erpnext_expenses.erpnext_expenses.doctype.expense_report.expense_report.create_journal_entries",
            args: {
              report: frm.doc.name,
            },
            callback: function (r) {
              frappe.dom.unfreeze();
              if (!r.exc) {
                frappe.show_alert(
                  {
                    message: "Asiento Contable creado exitosamente",
                    indicator: "green",
                  },
                  5
                );
                frm.reload_doc();
              }
            },
            error: function (r) {
              frappe.dom.unfreeze();
              frappe.msgprint({
                title: "Error",
                indicator: "red",
                message:
                  "Ocurrió un error al crear el Asiento Contable. Por favor revise el log de errores.",
              });
            },
          });
        }
      });
    }
  },

  after_workflow_action: function (frm) {
    if (frm.doc.workflow_state == "Journals Created") {
      frappe.dom.freeze("Generando Asientos Contables...");
      frappe.call({
        method:
          "erpnext_expenses.erpnext_expenses.doctype.expense_report.expense_report.create_journal_entries",
        args: {
          report: frm.doc.name,
        },
        callback: function (r) {
          frappe.dom.unfreeze();
          if (!r.exc) {
            frappe.show_alert(
              {
                message: "Asiento Contable creado exitosamente",
                indicator: "green",
              },
              5
            );
            frm.reload_doc();
          }
        },
        error: function (r) {
          frappe.dom.unfreeze();
          frappe.msgprint({
            title: "Error",
            indicator: "red",
            message:
              "Ocurrió un error al crear el Asiento Contable. Por favor revise el log de errores.",
          });
        },
      });
    }
  },
});
