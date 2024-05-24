# -*- coding:utf-8 -*-

{
    'name': 'HC Payroll Customization',
    'category': 'Payroll',
    "author": "Hashcode IT Solutions",
    'website': 'https://hashcodeit.com/',
    'version': '16.0.1.2',
    'support': 'info@hashcodeit.com',
    'summary': 'HC Payroll Customization',
    'description': "",
    'depends': ['hr_payroll', 'hr_work_entry_contract', 'hr_payroll_account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        # 'views/ir_config_settings.xml',
        'views/payroll_period_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_payslip_batches_views.xml',
    ],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
