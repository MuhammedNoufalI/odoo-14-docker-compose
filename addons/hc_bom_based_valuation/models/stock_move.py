# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_dest_account(self, accounts_data):
        if not self.bom_line_id:
            return super()._get_dest_account(accounts_data)
        else:
            bom_account = self.bom_line_id.bom_id.product_tmpl_id.with_company(self.company_id)._get_product_accounts()[
                'expense']
            return self.location_dest_id.valuation_out_account_id.id or bom_account.id

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, description):
        """ Overridden from stock_account to update the label with the bom parent product id
        """
        self.ensure_one()
        res = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
                                                                    debit_account_id, credit_account_id, description)
        if self.bom_line_id:
            bom_parent_id = self.bom_line_id.bom_id.product_tmpl_id
            res['debit_line_vals']['name'] = res['debit_line_vals']['name'] + ' | ' + str(bom_parent_id.name)
        return res
