# # -*- coding: utf-8 -*-
#
# from collections import namedtuple
# import json
# import time
#
# from odoo.fields import Date, Datetime
# from itertools import groupby
# from odoo import api, fields, models, _
# from datetime import datetime,date
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
# from odoo.tools.float_utils import float_compare, float_is_zero, float_round
# from odoo.exceptions import UserError
# from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
#
#
# class PosSession(models.Model):
#     _inherit = 'pos.session'
#
#     bank_move = fields.Many2one('account.move')
#     def _create_account_move(self):
#         super(PosSession, self)._create_account_move()
#
#         bank_payments = self.order_ids.payment_ids.filtered(lambda x:x.payment_method_id.is_bank_count==True)
#
#         if bank_payments:
#             bank_journal = bank_payments[0].payment_method_id.bank_journal_id
#             amount = sum(bank_payments.mapped('amount'))
#         my_list = []
#         my_list.append((0, 0, {
#             'name': str('account rece'),
#             'account_id': bank_payments[0].payment_method_id.receivable_account_id.id,
#             'credit': amount,
#         }))
#         my_list.append((0, 0, {
#             'name': str('Bank'),
#             'account_id': bank_journal.default_credit_account_id.id,
#             'debit': amount,
#         }))
#         move_id = self.env['account.move'].create({
#             'ref': str('Bank Reconcile'),
#             'journal_id': bank_journal.id,
#             'line_ids': my_list,
#             'type': 'entry'
#
#         })
#         move_id.action_post()
#         self.bank_move = move_id.id
#         aml = move_id.line_ids.filtered(lambda x:x.account_id == bank_payments[0].payment_method_id.receivable_account_id)
#         aml2 =self.move_id.line_ids.filtered(lambda x:x.account_id == bank_payments[0].payment_method_id.receivable_account_id and x.debit==amount)
#         aml3 = aml +aml2
#         aml3.reconcile()
#
#     def _get_related_account_moves(self):
#         res = super(PosSession, self)._get_related_account_moves()
#         res |= self.bank_move
#         return res




