{
    "name": "Employee Field Changes",
    "category": "Extra Tools",
    "summary": "Add custom fields in employee",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr", "uae_wps_report", "hr_employee_firstname", 'hr_modification', 'hr_holidays'],
    "data": [
        "security/ir.model.access.csv",
        'data/ir_sequence_data.xml',
        'views/hr_employee_type_view.xml',
        "views/hr_employee.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
