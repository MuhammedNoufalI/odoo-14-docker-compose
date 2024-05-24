# -*- coding: utf-8 -*-
{
    'name': "OdooERP Attendances API Integration",
    'version': '14.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': """Attendances API Integration""",
    'depends': ['hr_attendance', 'sh_message'],
    'author': "OdooERP.ae, tou-odoo",
    'website': 'https://odooerp.ae/',
    'data': [
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'wizard/zk_teco_attendance_views.xml',
        'views/hr_attendance_view.xml',
        'views/res_company_view.xml',
    ],
    'license': 'LGPL-3',
}
