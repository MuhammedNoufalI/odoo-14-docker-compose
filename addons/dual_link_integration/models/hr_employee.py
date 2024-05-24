# -*- coding: utf-8 -*-

from odoo import fields, models, _
import logging
_logger = logging.getLogger('Dual Link API - hr_employee')


class InheritPosCategory(models.Model):
    _inherit = 'hr.employee'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")

    pin_code = fields.Char(string="Pincode")
    dl_password = fields.Char(string="Password")