# -*- coding: utf-8 -*-
{
    'name': "Payslip Payment",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "odooerp-ae,ahmed mokhlef",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_accountant','hr'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/payslip_batches.xml',
        'views/multi_statement.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}