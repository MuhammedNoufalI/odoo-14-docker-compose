# -*- coding: utf-8 -*-
{
    'name': 'Time Off Customization',
    'description': """ Time Off Customization """,
    "author": "Hashcode IT Solutions",
    'maintainer': 'frs',
    'website': 'https://hashcodeit.com/',
    'version': '14.0.0.0.1',
    'support': 'info@hashcodeit.com',
    'category': 'Human Resources',
    'depends': ['base', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/time_off_allocation_views.xml',
        'views/time_off_views.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
