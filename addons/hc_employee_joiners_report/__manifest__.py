# -*- coding: utf-8 -*-
{
    'name': 'Employee Joiners Report',
    "author": 'awn',
    'maintainer': 'awn,rhn',
    'company': 'Hash Code IT Solutions',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.1.0.0',
    'support': 'info@hashcodeit.com',
    'category': '',
    'summary': 'Employee Joiners Report',
    'description': """ """,
    'depends': ['base','hr','hr_employee_updation','hr_gratuity_settlement'],
    'data': ['security/ir.model.access.csv',
             'report/joiners_report.xml',
             'report/joiners_report_template.xml',
             'wizard/joiners_report_wizard.xml',
             'views/joiners_report.xml'],
    "images": ["static/description/icon.png"],
    'license': 'OPL-1',
    'application': False,
    'installable': True,
    'auto_install': False,
}


