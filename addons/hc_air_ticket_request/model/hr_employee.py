from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ticket_benefit_date = fields.Date("Ticket Benefit Date",compute='compute_ticket_benefit_date')
    last_ticket_availed_date = fields.Date("Last Ticket Availed Date")
    ticket_balance = fields.Float("Ticket Balance")
    ticket_availed = fields.Integer("Ticket Availed")

    @api.depends('joining_date')
    def compute_ticket_benefit_date(self):
        if self.joining_date:
            self.ticket_benefit_date = self.joining_date
        else:
            self.ticket_benefit_date = False
