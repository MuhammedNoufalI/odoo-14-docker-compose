# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AssetGroup(models.Model):
    _name = 'asset.group'
    _rec_name = 'name'
    _description = ''

    name = fields.Char(string="Description", required=True, )
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True, )

