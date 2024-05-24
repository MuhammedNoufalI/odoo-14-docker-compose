# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from openerp.exceptions import Warning
from datetime import datetime
import pytz
import json
from odoo.tools import date_utils
class Ticketrule(models.TransientModel):

    _name = "ticket.rule"

    payslip_id = fields.Many2one(
        string="Payslip",
        comodel_name="hr.payslip",
        required=False)
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=False)
    ticket_rate = fields.Float()
    ticket_price = fields.Float()

    def apply(self):
        vals ={
            'name': 'TicketRule',
            'code': 'TicketRule',
            'num_of_days': 1,
            'num_of_hours': 1,
            'pay_amount': self.ticket_rate*self.ticket_price,
            'rule_id': self.payslip_id.id,
        }
        if self.ticket_rate*self.ticket_price:
            self.payslip_id.write({'attend_rule_ids': [(0, 0, vals)]})
            self.payslip_id.ticket_amount = self.ticket_rate*self.ticket_price
            self.payslip_id.compute_sheet()
        contract = self.env['hr.contract'].browse(self.env.context.get('active_id'))
        contract.ticket_allocation = 0