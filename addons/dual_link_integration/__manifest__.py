# -*- coding: utf-8 -*-
{
    'name': "Dual Link Integration",

    'summary': """
        Dual Link Integration""",

    'description': """
        Dual Link Integration
    """,

    'version': '16.0.0.0',
    'category': 'Sale',
    'author': 'Oakland',
    'website': 'https://www.odooerp.ae',
    'license': 'LGPL-3',
    'application': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/data.xml',
        'data/rules.xml',
        'views/dual_link.xml',
        'views/places.xml',
        'views/pos_session.xml',
        'views/product.xml',
        'views/pos_order.xml',
        'views/dual_link_log.xml',
        'views/menuitems.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
