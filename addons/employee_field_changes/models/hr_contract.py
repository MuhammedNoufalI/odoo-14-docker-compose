# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    registration_number = fields.Char(string="Employee Registration Number", compute='_compute_employee_reg_num')

    @api.depends('employee_id')
    def _compute_employee_reg_num(self):
        for record in self:
            if record.employee_id.registration_number:
                record.registration_number = record.employee_id.registration_number
            else:
                record.registration_number = False