# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    yeild_wastage = fields.Float(string="Wastage(%)", required=False, )
    yeild_wastage_amount = fields.Float(string="Wastage", required=False, )

    @api.onchange('product_id')
    def get_wastage_info(self):
        for rec in self:
            rec.yeild_wastage = rec.product_id.yeild_wastage
            rec.yeild_wastage_amount = rec.yeild_wastage * rec.product_qty / 100

