# -*- coding: utf-8 -*-
{
    'name': "access_update_qty",

    'summary': """
        access_update_qty""",

    'description': """
        access_update_qty
    """,
    'version': '1.0.0',
    'depends': [
        'stock',
        'product',
    ],
    # always loaded
    'data': [
        'views/product.xml',
        'security/security.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
