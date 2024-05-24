# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    credit_note_id = fields.Many2one(comodel_name="account.move", string="Credit Note", required=False, )


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        res = super(StockReturnPicking, self).create_returns()
        # if self.env.context.get('active_id', False):
        #     picking = self.env["stock.picking"].browse(self.env.context['active_id'])
        credit_note_lines =[]
        sale_order = self.picking_id.sale_id
        purchase_order = self.picking_id.purchase_id
        for rec in self.product_return_moves:
            unit_price = 0.0
            if sale_order:
                for line in sale_order.order_line.filtered(lambda x:x.product_id == rec.product_id):
                    unit_price = line.price_unit
            elif purchase_order:
                for line in purchase_order.order_line.filtered(lambda x:x.product_id == rec.product_id):
                    unit_price = line.price_unit
            else:
                unit_price = rec.product_id.lst_price
            credit_note_lines.append((0,0,{
                'product_id':rec.product_id.id,
                'name':rec.product_id.name,
                'quantity':rec.quantity,
                'price_unit':unit_price,
                'is_returned_trnasfer':True,
            }))
        self.picking_id.credit_note_id.update({'invoice_line_ids':credit_note_lines})
        self.picking_id.credit_note_id.update({'state':'transferred'})
        return res
