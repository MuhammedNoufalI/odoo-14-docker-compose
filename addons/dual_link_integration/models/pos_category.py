# -*- coding: utf-8 -*-

from odoo import fields, models, _
import logging
_logger = logging.getLogger('Dual Link API - pos_category')


class InheritPosCategory(models.Model):
    _inherit = 'pos.category'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    company_id = fields.Many2one('res.company', string="Company", related="dual_link_id.company_id", store=1)

class InheritProductCategory(models.Model):
    _inherit = 'product.category'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    company_id = fields.Many2one('res.company', string="Company", related="dual_link_id.company_id", store=1)
