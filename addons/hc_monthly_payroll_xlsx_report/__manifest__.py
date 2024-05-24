# -*- coding: utf-8 -*-
{
    'name': 'Monthly Payroll Xlsx Report',
    'author': 'asn',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.02',
    'maintainer': 'asn',
    'support': 'info@hashcodeit.com',
    'category': 'Human Resources',
    'summary': 'Monthly Payroll Xlsx Report',
    'description': """Monthly Payroll Xlsx Report""",
    'depends': ['hr', 'hr_contract', 'hc_payroll_customization', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'report/report_action.xml',
        'wizard/monthly_payroll_wiz.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
