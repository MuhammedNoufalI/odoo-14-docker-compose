from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    ticket_amount = fields.Float("Ticket Amount")

    @api.onchange('payroll_period_id', 'employee_id')
    def compute_ticket_amount(self):
        for rec in self:
            ticket_request = self.env['ticket.request'].search(
                [('employee_id', '=', rec.employee_id.id), ('payroll_period', '=', rec.payroll_period_id.id),
                 ('amount_to_payslip', '=', True)])
            if ticket_request:
                rec.ticket_amount = ticket_request.ticket_amount
            else:
                rec.ticket_amount = 0.00
