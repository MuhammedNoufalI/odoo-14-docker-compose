# -*- coding: utf-8 -*-
from . import models
from odoo import api, SUPERUSER_ID


def create_emp_ann_leaves(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    all_emp = env['hr.employee'].search([])
    if all_emp:
        for emp in all_emp:
            env['employee.annual.leave'].create({
                'employee_id': emp.id,
                'total_leaves': 10,
                'al_taken': 5,
                'al_remaining': 5,
                'company_id': emp.company_id.id
            })
