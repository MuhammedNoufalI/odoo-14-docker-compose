# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_gratuity = fields.Boolean(string="Available in Gratuity")