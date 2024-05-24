# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero


class POSOrderLineInherit(models.Model):
	_inherit = "pos.order.line"

	@api.depends('qty','product_id','state','price_subtotal','discount', 'price_unit', 'tax_ids', 'tax_ids_after_fiscal_position')
	def _compute_return_qty(self):
		for line in self:
			pos_orders = self.env['pos.order'].sudo().search([
				('pos_reference','=',line.order_id.pos_reference),
				('id','!=',line.order_id.id),
				('state','not in',['draft','cancel']),
				('amount_total','<',0),
			])

			tax_amount = tax_per = discount_amount = product_return_qty = return_rate = 0.0
			
			lines = pos_orders.mapped('lines').filtered(lambda x : x.product_id == line.product_id)
			return_qty = sum(line.qty for line in lines)
			if return_qty:
				rate =  (line.qty - return_qty)/(return_qty)
				product_return_qty = abs(return_qty)
				return_rate = rate/100

			cost = (line.product_id.standard_price * line.qty)
			profit = line.price_subtotal  - cost
			profitability = 0
			if profit != 0 and cost != 0 :
				profitability = profit/cost

			if line.order_id.amount_total < 0 :
				return_rate = product_return_qty = 0.0
				profitability = - abs(profitability)

			if line.tax_ids_after_fiscal_position and not line.discount:
				tax_amount =  line.price_subtotal_incl - (line.qty * line.price_unit)
			if line.tax_ids_after_fiscal_position and line.discount:
				tax_amount = (line.price_subtotal_incl - (line.qty * line.price_unit)) +line.discount_amount

			if tax_amount != 0 and (line.price_unit * line.qty) != 0 :
				tax_per = (tax_amount  * 100)/(line.price_unit * line.qty)
			discount_amount =((line.price_unit * line.discount)/100) * line.qty
			
			line.update({
				'return_rate' : return_rate,
				'return_qty' : product_return_qty,
				'deliver_qty' : line.qty,
				'product_cost' : cost,
				'profit' : profit,
				'profitability' : float_round(profitability, precision_rounding=line.order_id.pricelist_id.currency_id.rounding),
				'tax_amount' : tax_amount,
				'tax_per' : tax_per,
				'discount_amount' : discount_amount,
			})	


	product_cost = fields.Float(string="Cost",compute="_compute_return_qty",store=True)
	profit = fields.Float(string="Profit",compute="_compute_return_qty",store=True)
	return_qty = fields.Float(string="Return Quantity",compute="_compute_return_qty",store=True,default=0.0)
	return_rate = fields.Float(string="Return Rate",compute="_compute_return_qty",store=True)
	profitability = fields.Float(string="Profitability",compute="_compute_return_qty",store=True)
	deliver_qty = fields.Float(string="Deliver Qty",compute="_compute_return_qty",store=True)
	
	state = fields.Selection(string="State",related="order_id.state",store=True)
	order_date = fields.Datetime(string="Order Date",related="order_id.date_order",store=True)
	
	discount_amount = fields.Float(string="Dis. Amount",compute="_compute_return_qty",store=True)
	tax_per = fields.Float(string="Tax %", compute="_compute_return_qty",store=True)
	tax_amount = fields.Float(string="Tax amount", compute="_compute_return_qty",store=True)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: