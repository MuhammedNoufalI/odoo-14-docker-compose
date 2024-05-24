# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'
    _description = 'HR Work Entry Type'

    is_break = fields.Boolean(string="Is Break")


