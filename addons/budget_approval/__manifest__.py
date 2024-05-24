{
    'name': "budget_approval",

    'summary': """
        budget_approval
        """,

    'description': """
        budget_approval
    """,
    'category': 'Purchase',
    'version': '1.0.0',
    'depends': [
        'base',
        'purchase',
        'user_notification',
        'account_accountant',
        'web_domain_field'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/budget_approval.xml',
        'views/purchase_order_line.xml',
        'views/journal_entries.xml',
        'views/product_category.xml',
    ],
    'demo': [
    ],
}
# -*- coding: utf-8 -*-
