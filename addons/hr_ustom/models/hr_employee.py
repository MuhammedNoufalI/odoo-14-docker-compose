# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Employee(models.Model):
    _inherit = 'hr.employee'
    is_custom_shift = fields.Boolean('Custom Shift?')
