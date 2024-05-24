# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class SaleLine(models.Model):
    _inherit = 'sale.order.line'
    discount_amt = fields.Float('Discount Amount',compute='compute_discount_amt', inverse="_inverse_discount_amt",store=True,)

    @api.onchange('discount_amt','product_uom_qty','price_unit')
    def _inverse_discount_amt(self):
        for rec in self:
            total = rec.product_uom_qty * rec.price_unit
            if total:
                rec.discount = (rec.discount_amt / total) * 100
    # @api.onchange('discount')
    # def onchange_discount(self):
    #     for rec in self:
    #         rec.discount_amt = rec.discount /100 *(rec.product_uom_qty * rec.price_unit)
    @api.depends('discount','product_uom_qty','price_unit')
    def compute_discount_amt(self):
        for rec in self:
            rec.discount_amt = rec.discount / 100 * (rec.product_uom_qty * rec.price_unit)
class Sale(models.Model):
    _inherit = 'sale.order'


    def _prepare_invoice(self):
        res = super(Sale, self)._prepare_invoice()
        res.update({
            'partner_ref': self.client_order_ref
        })
        return res

