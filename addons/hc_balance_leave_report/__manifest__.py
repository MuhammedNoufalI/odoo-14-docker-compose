# -*- coding: utf-8 -*-
{
    'name': 'Leave Balance Report',
    "author": 'asn',
    'maintainer': 'asn',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.0',
    'support': 'info@hashcodeit.com',
    'category': 'Human Resources',
    'summary': 'Leave Balance Report',
    'description': """ Leave Balance Report """,
    'depends': ['web', 'hr_contract', 'hc_payroll_customization','base'],
    'data': [
        'report/report_action.xml',
        'security/ir.model.access.csv',
        'wizard/balance_leave_view.xml'

    ],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
