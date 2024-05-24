# -*- coding: utf-8 -*-
{
    'name': "Maternity Leaves",
    'summary': """
        Maternity Leaves
    """,
    'description': """
        Maternity Leaves
    """,
    'author': "odooERP.ae",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr', 'employee_field_changes', 'hr_modification'],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/views.xml',
        'views/maternity_leave_request.xml',
    ],
}
