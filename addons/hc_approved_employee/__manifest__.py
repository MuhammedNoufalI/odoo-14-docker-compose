# -*- coding: utf-8 -*-
{
    'name': 'Hc Approved Employee',
    "author": 'frs',
    'maintainer': '',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.0',
    'support': 'info@hashcodeit.com',
    'category': 'Human Resources',
    'summary': 'Hc Approved Employee',
    'description': """ Approved Employee """,
    'depends': ['hr', 'hr_appraisal', 'hr_contract', 'hr_gratuity_settlement'],
    'data': [
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml'
    ],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
