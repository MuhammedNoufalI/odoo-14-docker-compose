# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'All in one import images from zip file',
    'version': '16.0.1.0.0',
    'sequence': 11,
    'category': 'Extra Tools',
    'summary': 'import image from zip import product image from zip import bulk image from zip import partner image from zip import images from zip file import product images from zip import image by zip import images by zip all images import from zip product image import',
    "price": 12,
    "currency": 'EUR',
    'description': """ """,
    'author': 'Hash Code IT Solutions',
    'company': 'Hash Code IT Solutions',
    'maintainer': 'Hash Code IT Solutions',
    'category': 'Generic Modules/Human Resources',
    'website': "https://www.hashcodeit.com",


    'depends': ['base','sale','account','hr','sale_management'],
    'data': ['security/img_security.xml',
            'security/ir.model.access.csv',
            'wizard/sale.xml',
            "data/attachment_sample.xml"

             ],

	'qweb': [
		],

    'demo': [],
    'test': [],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    "images": ["static/description/icon.png"],
}
