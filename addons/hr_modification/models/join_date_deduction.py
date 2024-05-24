from odoo import fields, api, models


class InheritHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    joining_date_difference = fields.Integer("Joining Date Deduction")

    @api.onchange('employee_id', 'date_from', 'date_to')
    def _check_join_date(self):
        for rec in self:
            if (rec.employee_id.joining_date and rec.date_from) and (rec.employee_id.joining_date > rec.date_from):
                rec.joining_date_difference = (rec.employee_id.joining_date - rec.date_from).days
