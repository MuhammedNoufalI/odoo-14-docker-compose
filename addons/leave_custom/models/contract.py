# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class Contract(models.Model):
    _inherit = 'hr.contract'
    ticket_allocation = fields.Float()

    def create_ticket_allocation(self):
        running_contracts = self.search([('state', '=', 'open')])
        contract_wait_period = self.env.company.contract_wait_period
        for rec in running_contracts:
            if rec.date_start:
                date = fields.date.today()
                check_date = rec.date_start + relativedelta(months=contract_wait_period)
                if check_date < date:
                    rec.ticket_allocation = date.month/12

    def apply_in_payslip(self):
        return {
            'name': _('Ticket Rule'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'ticket.rule',

            'context':{'default_employee_id':self.employee_id.id,'default_ticket_rate':self.ticket_allocation},
        }
