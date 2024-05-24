# -*- coding: utf-8 -*-
{
    'name': "Parental Leave",
    'summary': """
        Employee Child's and Parental Leaves
    """,
    'description': """
        Employee Child's and Parental Leaves
    """,
    'author': "odooERP.ae",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr', 'employee_field_changes', 'hr_modification'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
