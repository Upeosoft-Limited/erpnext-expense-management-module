// Copyright (c) 2024, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense", {
  refresh: function (frm) {
    // Check if the workflow state is "pending_finance_approval"
    if (frm.doc.workflow_state === "pending_finance_approval") {
      // Show the paying_account field
      frm.toggle_display("paying_account", true);
    } else {
      // Hide the paying_account field
      frm.toggle_display("paying_account", false);
    }

    recalculateAmountsForCompanyCurrency(frm);

    if (frm.doc.workflow_state == "Submitted") {
      frm.add_custom_button("Crear Reporte", function () {
        frappe.call({
          method:
            "erpnext_expenses.erpnext_expenses.doctype.expense.expense.create_expense_report",
          args: {
            expense: frm.doc.name,
          },
          callback: function (r) {
            if (r.message.response == "Success") {
              frappe.set_route("Form", "Expense Report", r.message.expense);
            } else {
              frappe.msgprint({
                title: "Error",
                indicator: "red",
                message:
                  "Se produjo un error. Por favor intente nuevamente o póngase en contacto con el Administrador del sistema.",
              });
            }
          },
        });
      });
    }
  },

  onload: function (frm) {
    if (frm.is_new()) {
      frappe.call({
        method:
          "erpnext_expenses.erpnext_expenses.doctype.expense.expense.get_logged_in_employee",
        callback: function (response) {
          if (response.message) {
            frm.set_value("employee", response.message.employee);
            frm.set_value("employee_name", response.message.employee_name);
          }
        },
      });
    }

    update_item_filter(frm);
  },

  category: function (frm) {
    if (frm.doc.table_jkwj && frm.doc.table_jkwj.length > 0) {
      frm.clear_table("table_jkwj");
      frm.refresh_field("table_jkwj");
    }
    update_item_filter(frm);
  },

  validate: function (frm) {
    if (frm.doc.reference_no) {
      if (!/^\d+$/.test(frm.doc.reference_no)) {
        frappe.throw(__("El número de referencia solo debe contener números."));
      }
      if (frm.doc.reference_no.length < 4) {
        frappe.throw(__("El número de referencia debe tener al menos 4 dígitos."));
      }
    }
    let total_expense_amount = frm.doc.total;
    calculateTotalAmount(frm, total_expense_amount);
  },

  table_jkwj_add: function (frm) {
  },

  expense_date: function (frm) {
    if (frm.doc.expense_date > frappe.datetime.nowdate()) {
      frappe.msgprint("La fecha del gasto no puede ser en el futuro.");
      frappe.validated = false;
      frm.set_value("expense_date", "");
    }
  },

  spending_currency: async function (frm) {
    const old_rate = frm.doc.exchange_rate;
    const old_total_exchange = frm.doc.total_exchange;
    await recalculateAmountsForCompanyCurrency(
      frm,
      old_rate,
      old_total_exchange
    );
    frm.refresh_field("table_jkwj");
  },

  company: function (frm) {
    frm.trigger("spending_currency");
  },

  total_exchange: function (frm) {
    calculate_total_in_company_currency(frm);
  },

  exchange_rate: function (frm) {
    calculate_total_in_company_currency(frm);
  },

});

