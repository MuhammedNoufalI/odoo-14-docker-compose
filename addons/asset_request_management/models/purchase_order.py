# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = ''

    asset_request_id = fields.Many2one(comodel_name="asset.request", string="Asset Request", required=False, )

