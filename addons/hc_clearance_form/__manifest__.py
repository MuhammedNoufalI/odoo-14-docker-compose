# -*- coding: utf-8 -*-
{
    'name': "Clearance Workflow",
    "author": "frs",
    'maintainer': 'asn',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.4',
    'support': 'info@hashcodeit.com',
    'category': '',
    'summary': "",
    'description': """"
    """,
    'depends': ['hr_resignation'],
    'data': [
        'data/ir_module_category_data.xml',
        'security/ir.model.access.csv',
        'views/hr_clearance_view.xml',
        'views/hr_resignation_view.xml',
        'reports/report.xml',
        'reports/hr_clearence_form.xml',
    ],

    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
