frappe.ui.form.on('Petty Cash Voucher', {
    refresh: function(frm) {
        frm.events.calculate_total(frm);
    },
    petty_cash_details_on_form_rendered: function(frm, cdt, cdn) {
        frappe.model.on(cdt, cdn, 'debit', function() {
            frm.events.calculate_total(frm);
        });
    },
    petty_cash_details_add: function(frm) {
        frm.events.calculate_total(frm);
    },
    petty_cash_details_remove: function(frm) {
        frm.events.calculate_total(frm);
    },
    calculate_total: function(frm) {
        let total = 0;
        frm.doc.petty_cash_details.forEach(row => {
            total += flt(row.debit);
        });
        frm.set_value('total', total);
    }
});
