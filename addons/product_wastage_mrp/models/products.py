# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Products(models.Model):
    _inherit = 'product.template'

    yeild_wastage = fields.Float(string="Wastage", required=False, )

class ProductProduct(models.Model):
    _inherit = 'product.product'

    yeild_wastage = fields.Float(string="Wastage", required=False, )
