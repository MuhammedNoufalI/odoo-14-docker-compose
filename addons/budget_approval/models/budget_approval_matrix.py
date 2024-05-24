# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp

import pandas as pd


class BudgetApp(models.Model):
    _name = 'budget.approval.matrix'
    _description = 'Approval Matrix'
    name = fields.Char()
    general_approval_id = fields.Many2one(comodel_name="res.users", string="General Approval", required=False, )
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    date_from = fields.Date()
    date_to = fields.Date()

    company_id = fields.Many2one(comodel_name="res.company", string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    active = fields.Boolean(default=True)
    matrix_line_ids = fields.One2many(comodel_name="approval.matrix.line", inverse_name="budget_approval_id", string="",
                                      required=False, )
    limit = fields.Monetary('Limit')


    @api.constrains('date_from', 'date_to', 'matrix_line_ids')
    def _check_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise exceptions.ValidationError('Date From  must be < Date To')
        res = self.search([('id', '!=', self.id)])
        for rec in res:
            self.check_convergence(rec)

        # for line in self.matrix_line_ids:
        #     line.check_from_to_dates(line)


    def check_convergence(self, rec):
        for line in self:
            res = pd.date_range(rec.date_from, rec.date_to - timedelta(days=1), freq='d')
            res2 = pd.date_range(line.date_from, line.date_to - timedelta(days=1), freq='d')
            for date in res:
                if date in res2:
                    raise exceptions.ValidationError(
                        "There is a convergence in date range program with another budget approval !")

    @api.constrains('matrix_line_ids')
    def _check_matrix_line_ids(self):
        for rec in self:
            if len(rec.matrix_line_ids.mapped('categ_id')) != len(rec.matrix_line_ids):
                raise exceptions.ValidationError('Category cannot be repeated on lines')


class MatrixLine(models.Model):
    _name = 'approval.matrix.line'
    _description = 'Check Approval Matrix'

    budget_approval_id = fields.Many2one(comodel_name="budget.approval.matrix", required=False, )
    approval_id = fields.Many2one(comodel_name="res.users", string="Approval User", required=False, )
    categ_id = fields.Many2one(comodel_name="product.category", string="Category", required=False,
                               domain="[('is_budget_approval', '=', True)]", store=1)
    planned_amount = fields.Monetary(string="Planned Amount", required=False, )
    actual_amount = fields.Monetary(string="Actual Amount", required=False, compute='compute_actual_amount')
    remain_amount = fields.Monetary(string="Remain Amount", required=False, compute='compute_remain', )

    analytic_account = fields.Many2one('account.analytic.account', string="Analytic Account")
    budget_line_id = fields.Many2one('crossovered.budget.lines', string="Budget Line")

    budget_line_id_domain = fields.Char(
       compute="compute_budget_line_id_domain",
       readonly=True,
       store=False,)
    budget_date_from = fields.Date(related="budget_approval_id.date_from")
    budget_date_to = fields.Date(related="budget_approval_id.date_to")

    @api.depends('analytic_account')
    def compute_budget_line_id_domain(self):
        for rec in self:
            rec.budget_line_id_domain = json.dumps(
                [('analytic_account_id', '=', rec.analytic_account.id), ('date_from', '<=', rec.budget_approval_id.date_from), ('date_to', '>=', rec.budget_approval_id.date_to)], indent=4, sort_keys=True, default=str
            )

    @api.onchange('budget_line_id')
    def get_planned_amount(self):
        for rec in self:
            if rec.budget_line_id and rec.budget_line_id.planned_amount:
                rec.planned_amount = rec.budget_line_id.planned_amount
                rec.actual_amount = rec.budget_line_id.practical_amount

    @api.onchange('categ_id')
    def get_required_info(self):
        for rec in self:
            if rec.categ_id.budget_type:
                rec.type = rec.categ_id.budget_type
                if rec.categ_id.budget_type == 'percent':
                    rec.percent = rec.categ_id.budget_percentage

            if rec.categ_id.analytic_account:
                rec.analytic_account = rec.categ_id.analytic_account


    @api.depends('planned_amount', 'actual_amount')
    def compute_remain(self):
        for rec in self:
            rec.remain_amount = rec.planned_amount - rec.actual_amount

    def get_remain_amount(self):
        for rec in self:
             return rec.planned_amount - rec.actual_amount


    def compute_actual_amount(self):
        for rec in self:
            if rec.budget_approval_id:
                date_from = datetime.combine(rec.budget_approval_id.date_from, time.min)
                date_to = datetime.combine(rec.budget_approval_id.date_to, time.max)
                order_lines = self.env['purchase.order.line'].search(
                    [('order_id.state', '!=', 'cancel'), ('product_id.categ_id', '=', rec.categ_id.id),
                     ('order_id.date_order', '>=', date_from), ('order_id.date_order', '<=', date_to)])
                price_total = 0
                for line in order_lines:
                    price_total += line.currency_id._convert(line.price_total, rec.currency_id, rec.company_id,
                                                             line.order_id.date_order.date())
                rec.actual_amount = price_total
            else:
                rec.actual_amount = 0

    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name="res.company", string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    type = fields.Selection(string="Type", selection=[('fixed', 'Fixed'), ('percent', 'Percent'), ], required=False,
                            default='fixed')
    percent = fields.Float(string="Percent", required=False, )
    sales_amount = fields.Monetary(string="Sales Amount", required=False, compute='compute_sales_amount', store=True)

    date_from = fields.Date('Sales From')
    date_to = fields.Date('Sales To')

    def check_from_to_dates(self, line):
        print('HI')
        # if not self.env.user.has_group('budget_approval.allow_view_all_budget_lines'):
        if line.budget_approval_id and line.budget_approval_id.date_from and line.budget_approval_id.date_to:
            date_from = line.budget_approval_id.date_from - timedelta(days=31)
            date_to = line.budget_approval_id.date_to - timedelta(days=31)

            line.write({
                'date_from': date_from,
                'date_to': date_to
            })

            if line.categ_id.budget_type:
                line.write({
                    'type': line.categ_id.budget_type,
                })
                if line.categ_id.budget_type == 'percent':
                    line.write({
                        'percent': line.categ_id.budget_percentage,
                    })
        if line.date_from and line.date_to and line.date_from > line.date_to:
            raise exceptions.ValidationError('Sales From  must be < Sales To')

    def create(self, vals):
        res = super(MatrixLine, self).create(vals)
        for rec in res:
            self.check_from_to_dates(rec)
        return res

    # @api.constrains('date_from', 'date_to', 'budget_approval_id')
    # def _check_dates(self):
    #     for rec in self:
    #         if not self.env.user.has_group('budget_approval.allow_view_all_budget_lines'):
    #             print('havnot group')
    #             if rec.budget_approval_id and rec.budget_approval_id.date_from and rec.budget_approval_id.date_to:
    #                 date_from = rec.budget_approval_id.date_from - timedelta(days=7)
    #                 date_to = rec.budget_approval_id.date_to - timedelta(days=7)
    #                 print('dates is ', date_from, date_to)
    #                 rec.date_from = date_from
    #                 rec.date_to = date_to
    #         else:
    #             if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
    #                 raise exceptions.ValidationError('Sales From  must be < Sales To')

    @api.onchange('percent', 'sales_amount', 'type')
    def onchange_percent_sales_amount(self):
        for rec in self:
            if rec.type == 'percent':
                rec.planned_amount = rec.percent / 100 * rec.sales_amount

    @api.depends('date_from', 'date_to', 'type', 'categ_id')
    def compute_sales_amount(self):
        for rec in self:
            if rec.type == 'percent' and rec.date_from and rec.date_to:
                date_from = datetime.combine(rec.date_from, time.min)
                date_to = datetime.combine(rec.date_to, time.max)
                order_lines = self.env['sale.order.line'].search([
                    ('order_id.company_id', '=', rec.budget_approval_id.company_id.id),
                    ('order_id.state', '!=', 'cancel'),
                    ('product_id.categ_id', '=', rec.categ_id.id),
                    ('order_id.date_order', '>=', date_from),
                    ('order_id.date_order', '<=', date_to)
                 ])
                pos_lines = self.env['pos.order.line'].search([
                    ('order_id.company_id', '=', rec.budget_approval_id.company_id.id),
                    ('order_id.state', '!=', 'cancel'),
                    ('product_id.categ_id', '=', rec.categ_id.id),
                    ('order_id.date_order', '>=', date_from),
                    ('order_id.date_order', '<=', date_to)
                 ])
                price_total = 0
                for line in order_lines:
                    price_total += line.currency_id._convert(line.price_total, rec.currency_id, rec.company_id,
                                                             line.order_id.date_order.date())
                for line in pos_lines:
                    price_total += line.currency_id._convert(line.price_total, rec.currency_id, rec.company_id,
                                                             line.order_id.date_order.date())
                rec.sales_amount = price_total
                self.onchange_percent_sales_amount()
            else:
                rec.sales_amount = 0
