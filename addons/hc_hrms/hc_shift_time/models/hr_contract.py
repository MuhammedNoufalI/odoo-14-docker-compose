# -*- coding: utf-8 -*-

from odoo import fields, models
import time
from datetime import datetime, timedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'

    is_overtime_eligible = fields.Boolean(string="Is OverTime Eligible")
