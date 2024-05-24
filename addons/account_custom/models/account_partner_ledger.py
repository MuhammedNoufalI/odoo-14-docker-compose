# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
class AccountPartnerLedger(models.AbstractModel):
    _inherit = 'account.partner.ledger'

    def _get_columns_name(self, options):
        res = super(AccountPartnerLedger, self)._get_columns_name(options)
        if res:
            res.insert(4, {'name': _('LPO Number')}, )
        return res

    @api.model
    def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
        res = super(AccountPartnerLedger, self)._get_report_line_move_line(options, partner, aml,
                                                                           cumulated_init_balance, cumulated_balance)
        if res.get('columns'):
            if aml.get('id'):
                moveid = self.env['account.move.line'].browse(aml.get('id')).move_id
                ref = moveid.partner_ref if moveid.move_type != 'entry' else ''
            columns = res.get('columns')
            columns.insert(3, {'name': ref}, )
            res.update({'columns': columns})
        return res


    def _get_report_line_total(self, options, initial_balance, debit, credit, balance):
        res = super(AccountPartnerLedger, self)._get_report_line_total(options, initial_balance, debit, credit, balance)
        columns = res.get('columns')
        new_columns = []
        new_columns.append({'name': ''})
        for col in columns:
            new_columns.append(col)
        res.update({'columns': new_columns})
        return res

    @api.model
    def _get_report_line_partner(self, options, partner, initial_balance, debit, credit, balance):
        res = super(AccountPartnerLedger, self)._get_report_line_partner(options, partner, initial_balance, debit,
                                                                         credit, balance)
        columns = res.get('columns')
        new_columns = []
        new_columns.append({'name': ''})
        for col in columns:
            new_columns.append(col)
        res.update({'columns': new_columns})
        return res


