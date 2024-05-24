# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        if self.purchase_id and self.env.context.get('cancel_backorder'):
            for purchase_line in self.purchase_id.order_line:
                qty_rec = 0
                for move in purchase_line.move_ids:
                    qty_rec += move.quantity_done
                purchase_line.product_qty = qty_rec
        if self.sale_id and self.env.context.get('cancel_backorder'):
            for sale_line in self.sale_id.order_line:
                qty_rec = 0
                for move in sale_line.move_ids:
                    qty_rec += move.quantity_done
                sale_line.product_uom_qty = qty_rec
        return super(StockPicking, self)._action_done()

    def action_update_effective_date(self):
        if self.scheduled_date:
            self.date_done = self.scheduled_date
            for move in self.move_ids_without_package:
                move.date = self.scheduled_date
                valuation_records = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)])
                for valuation_record in valuation_records:
                    valuation_record.create_date = self.scheduled_date
                stock_quants = self.env['stock.quant'].search([('lot_id', 'in', move.lot_ids)])
                for stock_quant in stock_quants:
                    stock_quant.create_date = self.scheduled_date
            for move_line in self.move_line_ids:
                move_line.date = self.scheduled_date
