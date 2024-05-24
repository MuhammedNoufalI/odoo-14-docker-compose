{
    'name': 'Expense Requests Portal',
    'category': 'Website',
    'sequence': 58,
    'summary': 'Qualify Request queries with a website ',
    'depends': [
        'hr_expense','portal','website','product'
    ],
    'description': """
        Generate Expense request in portal.
    """,
    'data': [
        'views/assets.xml',

        'views/expense_request_templates.xml',
        'views/menus.xml',

    ],
    'license': 'OEEL-1',
}
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

