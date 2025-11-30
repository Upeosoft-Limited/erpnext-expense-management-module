// Copyright (c) 2024, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Report", {
  refresh(frm) {
    const is_account_user = frappe.user.has_role("Accounts User");
    const state = frm.doc.workflow_state;
    const fields = ["paying_account", "mode_of_payment"];

    const set_field_state = (show, read_only) => {
      fields.forEach(field => {
        frm.toggle_display(field, show);
        if (show) {
          frm.set_df_property(field, "read_only", read_only);
        }
      });
    };

    if (is_account_user) {
      if (state === "Approved") {
        set_field_state(true, 0); 
      } else if (state === "Journals Created") {
        set_field_state(true, 1);
      } else {
        set_field_state(false); 
      }
    } else {
      set_field_state(true, 1);
    }

    if (frm.is_new() || frm.doc.workflow_state === "Draft") {
      frm.set_df_property("company", "read_only", 0);
      frm.set_df_property("paid_by", "read_only", 0);
    } else {
      frm.set_df_property("company", "read_only", 1);
      frm.set_df_property("paid_by", "read_only", 1);
    }
    frm.set_query("paying_account", function () {
      return {
        filters: {
          company: frm.doc.company,
        },
      };
    });

    frm.set_query("expense_id", "expense", function (doc) {
      return {
        filters: {
          company: doc.company,
          docstatus: 1,
        },
      };
    });

    if (
      (frm.doc.workflow_state === "Approved" || frm.doc.workflow_state === "Journals Created") &&
      frappe.user.has_role("Accounts User") &&
      !frm.doc.journal_entry
    ) {
      frm.add_custom_button(__("Create Journal Entries"), function () {
        if (!frm.doc.paying_account || !frm.doc.mode_of_payment) {
          frappe.msgprint({
            title: __("Campos Requeridos"),
            message: __(
              "Por favor, seleccione un <b>Modo de Pago</b> y una <b>Cuenta de Pago</b> antes de continuar."
            ),
            indicator: "orange",
          });
          return; 
        }
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
                frappe.show_alert({ message: "Asiento Contable creado exitosamente", indicator: "green",}, 5);
                frm.reload_doc();
              }
            },
            error: function (r) {
              frappe.dom.unfreeze();
              frappe.msgprint({ title: "Error", indicator: "red", message: "Ocurrió un error al crear el Asiento Contable. Por favor revise el log de errores.",});
            },
          });
      });
    }
  },

  after_workflow_action: function (frm) {
    if (frm.doc.workflow_state == "Journals Created") {
      if (!frm.doc.paying_account || !frm.doc.mode_of_payment) {
        frappe.msgprint({
          title: __("Campos Requeridos"),
          message: __(
            "Por favor, seleccione un <b>Modo de Pago</b> y una <b>Cuenta de Pago</b>."
          ),
          indicator: "red",
        });
        frm.doc.workflow_state = "Approved";
        frm.save();
        return;
      }

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

  mode_of_payment: function (frm) {
    if (frm.doc.mode_of_payment) {
      if (!frm.doc.company) {
        frm.set_value("mode_of_payment", "");
        frappe.throw(
          __("Por favor, seleccione una <b>Compañía</b> primero.")
        );
        return;
      }

      frappe.call({
        method: "erpnext_expenses.erpnext_expenses.doctype.expense_report.expense_report.get_account_from_mode_of_payment",
        args: {
          mode_of_payment: frm.doc.mode_of_payment,
          company: frm.doc.company,
        },
        callback: function (r) {
          if (r.message) {
            frm.set_value("paying_account", r.message);
          }
        },
      });
    }
  },
  company: function (frm) {
    if (frm.doc.expense && frm.doc.expense.length > 0) {
      frm.clear_table("expense");
    }
    frm.refresh_field("expense");
  },
});

frappe.ui.form.on("Expense Detail", {
  expense_id: function (frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.expense_id) {
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Expense",
          name: row.expense_id,
        },
        callback: function (r) {
          if (r.message) {
            const expense_doc = r.message;
            frappe.model.set_value(
              cdt,
              cdn,
              "expense_date",
              expense_doc.expense_date
            );
            frappe.model.set_value(cdt, cdn, "category", expense_doc.category);
            frappe.model.set_value(cdt, cdn, "subtotal", expense_doc.total);
            frappe.model.set_value(cdt, cdn,"description", expense_doc.expense_description );
          }
        },
      });
    }
  },
});
