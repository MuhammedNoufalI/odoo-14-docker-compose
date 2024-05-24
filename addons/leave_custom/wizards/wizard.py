# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from openerp.exceptions import Warning
from datetime import datetime
import pytz
import json
from odoo.tools import date_utils
class StockCardWizard(models.TransientModel):

    _name = "allocation.post"

    post = fields.Boolean()
    date_start = fields.Datetime(
        string="Start date",
        required=False)

    date_end = fields.Datetime(
        string="End date",
        required=False)
    period = fields.Integer()
    allocation_id = fields.Many2one(
        string="Allocation",
        comodel_name="hr.leave.allocation",
        required=False)


    def post_close(self):
        if not self.post:
            self.allocation_id.active=False
        allocation_id = self.allocation_id
        allocation_values = {
            'name':  'posted from'+allocation_id.name ,
            'holiday_status_id': allocation_id.holiday_status_id.id,
            'employee_id': allocation_id.employee_id.id,
            'number_of_days': self.period,
            'date_from': self.date_start,
            'date_to': self.date_end,
        }
        allocations = self.env['hr.leave.allocation'].create(allocation_values)
        self.allocation_id.active = False