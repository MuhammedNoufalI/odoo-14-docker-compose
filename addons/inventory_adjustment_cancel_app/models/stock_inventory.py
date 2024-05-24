# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.tools.misc import OrderedSet



class StockInventory(models.Model):
	_inherit = "stock.inventory"

	def cancel_stock_inventory(self):
		for move in self :
			move.mapped('move_ids').delete_order()
			self.write({'state':'cancel'})
		return


class StockMove(models.Model):
	_inherit = 'stock.move'


	def draft_order(self):
		for order in self :
			order.cancel_order()
			for move in order.move_line_ids:
				move.write({'state':'draft'})

	def delete_order(self):
		for order in self :
			order.draft_order()
			# order.sudo().unlink()

	def cancel_order(self):
		for move in self:
			move._action_cancel()
			if move.stock_valuation_layer_ids:
				move.stock_valuation_layer_ids.sudo().unlink()
			for line in move.move_line_ids:                                  
				if move.location_id.usage == 'inventory':
					if not line.lot_id:
						incoming_quant = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id','=',move.location_dest_id.id)])
						if incoming_quant:
							old_qty = incoming_quant[0].quantity
							incoming_quant[0].quantity = old_qty - move.product_uom_qty
						incoming_customer_quant = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id)])
						if incoming_customer_quant:
							old_qty = incoming_customer_quant[0].quantity
							incoming_customer_quant[0].quantity = old_qty + move.product_uom_qty
					else:
						if line.product_id.tracking == 'lot':
							incoming_quant = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id','=',move.location_dest_id.id),('lot_id','=',line.lot_id.id)])
							incoming_customer_quant = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id),('lot_id','=',line.lot_id.id)])
							if incoming_quant:
								old_qty = incoming_quant[0].quantity
								incoming_quant[0].quantity = old_qty - move.product_uom_qty
							if incoming_customer_quant:
								old_qty = incoming_customer_quant[0].quantity
								incoming_customer_quant[0].quantity = old_qty + move.product_uom_qty
						else:
							incoming_quant = self.env['stock.quant'].sudo().search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id),('lot_id','=',line.lot_id.id)])
							for lot in incoming_quant:
								old_qty = lot.quantity
								lot.unlink()
								vals = { 'product_id' :move.product_id.id,
										 'location_id':move.location_dest_id.id,
										 'quantity': old_qty,
										 'lot_id':line.lot_id.id,
									   }
								test = self.env['stock.quant'].sudo().create(vals)
			if move.mapped('account_move_ids'):
				for account_move in  move.mapped('account_move_ids'):
					account_move.button_cancel()
					# account_move.sudo().unlink()
		return True


	def _do_unreserve(self):
		moves_to_unreserve = OrderedSet()
		for move in self:
			if self.user_has_groups('inventory_adjustment_cancel_app.group_cancel_inventory'):
				if move.state == 'cancel':
					# We may have cancelled move in an open picking in a "propagate_cancel" scenario.
					continue
				if move.state == 'done':
					if move.scrapped:
						# We may have done move in an open picking in a scrap scenario.
						continue
			else:
				if move.state == 'cancel' or (move.state == 'done' and move.scrapped):
					# We may have cancelled move in an open picking in a "propagate_cancel" scenario.
					# We may have done move in an open picking in a scrap scenario.
					continue
				elif move.state == 'done':
					raise UserError(_("You cannot unreserve a stock move that has been set to 'Done'."))
			moves_to_unreserve.add(move.id)
		moves_to_unreserve = self.env['stock.move'].browse(moves_to_unreserve)

		ml_to_update, ml_to_unlink = OrderedSet(), OrderedSet()
		moves_not_to_recompute = OrderedSet()
		for ml in moves_to_unreserve.move_line_ids:
			if ml.qty_done:
				ml_to_update.add(ml.id)
			else:
				ml_to_unlink.add(ml.id)
				moves_not_to_recompute.add(ml.move_id.id)
		ml_to_update, ml_to_unlink = self.env['stock.move.line'].browse(ml_to_update), self.env['stock.move.line'].browse(ml_to_unlink)
		moves_not_to_recompute = self.env['stock.move'].browse(moves_not_to_recompute)

		ml_to_update.write({'product_uom_qty': 0})
		ml_to_unlink.unlink()
		# `write` on `stock.move.line` doesn't call `_recompute_state` (unlike to `unlink`),
		# so it must be called for each move where no move line has been deleted.
		(moves_to_unreserve - moves_not_to_recompute)._recompute_state()
		return True


	def _action_cancel(self):
		moves_to_cancel = self.filtered(lambda m: m.state != 'cancel')
		# self cannot contain moves that are either cancelled or done, therefore we can safely
		# unlink all associated move_line_ids
		moves_to_cancel._do_unreserve()

		for move in moves_to_cancel:
			siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
			if move.propagate_cancel:
				# only cancel the next move if all my siblings are also cancelled
				if all(state == 'cancel' for state in siblings_states):
					move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
			else:
				if all(state in ('done', 'cancel') for state in siblings_states):
					move.move_dest_ids.write({'procure_method': 'make_to_stock'})
					move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
		self.write({
			'state': 'cancel',
			'move_orig_ids': [(5, 0, 0)],
			'procure_method': 'make_to_stock',
		})
		return True


class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'


	def unlink(self):
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		for ml in self:
			if ml.state in ('done'):
				raise UserError(_('You can not delete product moves if the picking is done. You can only correct the done quantities.'))
			# Unlinking a move line should unreserve.
			if ml.product_id.type == 'product' and not ml._should_bypass_reservation(ml.location_id) and not float_is_zero(ml.product_qty, precision_digits=precision):
				self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
		moves = self.mapped('move_id')
		res = super(StockMoveLine, self).unlink()
		if moves:
			# Add with_prefetch() to set the _prefecht_ids = _ids
			# because _prefecht_ids generator look lazily on the cache of move_id
			# which is clear by the unlink of move line
			moves.with_prefetch()._recompute_state()
		return res