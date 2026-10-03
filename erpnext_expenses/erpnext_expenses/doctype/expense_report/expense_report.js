// Copyright (c) 2024, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Report", {
  after_workflow_action: function (frm) {
    if (frm.selected_workflow_action == "Create Journal Entries") {
      frappe.call({
        method:
          "erpnext_expenses.erpnext_expenses.doctype.expense_report.expense_report.create_journal_entries",
        args: {
          report: frm.doc.name,
        },
        callback: function () { frm.reload_doc(); },
      });
    }
  },
});
