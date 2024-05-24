# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # def _create_payments(self):
    #     self.ensure_one()
    #     batches = self._get_batches()
    #
    #     to_reconcile = []
    #     if self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment):
    #         payment_vals = self._create_payment_vals_from_wizard()
    #         payment_vals_list = [payment_vals]
    #         to_reconcile.append(batches[0]['lines'])
    #     else:
    #         # Don't group payments: Create one batch per move.
    #         if not self.group_payment:
    #             new_batches = []
    #             for batch_result in batches:
    #                 for line in batch_result['lines']:
    #                     new_batches.append({
    #                         **batch_result,
    #                         'lines': line,
    #                     })
    #             batches = new_batches
    #
    #         payment_vals_list = []
    #         for batch_result in batches:
    #             payment_vals_list.append(self._create_payment_vals_from_batch(batch_result))
    #             to_reconcile.append(batch_result['lines'])
    #
    #     payments = self.env['account.payment'].create(payment_vals_list)
    #     if self.payment_type == 'outbound':
    #         print('l')
    #     else:
    #         payments.action_post()
    #
    #     domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
    #     for payment, lines in zip(payments, to_reconcile):
    #
    #         # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
    #         # and then, we can't perform the reconciliation.
    #         if payment.state != 'posted':
    #             print('kkkkkkkkkkkkkkkk')
    #             continue
    #         print('oooooooooooooooooo')
    #         payment_lines = payment.line_ids.filtered_domain(domain)
    #         for account in payment_lines.account_id:
    #             (payment_lines + lines)\
    #                 .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
    #                 .reconcile()
    #
    #     return payments
    #


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    request_approval_show_first = fields.Boolean(string="", compute='make_check_for_first_request_approval' )
    hide_request_approval_first = fields.Boolean(string="", )
    check_first_request = fields.Boolean(string="",compute='check_request_button'  )
    check_second_request = fields.Boolean(string="",compute='check_request_button'  )
    show_approved_button = fields.Boolean(string="",  )
    show_doo_hod_approved = fields.Boolean(string="",  )

    @api.depends()
    def make_check_for_first_request_approval(self):
        self.request_approval_show_first = False
        if self.state == 'draft' and self.payment_type == 'outbound':
            self.request_approval_show_first = True
        else:
            self.request_approval_show_first = False


    @api.depends()
    def check_request_button(self):
        self.check_first_request = False
        self.check_second_request = False
        if self.amount <= self.journal_id.payment_limit and self.payment_type =='outbound':
            self.check_first_request = True
        elif self.amount > self.journal_id.payment_limit and self.payment_type =='outbound':
            self.check_first_request = True
            self.check_second_request = True


    def first_request_approval_button(self):
        self.hide_request_approval_first = True
        hod_users = self.env.ref('vendor_payment_approval.hod_manager').users
        doo_users = self.env.ref('asset_request_management.doo_approvals').users
        users = hod_users + doo_users
        for user in users:
            reseiver = user.partner_id
            if reseiver:
                for payment in self:
                    msg_id = self.env['mail.message'].sudo().create({
                        'message_type': "comment",
                        "subtype_id": self.env.ref("mail.mt_comment").id,
                        'body': "Dear Sir<br></br> This Payment :{} Need Your Confirmation <br></br> Best Regards".format(
                            payment.name),
                        'subject': 'Payment Approval Needed',
                        'partner_ids': [(4, reseiver.id)],
                        'model': payment._name,
                        'res_id': payment.id,
                    })
                    notify_id = self.env['mail.notification'].sudo().create({
                        'mail_message_id': msg_id.id,
                        'res_partner_id': reseiver.id,
                        'notification_type': 'inbox',
                        'notification_status': 'exception',
                    })
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    body =  "Dear Sir<br></br> This Payment :{} Need Your Confirmation <br></br> Best Regards".format(payment.name) + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
                        base_url) + str(
                        payment.id) + '&view_type=form&model=account.payment&action=" style="font-weight: bold">' + str(payment.name) + '</a>'
                    if user.email:
                        mails_send = self.env['mail.mail'].sudo().create({
                            'subject': 'Payment Approval Needed',
                            'body_html': str(body),
                            'notification': True,
                            'auto_delete': True,
                            'email_to': user.email,
                            'message_type': 'email',
                        })

                        mails_send.sudo().send()


    def second_request_approval_button(self):
        self.show_doo_hod_approved = True
        if not self.check_second_request:
            self.sudo().button_approve()
        else:
            hod_users = self.env.ref('vendor_payment_approval.ceo_manager').users
            ceo_users = self.env.ref('asset_request_management.doo_approvals').users
            users = hod_users + ceo_users
            self.show_approved_button = True
            for user in users:
                reseiver = user.partner_id
                if reseiver:
                    for payment in self:
                        msg_id = self.env['mail.message'].sudo().create({
                            'message_type': "comment",
                            "subtype_id": self.env.ref("mail.mt_comment").id,
                            'body': "Dear Sir<br></br> This Payment :{} Need Your Confirmation <br></br> Best Regards".format(
                                payment.name),
                            'subject': 'Payment Approval Needed',
                            'partner_ids': [(4, reseiver.id)],
                            'model': payment._name,
                            'res_id': payment.id,
                        })
                        notify_id = self.env['mail.notification'].sudo().create({
                            'mail_message_id': msg_id.id,
                            'res_partner_id': reseiver.id,
                            'notification_type': 'inbox',
                            'notification_status': 'exception',
                        })
                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        body =  "Dear Sir<br></br> This Payment :{} Need Your Confirmation <br></br> Best Regards".format(payment.name) + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
                            base_url) + str(
                            payment.id) + '&view_type=form&model=account.payment&action=" style="font-weight: bold">' + str(payment.name) + '</a>'
                        if user.email:
                            mails_send = self.env['mail.mail'].sudo().create({
                                'subject': 'Payment Approval Needed',
                                'body_html': str(body),
                                'notification': True,
                                'auto_delete': True,
                                'email_to': user.email,
                                'message_type': 'email',
                            })

                            mails_send.sudo().send()



    def button_approve(self):
        self.sudo().action_post()

