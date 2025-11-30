
    // Archivo JS para personalizar la vista de lista de Expense Splitting Detail
    // Más información: https://frappeframework.com/docs/v15/user/en/desk/views/list-view#listviewsettings
    frappe.listview_settings['Expense Splitting Detail'] = {
    // add fields to fetch
    // add_fields: ['title', 'public'],
    // set default filters
    // filters: [
    //     ['public', '=', 1]
    // ],
    hide_name_column: true, // hide the last column which shows the `name`
    // hide_name_filter: true,
    has_indicator_for_draft: true,
    has_indicator_for_cancelled: true,
    onload(listview) {
        // triggers once before the list is loaded
        // Ejemplo: Añadir un botón
        // listview.page.add_inner_button(__("Mi Acción"), function() {
        // 	frappe.msgprint("Acción para Expense Splitting Detail");
        // });
    },
    before_render() {
        // triggers before every render of list records
    },

    // get_indicator(doc) {
        // customize indicator color
        // Ejemplo: Indicador basado en un campo 'status'
        // if (doc.status === "Approved") {
        // 	return [__("Approved"), "green", "status,=,Approved"];
        // } else if (doc.status === "Pending") {
        // 	return [__("Pending"), "orange", "status,=,Pending"];
        // } else {
        // 	return [__(doc.status), "darkgrey", `status,=,${doc.status}`];
        // }
    // },
    // primary_action() {
        // triggers when the primary action is clicked
        // Ejemplo: Acción por defecto
        // frappe.new_doc('Expense Splitting Detail');
    // },
    // get_form_link(doc) {
        // override the form route for this doc
        // Ejemplo: Ir a una ruta diferente si se cumple una condición
        // if (doc.custom_condition) {
        // 	return `/app/custom-route/${doc.name}`;
        // }
        // Si retorna null o undefined, usa la ruta estándar
        // return null;
    // },
    // add a custom button for each row
    // button: {
    // 	show(doc) {
    // 		// Mostrar botón solo si se cumple una condición
    // 		// return doc.status === 'Pending';
    // 		return true; // Mostrar siempre (ejemplo)
    // 	},
    // 	get_label() {
    // 		return __('Details'); // Etiqueta del botón
    // 	},
    // 	get_description(doc) {
    // 		// Tooltip del botón
    // 		return __('View Details for 0', [doc.name])
    // 	},
    // 	action(doc) {
    // 		// Acción al hacer clic en el botón
    // 		frappe.set_route('Form', 'Expense Splitting Detail', doc.name);
    // 	}
    // },
    // format how a field value is shown
    // formatters: {
    // 	subject(val) { // Asumiendo que tienes un campo 'subject'
    // 		return val.bold();
    // 	},
    // 	status(val) { // Asumiendo que tienes un campo 'status'
    // 		if (val === "Approved") {
    // 			return `<span style="color:green">${val}</span>`;
    // 		} else if (val === "Pending") {
    // 			return `<span style="color:orange">${val}</span>`;
    // 		} else {
    // 			return val;
    // 		}
    // 	}
    // }
};
