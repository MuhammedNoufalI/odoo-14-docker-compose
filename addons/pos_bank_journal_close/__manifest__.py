# -*- coding: utf-8 -*-
{
    'name': "pos_bank_journal_close",

    'summary': """
        pos_bank_journal_close""",

    'description': """
        pos_bank_journal_close
    """,

    'author': "G2mdx",
    'website': "http://www.G2mdx.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','account'],

    # always loaded
    'data': [

        'views/payment_method.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}