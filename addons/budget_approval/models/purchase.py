# -*- coding: utf-8 -*-
from odoo import models, fields, api,exceptions

class PurchaseOrederLine(models.Model):
    _inherit = 'purchase.order.line'
    categ_id = fields.Many2one('product.category',related='product_id.categ_id',store=True)
    remain_amount = fields.Monetary(string="Remain Amount", required=False,compute='compute_remain',)

    @api.depends('categ_id')
    def compute_remain(self):
        for rec in self:
            obj = self.env['approval.matrix.line'].sudo().search([('categ_id','=',rec.categ_id.id), ('budget_date_from', '<=', rec.date_order.date()), ('budget_date_to', '>=', rec.date_order.date()), ],limit=1)
            rec.remain_amount = obj.remain_amount
            rec.account_analytic_id = rec.categ_id.analytic_account.id

    def get_remain_amount(self):
        for rec in self:
            obj = self.env['approval.matrix.line'].sudo().search([('categ_id','=',rec.categ_id.id), ('budget_date_from', '<=', rec.date_order.date()), ('budget_date_to', '>=', rec.date_order.date()), ],limit=1)
            return obj.remain_amount


class PurchaseOreder(models.Model):
    _inherit = 'purchase.order'
    approval_user_id = fields.Many2one('res.users',string='approval User')
    login_is_approval = fields.Boolean(compute='check_login_is_approval',)
    def send_email(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        body = 'Purchase #:{} Confirmed by {}'.format(self.name,self.env.user.name) + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
            base_url) + str(
            self.id) + '&view_type=form&model=purchase.order&action=" style="font-weight: bold">' + str(
            self.name) + '</a>'
        if self.create_uid.email:
            mails_send = self.env['mail.mail'].create({
                'subject': 'Due Date Reminder Invoice ',
                'body_html': '<p><strong>Dear ' + str(self.create_uid.name) + '</strong></p><br></br>' + str(body),
                'notification': True,
                'auto_delete': True,
                'email_to': self.create_uid.email,
                'message_type': 'email',
            })

            mails_send.send()
    def button_approve(self,force=False):
        res = super(PurchaseOreder, self).button_approve(force)
        if self.env.user != self.create_uid:

            summary = 'Purchase #:{} Confirmed by {}'.format(self.name,self.env.user.name)
            self.env['user.notify'].create_activity(self, self.create_uid, summary)
            self.env['user.notify'].send_user_notification(self.create_uid, self,'Purchase Confirmation', summary)
        return res
    def check_login_is_approval(self):
        for rec in self:
            if  rec.approval_user_id:
                if self.env.user == rec.approval_user_id:
                    rec.login_is_approval = True
                else:
                    rec.login_is_approval = False
            else:
                rec.login_is_approval = True

    def check_budget_approval_levels(self,vals):
        for rec in self:
            matrix = []
            categs = rec.order_line.mapped('categ_id')
            matrix_lines = self.env['approval.matrix.line'].sudo().search([('categ_id','in',categs.ids),('budget_approval_id.date_to','>=',rec.date_order.date()),('budget_approval_id.date_from','<=',rec.date_order.date())])
            budget_approval_id = matrix_lines.mapped('budget_approval_id')
            if matrix_lines:
                categ_totals = rec.get_categ_lines_total(categs,rec.order_line)
                for categ in categs:
                    matrix_line = rec.get_matrix_line(matrix_lines, categ)
                    categ_total = rec.get_categ_total(categ,categ_totals)
                    if matrix_line.remain_amount < categ_total:
                        matrix.append(matrix_line.approval_id)
                if matrix:
                    if  len(list(set(matrix))) != 1:
                        rec.set_appove_user(budget_approval_id.general_approval_id,vals)
                    else:
                        # if rec.amount_total >= budget_approval_id.limit and budget_approval_id.limit:
                        #     rec.set_appove_user(budget_approval_id.general_approval_id,vals)
                        # if rec.remain_amount < 0:
                        #     rec.set_appove_user(matrix_lines[0].approval_id,vals)
                        # else:
                        #     rec.with_context(esc=True).approval_user_id = False

                        for line in rec.order_line:
                            print(line.get_remain_amount())
                            if line.get_remain_amount() < 0 and rec.amount_total < budget_approval_id.limit and budget_approval_id.limit:
                                rec.set_appove_user(matrix_lines[0].approval_id,vals)
                            elif rec.amount_total >= budget_approval_id.limit and budget_approval_id.limit:
                                rec.set_appove_user(budget_approval_id.general_approval_id,vals)
                            else:
                                rec.with_context(esc=True).approval_user_id = False
                else:
                    rec.with_context(esc=True).approval_user_id = False
            else:
                rec.with_context(esc=True).approval_user_id = False

    def set_appove_user(self,user,vals):
        self.with_context(esc=True).approval_user_id = user.id
        if vals.get('state') not in ('cancel','draft'):
            summary = 'Purchase Quotaion #:{} Need Your Approve'.format(self.name)
            self.env['user.notify'].create_activity(self,user,summary )

    def get_matrix_line(self,matrix_lines,categ):
        for line in matrix_lines:
            if line.categ_id == categ:
                return line
        return self.env['approval.matrix.line']
    def get_categ_lines_total(self,categs,lines):
        totals = []

        for categ in categs:
            price_total = 0
            for line in lines:
                if line.categ_id == categ:
                    price_total += line.price_total
            totals.append((categ.id,price_total))
        return totals
    def get_categ_total(self,categ,totals):
        for (x,y) in totals:
            if x == categ.id:
                return y
    @api.model
    def create(self,vals):
        new_record = super(PurchaseOreder, self).create(vals)

        new_record.check_budget_approval_levels(vals)
        return new_record
    def write(self,vals):
        super(PurchaseOreder, self).write(vals)
        if not self.env.context.get('esc'):
            if vals.get('order_line'):
                flag = False
                for ar in vals.get('order_line'):
                    if ar[2]:
                        if any('product_qty' in x or 'price_unit' in x or 'product_id' in x for x in ar[2]):
                            flag = True
                if flag:
                    self.check_budget_approval_levels(vals)
        return True

