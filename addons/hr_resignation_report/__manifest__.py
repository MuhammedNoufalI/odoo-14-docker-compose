# -*- coding: utf-8 -*-
{
    'name': "Hr Resignation Report",
    'summary': """
        Resignation Report
    """,
    'description': """
        Resignation Report
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr_resignation'],
    'data': [
        'security/ir.model.access.csv',
        'report/report.xml',
        'report/report_template.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
