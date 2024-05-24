# -*- coding: utf-8 -*-
{
    'name': "Asset Request Management",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Oakland",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Assets',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','purchase','stock','account_accountant','account_asset','hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/asset_request.xml',
        'views/asset_group.xml',
        'views/asset.xml',
        'views/asset_transfer.xml',
        'views/report_purchase_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
