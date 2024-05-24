# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Products(models.Model):
    _inherit = 'product.template'

    _sql_constraints = [
        ('default_code_uniq', 'UNIQUE (default_code)', 'Internal Reference is Unique')
    ]