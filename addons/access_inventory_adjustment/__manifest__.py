{
    'name': "access_inventory_adjustment",

    'summary': """
        access_inventory_adjustment""",

    'description': """
        access_inventory_adjustment
    """,

    'version': '1.0.0',
    'depends': [
        'stock',
    ],
    # always loaded
    'data': [
        'security/security.xml',
        'views/stock.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
