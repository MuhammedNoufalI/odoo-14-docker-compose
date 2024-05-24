# -*- coding:utf-8 -*-

{
    'name': 'HC Certificate',
    'category': 'Employees',
    'version': '14.0.1.0.0',
    'sequence': 1,
    'author': 'HC Certificate',
    'maintainer': 'asn',
    'summary': 'HC Certificate',
    'description': "HC Certificate",
    'depends': [
        'hr', 'sign'
    ],
    'data': [
        'data/seq.xml',
        'security/ir.model.access.csv',
        'views/hc_certificate.xml',
        'views/hc_certificate_request.xml',
        'report/certificate.xml',

    ],

    "images": ["static/description/icon.png"],
    'application': True,
    'license': 'OPL-1',
}
