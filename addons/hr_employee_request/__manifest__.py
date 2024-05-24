# -*- coding: utf-8 -*-

{
    'name': 'Employee Requests',
    'version': '13.0',
    'category': 'HR',
    'summary': 'Employee Can request multi types of requested that will be called in the payslip calculations',
    'description': """
Employee Request
----------------------------------
Employee Can request multi types of requested that will be called in the payslip calculations.
Requests will be linked to codes which will be called in the python code of rules calculations
""",
    'depends': ['hr','hr_payroll'],
    'data': [
        'security/hr_employee_request_security.xml',
        'security/ir.model.access.csv',
        'views/hr_request_view.xml',
        'views/hr_request_type_view.xml',
        'data/data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
