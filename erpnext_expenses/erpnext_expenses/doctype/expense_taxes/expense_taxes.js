// Copyright (c) 2024, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Taxes", {
	refresh: function(frm) {
        frm.set_query('tax_account', function() {
            return {
                filters: [
                    ['Account', 'account_type', '=', 'Tax']
                ]
            };
        });
    }
});


