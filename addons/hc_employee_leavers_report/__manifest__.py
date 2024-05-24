# -*- coding: utf-8 -*-
{
    'name': 'Employee Leavers Report',
    "author": 'awn',
    'maintainer': 'awn,rhn',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.0',
    'support': 'info@hashcodeit.com',
    'category': '',
    'summary': 'Employee Leavers Report',
    'description': """ """,
    'depends': ['base','hr', 'hr_gratuity_settlement'],
    'data': ['security/ir.model.access.csv',
             'report/leavers_report.xml',
             'report/leavers_report_template.xml',
             'wizard/leavers_report_wizard.xml',
             'views/leavers_report.xml'],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'application': False,
    'installable': True,
    'auto_install': False,
}


