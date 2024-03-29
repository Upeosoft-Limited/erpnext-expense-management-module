// Copyright (c) 2024, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Report", {
	refresh(frm) {
        if( (frm.doc.workflow_state == 'Approved') && (frappe.user.has_role('Accounts User')) ){
            frm.add_custom_button(__('Create Journal Entries'), function(){

                if(!frm.doc.paying_account){
                    frappe.throw("Please provide the paying account!")
                }else{
                    frappe.call({
                        method: 'erpnext_expenses.erpnext_expenses.doctype.expense_report.expense_report.create_journal_entries',
                        args: {
                            'report': frm.doc.name
                        },
                        callback: function(r) {
                            console.log(r.message);
                        }
                    });
                }

            });
        }

	},


    after_workflow_action: function (frm) {
        if(frm.doc.workflow_state == 'Journals Created'){
            frappe.call({
                method: 'erpnext_expenses.erpnext_expenses.doctype.expense_report.expense_report.create_journal_entries',
                args: {
                    'report': frm.doc.name
                },
                callback: function(r) {
                    console.log(r.message);
                }
            });
        }
        
    }


});
