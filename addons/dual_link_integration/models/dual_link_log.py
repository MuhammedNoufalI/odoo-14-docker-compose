# -*- coding: utf-8 -*-

from odoo import fields, models, _
import logging
_logger = logging.getLogger('Dual Link API - product')


class DualLinkLogLines(models.Model):
    _name = 'dual.link.log.lines'
    _description = "Dual link log lines"

    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', string="Product")
    product_name = fields.Char(string="Product Name")
    format_name = fields.Char(string="Format Name")
    product_ref = fields.Char(string="Product Ref")
    log_id = fields.Many2one('dual.link.log', string="Log")
    qty = fields.Char(string="Quantity")
    price = fields.Char(string="Price")
    total_price = fields.Char(string="Total Price")
    is_cloned = fields.Boolean(string="Cloned")


class DualLinkLog(models.Model):
    _name = 'dual.link.log'
    _description = "Dual link log"

    name = fields.Char(string="Name")
    message = fields.Text(string="Message")
    is_order = fields.Boolean(string="Order")
    order_ids = fields.Many2many('pos.order', string="Orders")
    line_ids = fields.Many2many('pos.order.line', string="Lines")
    api_lines = fields.One2many(
        'dual.link.log.lines', 'log_id', string="API Lines")
    api_obj = fields.Text(string="Object of API")
    payment_obj = fields.Text(string="Payment of API")
