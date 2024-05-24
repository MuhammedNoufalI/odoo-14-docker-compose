# -*- coding: utf-8 -*-

from odoo import fields, models, _
import logging
_logger = logging.getLogger('Dual Link API - account_tax')


class InheritAccountTax(models.Model):
    _inherit = 'account.tax'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    main_id = fields.Many2one('account.tax', string="Main Tax")
    subtax_ids = fields.One2many('account.tax', 'main_id', string="Sub Taxes")
