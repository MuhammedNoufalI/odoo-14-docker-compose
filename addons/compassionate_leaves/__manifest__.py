# -*- coding: utf-8 -*-
{
    'name': "Bereavement Leaves",
    'summary': """
        Bereavement Leaves
    """,
    'description': """
        Bereavement Leaves
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
        'views/compassionate_leave_request.xml',
        'views/templates.xml',
    ],
}
