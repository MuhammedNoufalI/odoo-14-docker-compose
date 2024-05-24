# -*- coding: utf-8 -*-
{
    'name': 'Leave Customization',
    'summary': "Leave Customization",
    'description': "Leave Customization",
    'category': 'hr',
    'version': '13.0.0.1.0',
    'depends': [
        'base',
        'hr',
        'hr_holidays',
        'hr_contract',
        'hr_payroll',
        'user_notification',
        'resource',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/employee.xml',
        'views/contract.xml',
        'views/cron.xml',
        'views/res_config.xml',
        'views/menus.xml',
        'views/leave_type.xml',
        'views/leave_allocation.xml',
        'wizards/allocation_post.xml',
        'wizards/ticket_rule.xml',
        'views/hr_attendance_view.xml'
    ],
    'auto_install': False,
    'installable': True,

}
