# -*- coding: utf-8 -*-

from odoo import models, fields


class HcTimeOffType(models.Model):
    _inherit = "hr.leave.type"

    pay_type = fields.Selection([('paid', 'Paid'),('half_paid', 'Half Paid'), ('unpaid', 'Unpaid')],
                                default='paid')
    include_to_net_working = fields.Boolean(string="Include to Net Working Days", help='Include to the Net Working Days of the Employee')
    is_compensatory_timeoff_type = fields.Boolean(string="Is Compensatory")

