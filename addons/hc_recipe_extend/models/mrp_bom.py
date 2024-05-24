from odoo import models, fields, api, _


class MrpBom(models.Model):
    _inherit = 'mrp.bom.line'

    recipe_qty = fields.Char("Recipe Qty")
