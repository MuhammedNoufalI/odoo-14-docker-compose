# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
        lose_account_id = gain_account_id = False
        if self._context.get('from_adjust') or self._context.get('single_product'):
            if qty < 0:
                lose_account_id = self.product_id.categ_id.account_lose_id.id
            if qty > 0:
                gain_account_id = self.product_id.categ_id.account_gain_id.id

        return super(StockMove, self)._prepare_account_move_line(qty, cost, gain_account_id or credit_account_id,
                                                                 lose_account_id or debit_account_id, description)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def post_inventory(self):
        # The inventory is posted as a single step which means quants cannot be moved from an internal location to
        # another using an inventory as they will be moved to inventory loss, and other quants will be created to the
        # encoded quant location. This is a normal behavior as quants cannot be reuse from inventory location (users
        # can still manually move the products before/after the inventory if they want).
        self.mapped('move_ids').filtered(lambda move: move.state != 'done').with_context(
            from_adjust=True)._action_done()


class ProductCategory(models.Model):
    _inherit = 'product.category'
    account_gain_id = fields.Many2one('account.account', company_dependent=True,
                                      domain="['&', ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
                                      string="Gain Account")
    account_lose_id = fields.Many2one('account.account', company_dependent=True,
                                      string="Lose Account",
                                      domain="['&', ('deprecated', '=', False), ('company_id', '=', current_company_id)]")
