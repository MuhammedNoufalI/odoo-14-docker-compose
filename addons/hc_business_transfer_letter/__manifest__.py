# -*- coding:utf-8 -*-

{
    'name': 'Business Transfer Letter Workflow',
    'category': 'Employees',
    'version': '14.0.1.0.2',
    'sequence': 1,
    'author': 'asn',
    'maintainer': 'asn',
    'summary': 'Business Transfer Letter Workflow',
    'description': "",
    'depends': [
        'base', 'resource', 'hr','hr_departure_modi','hc_employee_customization'],
    'data': [
        'security/ir.model.access.csv',
        'views/business_transfer_letter.xml',
        'report/report.xml',
        'report/transfer_letter_template.xml'
    ],

    "images": ["static/description/icon.png"],
    'application': True,
    'license': 'OPL-1',
}
