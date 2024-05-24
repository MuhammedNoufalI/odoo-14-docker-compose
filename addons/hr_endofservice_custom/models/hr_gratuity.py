# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HRGratutiy(models.Model):
    _inherit = 'hr.gratuity'

    leave_balance = fields.Char(string="Leave Balance", compute="_compute_leave_balance")
    leave_balance_amount = fields.Char(string="Leave Balance", compute="_compute_leave_balance")
    last_salary = fields.Char(string="Last Salary", compute="_compute_last_salary")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    gratuity_date = fields.Date(string="Gratuity Date")

    def _compute_leave_balance(self):
        for rec in self:
            types = self.env['hr.leave.type'].sudo().search([
                ('is_gratuity', '=', True)
            ])
            leaves = self.env['hr.leave.allocation'].sudo().search([
                ('employee_id', '=', rec.employee_id.id),
                ('holiday_status_id', 'in', types.ids),
            ])
            rec.leave_balance = sum(leaves.mapped('number_of_days_display'))
            rec.leave_balance_amount = rec.employee_id.get_balance_allowence_amount()

    def _compute_last_salary(self):
        for rec in self:
            if rec.payslip_id:
                rec.last_salary = sum(rec.payslip_id.line_ids.filtered(lambda x: x.code == 'NET').mapped('total'))
            else:
                rec.last_salary = 0

    def unlink(self):
        for record in self:
            if record.state == 'approve':
                raise UserError(_("You cannot delete an approved record."))
        return super(HRGratutiy, self).unlink()