async function recalculateAmountsForCompanyCurrency(
  frm,
  old_rate = null,
  old_total_exchange = null
) {
  if (!frm.doc.company || !frm.doc.spending_currency) {
    frm.set_df_property("total", "label", "Total");
    frm
      .get_field("table_jkwj")
      .grid.update_docfield_property("amount", "label", "Importe");
    return;
  }

  const company_data = await frappe.db.get_value(
    "Company",
    frm.doc.company,
    "default_currency"
  );
  const company_currency = company_data?.message?.default_currency;

  if (!company_currency) {
    frappe.msgprint({
      title: __("Moneda no Encontrada"),
      indicator: "red",
      message: __(
        "No se pudo encontrar la moneda por defecto para la compañía seleccionada."
      ),
    });
    return;
  }

  frm.set_df_property("total", "label", `Total (${company_currency})`);

  const spending_currency = frm.doc.spending_currency;
  frm
    .get_field("table_jkwj")
    .grid.update_docfield_property(
      "amount",
      "label",
      `Importe (${spending_currency})`
    );

  if (frm.doc.spending_currency === company_currency) {
    frm.set_value("exchange_rate", 1);
    frm.toggle_display("total", false);

    if (old_rate && old_rate != 1 && old_total_exchange > 0) {
      frm.set_value(
        "total_exchange",
        flt(old_total_exchange * old_rate, precision("total_exchange"))
      );
      (frm.doc.table_jkwj || []).forEach((row) => {
        if (row.amount_exchange > 0) {
          let new_amount_exchange = flt(
            row.amount_exchange * old_rate,
            precision("amount_exchange", row)
          );
          frappe.model.set_value(
            row.doctype,
            row.name,
            "amount_exchange",
            new_amount_exchange
          );
        }
      });
    }
  } else {
    frm.toggle_display("total", true);
    const r = await frappe.call({
      method: "frappe.client.get_value",
      args: {
        doctype: "Currency Exchange",
        filters: {
          from_currency: frm.doc.spending_currency,
          to_currency: company_currency,
        },
        fieldname: ["exchange_rate"],
      },
    });

    if (r.message && r.message.exchange_rate) {
      const new_rate = r.message.exchange_rate;
      frm.set_value("exchange_rate", new_rate);

      if (old_rate == 1 && old_total_exchange > 0 && new_rate > 0) {
        frm.set_value(
          "total_exchange",
          flt(old_total_exchange / new_rate, precision("total_exchange"))
        );
      }

      (frm.doc.table_jkwj || []).forEach((row) => {
        if (row.amount > 0 && new_rate > 0) {
          let new_amount_exchange = flt(
            row.amount / new_rate, precision("amount_exchange", row)
          );
          frappe.model.set_value(
            row.doctype,
            row.name,
            "amount_exchange",
            new_amount_exchange
          );
        }
      });
    } else {
      frappe.msgprint({
        title: __("Tasa de Cambio no Encontrada"),
        indicator: "orange",
        message: __(
          "No se encontró una tasa de cambio para la moneda y fecha seleccionadas. Por favor, ingrésela manualmente."
        ),
      });
    }
  }
}

function update_item_filter(frm) {
  let category = frm.doc.category;
  if (category) {
    frappe.db.get_value("Expense Category", category, "item").then((r) => {
      let item_code = r.message.item;
      frm.set_query("item", "table_jkwj", function () {
        return {
          filters: {
            name: item_code || "non-existent-item",
          },
        };
      });
    });
  } else {
    frm.set_query("item", "table_jkwj", function () {
      return {
        filters: {
          name: "non-existent-item",
        },
      };
    });
  }
}

// get the total in real time as it is added to the splitting child table

frappe.ui.form.on(
  "Expense Splitting Detail",
  "amount",
  function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (frm.doc.exchange_rate > 0) {
      let new_amount_exchange = flt(
        row.amount / frm.doc.exchange_rate,
        precision("amount_exchange", row)
      );
      frappe.model.set_value(cdt, cdn, "amount_exchange", new_amount_exchange);
    }
    calculate_split_totals(frm);
  }
);

frappe.ui.form.on(
  "Expense Splitting Detail",
  "amount_exchange",
  function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let new_amount = flt(
      row.amount_exchange * frm.doc.exchange_rate,
      precision("amount", row)
    );
    frappe.model.set_value(cdt, cdn, "amount", new_amount);
    calculate_split_totals(frm);
  }
);

function calculate_split_totals(frm) {
  let split_total = 0;
  let split_exchange = 0;
  (frm.doc.table_jkwj || []).forEach((d) => {
    split_total += flt(d.amount, 2) || 0;
    split_exchange += flt(d.amount_exchange, 2) || 0;
  });
  frm.set_value({
    split_total: flt(split_total, 2),
    split_exchange: flt(split_exchange, 2),
  });
}

// Function to calculate total amount in the child table
function calculateTotalAmount(frm, total_expense_amount) {
  // Initialize total variable
  let total_amount = 0;
  let hasValue = false;

  // Loop through each row in the child table
  frm.doc.table_jkwj.forEach(function (item) {
    if (item.amount) {
      hasValue = true;
      // Sum up the amount field of each row
      total_amount += item.amount;
    }
  });

  if (hasValue == true) {
    if (flt(total_expense_amount, 2) != flt(total_amount, 2)) {
      frappe.throw(
        "El monto de la división no coincide con el monto total del gasto."
      );
    }
  } else {
    return true;
  }
}

function calculate_total_in_company_currency(frm) {
  if (frm.doc.total_exchange != null && frm.doc.exchange_rate != null) {
    let total = flt(
      frm.doc.total_exchange * frm.doc.exchange_rate,
      2
    );
    frm.set_value("total", total);
  }
}
