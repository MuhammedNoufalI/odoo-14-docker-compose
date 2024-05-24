# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custody Requests Portal',
    'category': 'Website',
    'sequence': 58,
    'summary': 'Qualify Request queries with a website ',
    'depends': [
        'hr_custody','portal','website'
    ],
    'description': """
Generate Custody request in portal.
    """,
    'data': [

        'views/custody_request_templates.xml',
        'views/menus.xml',

    ],
    'license': 'OEEL-1',
}
