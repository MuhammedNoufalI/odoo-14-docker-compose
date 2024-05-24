# -*- coding: utf-8 -*-

import math

from datetime import datetime, timedelta, time, date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import format_time
from odoo.addons.resource.models.resource import float_to_time
from odoo.exceptions import UserError, ValidationError


class HrContracts(models.Model):
    _inherit = "hr.contract"

    name = fields.Char('Contract Reference', required=True, copy=False)

    @api.onchange('resource_calendar_id')
    def onchange_resource_calendar_id(self):
        # super(HrContracts, self).onchange_resource_calendar_id()
        if self.resource_calendar_id:
            self.employee_id.resource_calendar_id = self.resource_calendar_id

    def unlink(self):
        res = super(HrContracts, self).unlink()
        user = self.env.user
        if not user.has_group('hc_planning_customization.high_management_user'):
            raise UserError(
                _("You are not allowed to delete this record,Only High Management users can delete this record"))

        return res

    @api.model
    def update_state(self):
        contracts = self.search([
            ('state', '=', 'open'), ('kanban_state', '!=', 'blocked'),
            '|',
            '&',
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=7))),
            ('date_end', '>=', fields.Date.to_string(date.today() + relativedelta(days=1))),
            '&',
            ('visa_expire', '<=', fields.Date.to_string(date.today() + relativedelta(days=60))),
            ('visa_expire', '>=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        ])
        for contract in contracts:
            contract.with_context(mail_activity_quick_update=True).activity_schedule(
                'mail.mail_activity_data_todo', contract.date_end,
                _("The contract of %s is about to expire.", contract.employee_id.name),
                user_id=contract.hr_responsible_id.id or self.env.uid)

        contracts.write({'kanban_state': 'blocked'})

        self.search([
            ('state', 'in', ['open', 'draft']),
            '|',
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
            ('visa_expire', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        ]).write({
            'state': 'close'
        })

        self.search([('state', '=', 'draft'), ('kanban_state', '=', 'done'),
                     ('date_start', '<=', fields.Date.to_string(date.today())), ]).write({
            'state': 'open'
        })

        contract_ids = self.search([('date_end', '=', False), ('state', '=', 'close'), ('employee_id', '!=', False)])
        # Ensure all closed contract followed by a new contract have a end date.
        # If closed contract has no closed date, the work entries will be generated for an unlimited period.
        for contract in contract_ids:
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('state', 'not in', ['cancel', 'new']),
                ('date_start', '>', contract.date_start)
            ], order="date_start asc", limit=1)
            if next_contract:
                contract.date_end = next_contract.date_start - relativedelta(days=1)
                continue
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('date_start', '>', contract.date_start)
            ], order="date_start asc", limit=1)
            if next_contract:
                contract.date_end = next_contract.date_start - relativedelta(days=1)

        return True
