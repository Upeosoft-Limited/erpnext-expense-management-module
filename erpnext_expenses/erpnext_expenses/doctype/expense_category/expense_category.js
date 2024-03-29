// Copyright (c) 2024, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Category", {
	refresh(frm) {
        frm.set_query('expense_account', function() {
            return {
                filters: {
                    root_type: 'Expense'
                }
            };
        });
	},
});
