# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    def get_gratuity_amount(self):
        for rec in self:
            amount = 0
            payslip = self.env['hr.payslip'].sudo().search([
                ('employee_id', '=', rec.id),
            ], limit=1, order="id desc")
            gratuity = self.env['hr.gratuity'].sudo().search([
                ('employee_id', '=', rec.id),
                ('gratuity_date', '>=', payslip.date_from),
                ('gratuity_date', '<=', payslip.date_to),
            ], limit=1)
            amount = gratuity.employee_gratuity_amount
            gratuity.payslip_id = payslip.id
            return amount

    def _compute_leave_balance(self):
        for rec in self:
            types = self.env['hr.leave.type'].sudo().search([
                ('is_gratuity', '=', True)
            ])
            leaves = self.env['hr.leave.allocation'].sudo().search([
                ('employee_id', '=', rec.id),
                ('holiday_status_id', 'in', types.ids),
            ])
            return sum(leaves.mapped('number_of_days_display'))

    def get_balance_allowence_amount(self):
        for rec in self:
            payslip = self.env['hr.payslip'].sudo().search([
                ('employee_id', '=', rec.id),
            ], limit=1, order="id desc")
            gratuity = self.env['hr.gratuity'].sudo().search([
                ('employee_id', '=', rec.id),
                ('gratuity_date', '>=', payslip.date_from),
                ('gratuity_date', '<=', payslip.date_to),
            ], limit=1)
            if gratuity:
                return (rec._compute_last_salary()/30) * rec._compute_leave_balance()
            return 0

    def _compute_last_salary(self):
        return self.contract_id.wage if self.contract_id else 0
