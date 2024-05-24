# -*- coding: utf-8 -*-
{
    'name': "ps_report",

    'summary': """
        Print Payslip Report for Employees""",

    'description': """
        This app helps you to print the Payslip for Employee.
    """,
    'category': 'Employees',
    'version': '14.0.1',
    'depends': ['base', 'hr_payroll','leave_custom'],
    # always loaded
    'data': [
        'views/hr_payslip_view.xml',
        'views/templates.xml',
        'views/report_views.xml',
        'views/rule.xml',
    ],
    "application": True,
    "installable": True,
}
