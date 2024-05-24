# -*- coding:utf-8 -*-

{
    'name': 'Cancel Leave Request',
    'category': 'Employees',
    'version': '14.0.1.0.0',
    'sequence': 1,
    'author': 'asn',
    'maintainer': 'asn',
    'summary': 'Cancel Leave Request',
    'description': "Cancel Leave Request",
    'depends': ['hr','hr_holidays'],
    'data': [
        'views/hr_leave_view.xml'
    ],

    "images": ["static/description/icon.png"],
    'application': True,
    'license': 'OPL-1',
}
