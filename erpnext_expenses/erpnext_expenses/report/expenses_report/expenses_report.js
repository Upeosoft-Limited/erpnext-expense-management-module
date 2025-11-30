// Copyright (c) 2025, Karani Geoffrey and contributors
// For license information, please see license.txt

frappe.query_reports["Expenses Report"] = {
	"filters": [
{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": "Company",
			"mandatory": 0,
			"options": "Company",
			"wildcard_filter": 0
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"mandatory": 0,
			"wildcard_filter": 0
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"mandatory": 0,
			"wildcard_filter": 0
		},
		{
			"fieldname": "currency",
			"label": __("Moneda"),
			"fieldtype": "Link",
			"options": "Currency"
		}
	]	
};