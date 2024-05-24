# -*- coding: utf-8 -*-
from odoo import models, fields, api,exceptions

class PurchaseOrederLine(models.Model):
    _inherit = 'product.category'

    is_budget_approval = fields.Boolean(string="Show in Budget Approval")
    budget_type = fields.Selection([('fixed', 'Fixed'), ('percent', 'Percent')], default='fixed', string="Budget Type")
    budget_percentage = fields.Integer(string="Budget Percentage")
    analytic_account = fields.Many2one('account.analytic.account', string="Analytic Account")