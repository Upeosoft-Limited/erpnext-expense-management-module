
import os
import csv

import frappe


def set_data():
    """
    Configura los datos iniciales para erpnext_expenses.
    Lee el archivo expense_category.csv y crea las categorías de gastos.
    """
    print("Iniciando configuración de datos para erpnext_expenses...")
    create_expense_categories()
    create_expense_manager_role()
    print("Configuración de datos completada.")


def create_expense_categories():
    """
    Crea registros de Expense Category basados en el CSV de recursos.
    Itera por todas las compañías para asignar la cuenta contable correcta.
    """
    print("Creando categorías de gastos...")

    # Ruta al archivo CSV
    csv_file_path = frappe.get_app_path('erpnext_expenses', 'erpnext_expenses', 'resources', 'setup', 'expense_category.csv')

    if not os.path.exists(csv_file_path):
        print(f"Error: No se encontró el archivo CSV en {csv_file_path}")
        return

    # Obtener todas las compañías
    companies = frappe.get_all("Company", pluck="name")
    if not companies:
        print("No se encontraron compañías en el sistema.")
        return

    categories_without_account = []

    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            # Convertir a lista para poder iterar múltiples veces si fuera necesario,
            # pero aquí iteramos compañías fuera y filas dentro, o viceversa.
            # Mejor iterar filas y por cada fila iterar compañías para procesar el CSV una vez.
            csv_rows = list(reader)

            for company in companies:
                print(f"Procesando compañía: {company}")

                for row in csv_rows:
                    description = row.get('Descripción', '').strip()
                    code = row.get('Codigo', '').strip()

                    if not description:
                        continue

                    # 1. Buscar cuenta con nombre EXACTO
                    account_name = frappe.db.get_value("Account", {
                        "account_name": description,
                        "company": company,
                        "is_group": 0
                    }, "name")

                    # 2. Si no existe, buscar "OTROS GASTOS"
                    if not account_name:
                        account_name = frappe.db.get_value("Account", {
                            "account_name": "OTROS GASTOS",
                            "company": company,
                            "is_group": 0
                        }, "name")

                    # 3. Si no se consigue cuenta
                    if not account_name:
                        msg = f"No se encontró cuenta para la categoría '{description}' en la compañía '{company}'"
                        print(msg)
                        categories_without_account.append(msg)
                        continue

                    # Crear Expense Category
                    # Verificamos si ya existe una categoría con este código
                    exists = frappe.db.exists("Expense Category", {"code": code}) if code else False

                    # Fallback check if code is empty (shouldn't be based on CSV)
                    if not exists:
                         exists = frappe.db.exists("Expense Category", {
                            "category_name": description,
                            "expense_account": account_name
                        })

                    if not exists:
                        try:
                            doc = frappe.new_doc("Expense Category")
                            doc.category_name = description
                            doc.expense_account = account_name
                            if code:
                                doc.code = code
                            doc.insert(ignore_permissions=True)
                            print(f"  -> Creada categoría: {code} - {description} ({account_name})")
                        except Exception as e:
                            print(f"  !! Error creando categoría {description}: {e}")
                    else:
                        print(f"  -- Omitiendo (ya existe): {description} ({account_name})")

        frappe.db.commit()

        # Guardar registro de errores si hubo
        if categories_without_account:
            error_log_message = "\n".join(categories_without_account)
            frappe.log_error(message=error_log_message, title="Errores en Configuración de Categorías de Gastos")
            print("Se encontraron errores al asignar cuentas. Revise el Error Log.")

    except Exception as e:
        print(f"Error fatal procesando categorías de gastos: {e}")
        frappe.log_error(frappe.get_traceback(), 'Error en create_expense_categories')

    print("Success: Configuración de categorías de gastos completada.")


def create_expense_manager_role():
    """
    Crea el rol 'Expense Manager' y lo asigna al usuario Administrator.
    """
    print("Configurando Rol Expense Manager...")
    role_name = "Expense Manager"

    if not frappe.db.exists("Role", role_name):
        try:
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.desk_access = 1
            role.insert(ignore_permissions=True)
            print(f"  -> Rol '{role_name}' creado.")
        except Exception as e:
            print(f"  !! Error creando rol '{role_name}': {e}")
    else:
        print(f"  -- Rol '{role_name}' ya existe.")

    try:
        user = frappe.get_doc("User", "Administrator")
        current_roles = [r.role for r in user.roles]
        if role_name not in current_roles:
            user.append("roles", {"role": role_name})
            user.save(ignore_permissions=True)
            print(f"  -> Rol '{role_name}' asignado a Administrator.")
        else:
            print(f"  -- Administrator ya tiene el rol '{role_name}'.")
    except Exception as e:
        print(f"  !! Error asignando rol a Administrator: {e}")
