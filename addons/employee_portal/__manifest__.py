# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Employee Portal',
    'category': 'account',
    'summary': 'Employee Portal',
    'description': """
        Publish your employees public information on About Us website page.
    """,
    'depends': [
        'account',
        'portal',
        'base',
        'hr_holidays',
        'website',
        'hr',
        'hr_payroll',
        'web',
        'website_test',
        'hr_attendance',
        'loan_portal',
        'custody_portal'
    ],
    'demo': [
    ],
    'qweb': [
        # 'static/src/xml/row_template.xml',
    ],
    'data': [
        'views/menu.xml',
        'views/employee_details.xml',
        'views/leaves_history.xml',
        'views/attendance.xml',
        'views/payslip_history.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
