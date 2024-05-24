# -*- coding:utf-8 -*-

{
    'name': 'Exit Interview Workflow',
    'category': 'Employees',
    'version': '14.0.1.0.4',
    'sequence': 1,
    'author': 'asn',
    'maintainer': 'asn',
    'summary': 'Exit Interview Workflow',
    'description': "",
    'depends': [
        'base', 'resource', 'hr','hr_resignation','hc_clearance_form','hr_gratuity_settlement'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/exit_interview_view.xml',
        'views/hr_resignation_view.xml',
        'reports/exit_interview_workflow.xml',
        'reports/report.xml'
    ],

    "images": ["static/description/icon.png"],
    'application': True,
    'license': 'OPL-1',
}
