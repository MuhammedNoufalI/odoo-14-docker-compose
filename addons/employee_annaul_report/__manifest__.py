# -*- coding: utf-8 -*-
{
    'name': "Employee Annual Leaves",
    'summary': """
        Get the Employee Annual Leaves
    """,
    'description': """
       Get the Employee Annual Leaves
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
    ],
    'post_init_hook': 'create_emp_ann_leaves',
}
