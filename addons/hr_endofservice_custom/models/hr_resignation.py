# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HRResignation(models.Model):
    _inherit = 'hr.resignation'

    gratuity_id = fields.Many2one('hr.gratuity', string="Gratuity")

    def action_create_gratuity(self):
        gratuity = self.env['hr.gratuity'].create({
            'employee_id': self.employee_id.id,
            'employee_exit_date': self.expected_revealing_date,

        })
        gratuity._onchange_employee_id()
        gratuity._onchange_emp_id()
        self.gratuity_id = gratuity.id
        if self.expected_revealing_date <= fields.Date.today() and self.employee_id.active:
            self.employee_id.active = False
            self.employee_id.contract_id.state = 'close'
            if self.employee_id.user_id:
                # rec.employee_id.user_id.active = False
                self.employee_id.user_id = None
        return {
            "name": 'Gratuity',
            "view_mode": "form",
            "res_model": "hr.gratuity",
            "type": "ir.actions.act_window",
            "res_id": gratuity.id
        }