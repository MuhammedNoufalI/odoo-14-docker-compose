# -*- coding: utf-8 -*-
import datetime
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import ValidationError,UserError


class payslips(models.Model):
    _inherit = 'hr.payslip'


    payment_count = fields.Integer(string="payments", compute='get_payments')
    statement_count = fields.Integer(string="statement", compute='get_payments')
    total_net_salary = fields.Monetary('total net',compute='get_total_net')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    state = fields.Selection(selection_add=[('paid','Paid')] )


    @api.depends('total_net_salary','line_ids')
    def get_total_net(self):
        for pay in self:
            net_salary = 0.0
            for rec in pay.line_ids:
                if rec.code == 'NET':
                    net_salary += round(rec.total)
            pay.total_net_salary = net_salary



    @api.depends('payment_count','statement_count')
    def get_payments(self):
        statements_count = 0
        self.payment_count = self.env['account.payment'].search_count([('payslip_id', '=', self.id)])
        account_statements = self.env['account.bank.statement'].search([('journal_id', '=', self.employee_id.journal_id.id)])
        for rec in account_statements:
            for line in rec.line_ids:
                if line.payslip_id.id == self.id:
                    statements_count += 1
        self.statement_count = statements_count

    def open_statements_screen(self):
        statements = []
        account_statements = self.env['account.bank.statement'].search(
            [('journal_id', '=', self.employee_id.journal_id.id)])
        for rec in account_statements:
            for line in rec.line_ids:
                if line.payslip_id.id == self.id:
                   statements.append(rec.id)
        return {
            'name': _('Statements'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.bank.statement',
            'target': 'current',
            'domain': [('id', 'in', statements)],

        }

    def open_payment_screen(self):


        view = self.env.ref('account.action_account_payments')
        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'target': 'new',
            # 'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_payslip_id': self.id,'default_payment_type': 'outbound', 'default_partner_type': 'supplier',
                         'default_communication': str(self.name),
                        'default_partner_id': self.employee_id.address_home_id.id,'default_journal_id': self.employee_id.journal_id.id }
        }


class Payment_payslip(models.Model):
    _inherit = 'account.payment'

    payslip_id = fields.Many2one(comodel_name="hr.payslip",string="Payslip ", required=False,)

    def post(self):
        res = super(Payment_payslip, self).post()
        if self.payslip_id:
            payslips = self.env['hr.payslip'].browse(self._context.get('active_id', []))
            payslips.state = 'paid'
        return res




