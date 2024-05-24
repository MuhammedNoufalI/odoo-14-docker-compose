# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models,_
from odoo.tools.float_utils import float_round, float_is_zero


class sale_order_line_inherit(models.Model):
	_inherit = "sale.order.line"

	@api.depends('qty_delivered','product_id','product_uom_qty','price_subtotal',
		'discount','tax_id')
	def _compute_return_qty(self):
		for line in self:
			in_picking = self.env['stock.move'].search([
				('sale_line_id','=',line.id),
				('picking_id.state','=','done'),
				('picking_id.picking_type_code','=','incoming')])

			out_picking = self.env['stock.move'].search([
				('sale_line_id','=',line.id),
				('picking_id.state','=','done'),
				('picking_id.picking_type_code','=','outgoing')])

			in_qty = sum(in_picking.mapped('quantity_done')) 
			out_qty = sum(out_picking.mapped('quantity_done')) 

			tax_amount = tax_per = discount_amount = product_return_qty = return_rate = 0.0

			return_qty = out_qty - in_qty
			product_return_qty =return_qty

			if return_qty > 0.0:
				rate =  (line.qty_delivered - return_qty)/(return_qty)
				product_return_qty = rate/100
			
			cost = line.product_id.standard_price * line.product_uom_qty
			profit = line.price_subtotal - cost
			profitability = 0
			if profit != 0 and cost != 0 :
				profitability = profit/cost
				
			if line.order_id.amount_total < 0 :
				return_rate = product_return_qty = 0.0
				profitability = - abs(profitability)

			if line.tax_id and not line.discount:
				tax_amount =  line.price_total - (line.product_uom_qty * line.price_unit)
			if line.tax_id and line.discount:
				tax_amount = (line.price_total - (line.product_uom_qty * line.price_unit)) +line.discount_amount

			if tax_amount != 0 and (line.price_unit * line.product_uom_qty) != 0 :
				tax_per = (line.tax_amount  * 100)/(line.price_unit * line.product_uom_qty)

			discount_amount =((line.price_unit * line.discount)/100) * line.product_uom_qty
			
			line.update({
				'return_rate' : return_rate,
				'return_qty' : product_return_qty,
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
	profitability = fields.Float(string="Profitability",compute="_compute_return_qty",store=True )

	order_place_date = fields.Datetime(string="Order Date", related='order_id.date_order', store=True)

	discount_amount = fields.Float(string="Dis. Amount",compute="_compute_return_qty",store=True)
	tax_per = fields.Float(string="Tax %", compute="_compute_return_qty",store=True)
	tax_amount = fields.Float(string="Tax amount", compute="_compute_return_qty",store=True)

			
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
