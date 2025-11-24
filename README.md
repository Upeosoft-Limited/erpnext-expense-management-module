# ERPNext Expenses

Sistema completo de gestión de gastos para ERPNext con flujo de aprobación y generación automática de asientos contables.

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [DocTypes](#doctypes)
- [Flujo de Trabajo](#flujo-de-trabajo)
- [Instalación](#instalación)
- [Configuración Inicial](#configuración-inicial)
- [Guía de Uso](#guía-de-uso)
- [Integración con l10n_ve](#integración-con-l10n_ve)
- [API](#api)

---

## Descripción General

**ERPNext Expenses** es una aplicación de Frappe que permite a las organizaciones gestionar el ciclo completo de gastos de empleados, desde el registro individual hasta la contabilización y reembolso.

### Características Principales

✅ Registro de gastos individuales por empleado
✅ Agrupación de gastos en reportes para aprobación
✅ Flujo de trabajo configurable con múltiples niveles de aprobación
✅ Generación automática de asientos contables (Journal Entries)
✅ Validación de duplicados y control de integridad
✅ Cancelación automática de asientos al cancelar reportes
✅ Soporte para múltiples categorías de gastos
✅ División de gastos entre proyectos/centros de costo

---

## Arquitectura

### Modelo de Datos

```
Employee
    ↓
Expense (Gasto Individual)
    ├── Expense Category → Cuenta Contable
    └── Expense Splitting Detail (División opcional)
        ↓
Expense Report (Agrupación)
    ├── Expense Detail (Tabla hija)
    ├── Journal Entry (Generado automáticamente)
    └── Workflow States
```

### Flujo de Estados

```
Expense:
  Draft → Submitted

Expense Report:
  Draft → Pending Manager → Pending Finance → Approved → Journals Created
                ↓                  ↓              ↓
            Rejected           Rejected      Rejected
```

---

## DocTypes

### 1. **Expense** (Gasto Individual)

Representa un gasto único incurrido por un empleado.

**Campos Principales:**

- `employee`: Empleado que realizó el gasto
- `expense_date`: Fecha del gasto
- `category`: Categoría del gasto (Link a Expense Category)
- `expense_description`: Descripción del gasto
- `total`: Monto total
- `company`: Empresa
- `paid_by`: Quién pagó (Empresa/Empleado)
- `workflow_state`: Estado del gasto

**Ejemplo:**

```python
{
    "doctype": "Expense",
    "employee": "EMP-00001",
    "expense_date": "2025-11-23",
    "category": "Viajes",
    "expense_description": "Taxi al aeropuerto",
    "total": 50.00,
    "company": "Mi Empresa",
    "paid_by": "Empleado"
}
```

### 2. **Expense Category** (Categoría de Gasto)

Define las categorías de gastos y sus cuentas contables asociadas.

**Campos Principales:**

- `category_name`: Nombre de la categoría
- `expense_account`: Cuenta contable de gasto

**Ejemplo:**

```python
{
    "doctype": "Expense Category",
    "category_name": "Viajes",
    "expense_account": "5.1.01.001 - Gastos de Viaje"
}
```

### 3. **Expense Splitting Detail** (División de Gastos)

Permite dividir un gasto entre múltiples ítems o proyectos.

**Campos Principales:**

- `item`: Ítem o proyecto
- `amount`: Monto asignado

**Ejemplo:**

```python
{
    "doctype": "Expense Splitting Detail",
    "parent": "EXP-2025-11-0001",
    "item": "Proyecto A",
    "amount": 30.00
}
```

### 4. **Expense Report** (Reporte de Gastos)

Agrupa múltiples gastos para aprobación y contabilización.

**Campos Principales:**

- `employee`: Empleado que reporta
- `company`: Empresa
- `paid_by`: Quién pagó
- `expense`: Tabla de Expense Detail
- `paying_account`: Cuenta de pago (obligatorio en estado Approved)
- `journal_entry`: Link al Journal Entry generado
- `workflow_state`: Estado del reporte

**Ejemplo:**

```python
{
    "doctype": "Expense Report",
    "employee": "EMP-00001",
    "company": "Mi Empresa",
    "paid_by": "Empleado",
    "paying_account": "1.1.01.001 - Banco Principal",
    "expense": [
        {
            "expense_id": "EXP-2025-11-0001",
            "subtotal": 50.00
        },
        {
            "expense_id": "EXP-2025-11-0002",
            "subtotal": 75.00
        }
    ]
}
```

### 5. **Expense Detail** (Detalle de Gasto en Reporte)

Tabla hija que vincula gastos individuales al reporte.

**Campos Principales:**

- `expense_id`: Link al Expense
- `expense_date`: Fecha del gasto
- `category`: Categoría
- `description`: Descripción
- `subtotal`: Monto

---

## Flujo de Trabajo

### Workflow del Expense Report

```
Draft → Submit to Manager → Pending Manager
                                  ↓
                            Approve/Reject
                                  ↓
                          Pending Finance
                                  ↓
                            Approve/Reject
                                  ↓
                              Approved
                                  ↓
                       Create Journal Entries
                                  ↓
                          Journals Created
```

### Estados y Transiciones

| Estado               | Descripción                       | Acciones Disponibles               |
| -------------------- | --------------------------------- | ---------------------------------- |
| **Draft**            | Borrador inicial                  | Submit to Manager                  |
| **Pending Manager**  | Esperando aprobación del gerente  | Approve, Reject, Request Amendment |
| **Pending Finance**  | Esperando aprobación de finanzas  | Approve, Reject                    |
| **Approved**         | Aprobado, listo para contabilizar | Create Journal Entries, Cancel     |
| **Journals Created** | Asientos contables creados        | Cancel                             |
| **Rejected**         | Rechazado                         | Recall                             |
| **Cancelled**        | Cancelado                         | -                                  |

### Roles y Permisos

- **Employee**: Puede crear y ver sus propios gastos
- **Expense Manager**: Puede aprobar reportes en nivel Manager
- **Accounts User**: Puede aprobar en nivel Finance y crear Journal Entries
- **Accounts Manager**: Acceso completo

---

## Instalación

### Requisitos Previos

- Frappe Framework v15+
- ERPNext v15+
- Python 3.10+

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
cd ~/frappe-bench/apps
git clone [URL_DEL_REPOSITORIO] erpnext_expenses

# 2. Instalar la app en el sitio
bench --site [nombre_sitio] install-app erpnext_expenses

# 3. Ejecutar migraciones
bench --site [nombre_sitio] migrate

# 4. Reiniciar bench
bench restart
```

---

## Configuración Inicial

### 1. Crear Categorías de Gastos

Navega a: **Gastos > Expense Category > New**

```
Categoría: Viajes
Cuenta de Gasto: 5.1.01.001 - Gastos de Viaje

Categoría: Comidas
Cuenta de Gasto: 5.1.01.002 - Gastos de Alimentación

Categoría: Alojamiento
Cuenta de Gasto: 5.1.01.003 - Gastos de Hospedaje
```

### 2. Configurar Empleados

Asegúrate de que cada empleado tenga:

- Usuario de Frappe asociado
- Rol "Employee" asignado

### 3. Configurar Cuentas de Pago

Define las cuentas bancarias que se usarán para reembolsos.

---

## Guía de Uso

### Caso de Uso Completo

#### Paso 1: Empleado Registra Gastos

Juan viaja a una conferencia y registra sus gastos:

```python
# Gasto 1: Taxi
{
    "expense_date": "2025-11-20",
    "category": "Viajes",
    "expense_description": "Taxi al aeropuerto",
    "total": 50.00
}

# Gasto 2: Hotel
{
    "expense_date": "2025-11-20",
    "category": "Alojamiento",
    "expense_description": "Hotel 2 noches",
    "total": 200.00
}

# Gasto 3: Comida
{
    "expense_date": "2025-11-21",
    "category": "Comidas",
    "expense_description": "Cena con cliente",
    "total": 75.00
}
```

#### Paso 2: Crear Expense Report

Juan agrupa todos los gastos:

1. Abre cualquier Expense en estado "Submitted"
2. Click en "Crear Reporte"
3. Se crea automáticamente un Expense Report con ese gasto
4. Puede agregar más gastos manualmente

**Total del Reporte:** Bs. 325.00

#### Paso 3: Flujo de Aprobación

```
1. Juan: Submit to Manager
   ↓
2. Gerente: Approve
   ↓
3. Finanzas: Approve
   ↓
4. Estado: Approved
```

#### Paso 4: Seleccionar Cuenta de Pago

En estado "Approved", el campo `paying_account` se vuelve obligatorio:

```
Paying Account: 1.1.01.001 - Banco Principal
```

#### Paso 5: Generar Asiento Contable

Click en "Create Journal Entries" o aprobar automáticamente.

**Journal Entry Generado:**

```
DÉBITO:
  5.1.01.001 - Gastos de Viaje:       Bs.  50.00
  5.1.01.003 - Gastos de Hospedaje:   Bs. 200.00
  5.1.01.002 - Gastos de Alimentación: Bs.  75.00
  ─────────────────────────────────────────────
  Total Débito:                       Bs. 325.00

CRÉDITO:
  1.1.01.001 - Banco Principal:       Bs. 325.00
  ─────────────────────────────────────────────
  Total Crédito:                      Bs. 325.00
```

#### Paso 6: Estado Final

```
Expense Report: REPORT-2025-11-0001
├── Estado: Journals Created
├── Journal Entry: ACC-JV-2025-00001
└── Listo para pago
```

---

## Integración con l10n_ve

La aplicación está diseñada para integrarse con la localización venezolana (`l10n_ve`).

### Separación de Responsabilidades

**erpnext_expenses:**

- Gestión de gastos y reportes
- Flujo de aprobación
- Generación de Journal Entry básico (sin impuestos)

**l10n_ve:**

- Cálculo de impuestos venezolanos (IVA, IGTF, retenciones)
- Agregación de líneas de impuestos al Journal Entry
- Validaciones fiscales específicas de Venezuela

### Hooks Recomendados para l10n_ve

```python
# En l10n_ve/hooks.py

doc_events = {
    "Journal Entry": {
        "before_submit": "l10n_ve.overrides.journal_entry.add_venezuelan_taxes"
    }
}
```

### Ejemplo de Extensión

```python
# l10n_ve/overrides/journal_entry.py

def add_venezuelan_taxes(doc, method):
    """Agrega impuestos venezolanos al Journal Entry"""

    if doc.remark and "Expense Report:" in doc.remark:
        # Calcular IVA, IGTF, etc.
        # Agregar líneas al Journal Entry
        pass
```

---

## API

### Funciones Whitelisted

#### `create_expense_report(expense, details=None)`

Crea un Expense Report desde uno o varios gastos.

**Parámetros:**

- `expense` (str): ID del Expense principal
- `details` (list, optional): Lista de detalles de gastos adicionales

**Retorna:**

```python
{
    "response": "Success",
    "expense": "REPORT-2025-11-0001"
}
```

**Ejemplo:**

```javascript
frappe.call({
  method:
    "erpnext_expenses.erpnext_expenses.doctype.expense.expense.create_expense_report",
  args: {
    expense: "EXP-2025-11-0001",
  },
  callback: function (r) {
    console.log(r.message);
  },
});
```

#### `create_journal_entries(report)`

Genera el Journal Entry para un Expense Report aprobado.

**Parámetros:**

- `report` (str): Nombre del Expense Report

**Retorna:**

```python
{
    "success": True,
    "journal_entry": "ACC-JV-2025-00001"
}
```

**Ejemplo:**

```javascript
frappe.call({
  method:
    "erpnext_expenses.erpnext_expenses.doctype.expense_report.expense_report.create_journal_entries",
  args: {
    report: "REPORT-2025-11-0001",
  },
  callback: function (r) {
    if (r.message.success) {
      frappe.msgprint("Asiento creado: " + r.message.journal_entry);
    }
  },
});
```

---

## Validaciones y Reglas de Negocio

### 1. Un Expense solo puede estar en un Expense Report activo

```python
# Si intentas crear un segundo reporte con el mismo gasto:
❌ Error: "Este gasto ya está incluido en el Reporte de Gastos REPORT-2025-11-0001"
```

### 2. Paying Account es obligatorio en estado Approved

```python
# No puedes crear Journal Entries sin seleccionar cuenta de pago
❌ Error: "Debe seleccionar una Cuenta de Pago antes de crear los asientos contables"
```

### 3. Cancelación en Cascada

```python
# Al cancelar un Expense Report:
1. Se cancela automáticamente el Journal Entry asociado
2. El campo journal_entry se limpia
3. Los Expenses vuelven a estado disponible
```

### 4. Protección contra Cancelación Directa de Journal Entry

```python
# No puedes cancelar un JE si está vinculado a un Expense Report activo
# Debes cancelar primero el Expense Report
```

---

## Solución de Problemas

### Error: "Namespace collision"

**Problema:** Conflicto de nombres de paquetes.

**Solución:**

```bash
# Verificar apps.txt
cat sites/apps.txt

# Reinstalar la app
bench --site [sitio] uninstall-app erpnext_expenses
bench --site [sitio] install-app erpnext_expenses --force
```

### Error: "Journal Entry no se cancela"

**Problema:** Dependencia circular.

**Solución:** Ya está implementado con `flags.ignore_links = True` en el código.

### Error: "Workflow state no cambia"

**Problema:** Fixtures no aplicados.

**Solución:**

```bash
bench --site [sitio] migrate
bench clear-cache
```

---

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## Licencia

MIT License

---

## Soporte

Para reportar bugs o solicitar features, abre un issue en el repositorio.

---

## Changelog

### v0.0.1 (2025-11-23)

- ✅ Implementación inicial de Expense y Expense Report
- ✅ Workflow de aprobación multinivel
- ✅ Generación automática de Journal Entries
- ✅ Validación de duplicados
- ✅ Cancelación en cascada
- ✅ Type hints en todas las funciones
- ✅ Mensajes en español
- ✅ Integración preparada para l10n_ve
