# -*- coding: utf-8 -*-
{
    'name': "Employee Month Attendances",
    'summary': """
        Get Employee Month Attendances on Payslip
    """,
    'description': """
        Get Employee Month Attendances on Payslip
    """,
    'author': "odooERP.ae",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '14.0.0.1',
    'depends': ['base', 'hr', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
