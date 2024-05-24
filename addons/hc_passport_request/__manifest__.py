# -*- coding:utf-8 -*-

{
    'name': 'Passport Request',
    'category': 'Employees',
    'version': '14.0.1.0.0',
    'sequence': 1,
    'author': 'asn',
    'maintainer': 'asn',
    'summary': 'HC Certificate',
    'description': "Passport Request",
    'depends': ['hr', 'sign'],
    'data': [
        'data/seq.xml',
        'security/ir.model.access.csv',
        'views/passport_request_view.xml',
        'report/passport_request_form.xml'
    ],

    "images": ["static/description/icon.png"],
    'application': True,
    'license': 'OPL-1',
}
