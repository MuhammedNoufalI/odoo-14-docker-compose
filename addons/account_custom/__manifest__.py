# -*- coding: utf-8 -*-

{
    "name": "account_custom",
    "depends": ['account', 'sale_management', 'account_reports', 'product', 'stock', 'purchase'],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_invoice.xml',
        'views/payment.xml',
        'views/refund_reason.xml',
        'views/sale.xml',
        'views/partner.xml',
        'data/sequence.xml',
        'views/stock_picking.xml'
    ],
    "auto_install": False,
    "installable": True,
}
