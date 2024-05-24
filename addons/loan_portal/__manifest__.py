# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Loan Requests Portal',
    'category': 'Website',
    'sequence': 58,
    'summary': 'Qualify Request queries with a website ',
    'depends': [
        'ohrms_loan','portal','website','hr'
    ],
    'description': """
        Generate Custody request in portal.
    """,
    'data': [

        'views/loan_request_templates.xml',
        'views/menus.xml',
        'views/salary_advance_request_templates.xml'

    ],
    'license': 'OEEL-1',
}
