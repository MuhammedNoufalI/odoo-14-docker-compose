from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, time


class AirTicketRequest(models.Model):
    _inherit = "hr.leave"

    ticket_request_id = fields.Many2one('ticket.request')

    def ticket_request(self):
        for rec in self:
            employee_id = self.employee_id
            employee_code = employee_id.oe_emp_sequence
            data = {
                'leave_id':rec.id,
                'employee_id': employee_id.id,
                'employee_code': employee_code,
                'request_date': date.today(),
                'ticket_entitlement':employee_id.contract_id.ticket_entitlement,
                'state': 'draft'
            }
            view_id = self.env['ticket.request'].create(data)
            rec.ticket_request_id = view_id.id
            return {
                'name': "Air Ticket Request Form",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'ticket.request',
                'view_id': self.env.ref('hc_air_ticket_request.air_ticket_request_form').id,
                'target': 'current',
                'res_id': view_id.id
            }

