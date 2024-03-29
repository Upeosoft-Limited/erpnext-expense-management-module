// Copyright (c) 2024, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense", {
	refresh: function(frm) {
        // Check if the workflow state is "pending_finance_approval"
        if (frm.doc.workflow_state === 'pending_finance_approval') {
            // Show the paying_account field
            frm.toggle_display('paying_account', true);
        } else {
            // Hide the paying_account field
            frm.toggle_display('paying_account', false);
        }


        if(frm.doc.workflow_state == 'Draft'){
            frm.add_custom_button(__('Create Report'), function(){
                frappe.call({
                    method: 'erpnext_expenses.erpnext_expenses.doctype.expense.expense.create_expense_report',
                    args: {
                        'expense': frm.doc.name
                    },
                    callback: function(r) {
                        if(r.message.response == 'Success'){

                            frappe.set_route("Form", "Expense Report", r.message.expense);

                        }else{
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: __('Sorry, an error was encountered. Please see the error logs for details.')
                            });
                        }
                    }
                });
            });
        }

    },

    onload: function(frm) {
        if (frm.is_new()) {
            frappe.call({
                method: 'erpnext_expenses.erpnext_expenses.doctype.expense.expense.get_logged_in_employee',
                callback: function(response) {
                    if (response.message) {
                        frm.set_value('employee', response.message.employee);
                        frm.set_value('employee_name', response.message.employee_name);
                    }
                }
            });
        }

    },

    validate: function(frm) {
        total_expense_amount = frm.doc.total;
        calculateTotalAmount(frm, total_expense_amount);
    },

    table_jkwj_add: function(frm){
        var total = 0;
        frm.doc.amount.forEach(function(row) {
            total += row.amount || 0;

            console.log(total)
        });
    }

});


// get the total in real time as it is added to the splitting child table


frappe.ui.form.on("Expense Splitting Detail", "amount", function(frm, cdt, cdn) {

    let split_total = 0;

    frm.doc.table_jkwj.forEach(function(item) {
        split_total += item.amount;
    });

    frm.set_value('split_total', split_total);

});


// Function to calculate total amount in the child table
function calculateTotalAmount(frm, total_expense_amount) {
    // Initialize total variable
    let total_amount = 0;
    let hasValue = false;

    // Loop through each row in the child table
    frm.doc.table_jkwj.forEach(function(item) {
        if(item.amount) {
            hasValue = true;

            // Sum up the amount field of each row
            total_amount += item.amount;
        }
    });

    if(hasValue == true){
        if(total_expense_amount != total_amount){
            frappe.throw("The split amount does not match the expense total amount.");
        }
    }else{
        return true
    }
    
}