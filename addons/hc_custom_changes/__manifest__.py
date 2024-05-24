# -*- coding: utf-8 -*-
{
    'name': "Custom Changes",
    "author": "asn",
    'maintainer': 'asn',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.2',
    'support': 'info@hashcodeit.com',
    'category': '',
    'summary': "",
    'description': """"
    """,
    'depends': ['employee_field_changes', 'hr_employee_updation', 'hc_branch', 'hr_modification','hr_employee_lastnames'],
    'data': [
        'views/hr_employee_view.xml',
        'views/hr_contract.xml'
    ],

    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
