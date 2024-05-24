# -*- coding: utf-8 -*-
from odoo import models, fields, api, _,exceptions
from dateutil.relativedelta import relativedelta

class Accountmove(models.Model):
    _inherit = 'account.move'

    refund_reason_id = fields.Many2one('refund.reason',string='Refund Reason')
    partner_ref = fields.Char(string="Partner Ref")
    state = fields.Selection(selection_add=[('transferred', 'Transferred'),('posted',), ], ondelete={'transferred': 'set default','draft': 'set default',})

    def button_draft(self):
        res = super(Accountmove, self).button_draft()
        self.send_user_notification()
        return res
    def send_user_notification(self):
        users = self.env.ref('account_custom.receive_notify_entry_draft_group').users
        reseivers = users.mapped('partner_id')
        if reseivers:
            for entry in self:

                msg_id = self.env['mail.message'].create({
                    'message_type': "comment",
                    "subtype_id": self.env.ref("mail.mt_comment").id,
                    'body': "Dear Sir<br></br> This Entry :{} has been set to draft <br></br> Best Regards".format(
                        entry.name),
                    'subject': 'Entry Set to Draft',
                    'partner_ids': [(4, user.id) for user in reseivers],
                    'model': entry._name,
                    'res_id': entry.id,
                })
                for user in users:
                    notify_id = self.env['mail.notification'].create({
                        'mail_message_id': msg_id.id,
                        'res_partner_id': user.partner_id.id,
                        'notification_type': 'inbox',
                        'notification_status': 'exception',
                    })
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    body =  "Dear Sir<br></br> This Entry :{} has been set to draft <br></br> Best Regards".format(entry.name) + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
                        base_url) + str(
                        entry.id) + '&view_type=form&model=account.move&action=" style="font-weight: bold">' + str(entry.name) + '</a>'
                    if user.email:
                        mails_send = self.env['mail.mail'].create({
                            'subject': 'Entry Set to Draft',
                            'body_html': str(body),
                            'notification': True,
                            'auto_delete': True,
                            'email_to': user.email,
                            'message_type': 'email',
                        })

                        mails_send.send()

    # @api.constrains('invoice_date')
    # def _check_invoice_date(self):
    #     to_check = fields.date.today() + relativedelta(days=-30)
    #     if self.invoice_date and self.invoice_date < to_check:
    #         raise exceptions.ValidationError('Invoice Date Must be greater than {}'.format(to_check) )

    related_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order", required=False, )
    related_purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="Purchase Order",
                                                required=False, )
    transfer_back_ids = fields.Many2many(comodel_name="stock.picking", string="Returned Transfer", required=False, )

    @api.onchange('related_purchase_order_id')
    def filter_tarnsfer_back_by_purchase(self):
        return {
            'domain': {
                'transfer_back_ids': [('id', 'in', self.related_purchase_order_id.picking_ids.filtered(lambda x:x.state == 'done').ids)]}}

    @api.onchange('related_sale_order_id')
    def filter_tarnsfer_back_by_sales(self):
        return {
            'domain': {'transfer_back_ids': [('id', 'in', self.related_sale_order_id.picking_ids.filtered(lambda x:x.state=='done').ids)]}}

    def action_open_related_transfer(self):
        for rec in self.transfer_back_ids:
            rec.credit_note_id = self.id
        return {
            'name': 'Transfer',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'context': {'default_credit_note_id': self.id},
            'domain': [('id', 'in', self.transfer_back_ids.ids)],
            'target': 'current',
        }

    def action_post(self):
        res = super(Accountmove, self).action_post()
        if self.move_type in ['out_refund', 'in_refund']:
            if not self.transfer_back_ids:
                raise exceptions.ValidationError(
                    'You must set transfer/s and make return on it to auto fill credit note lines ')
            product_not_from_return = self.invoice_line_ids.filtered(
                lambda x: x.product_id and not x.is_returned_trnasfer)
            if product_not_from_return:
                raise exceptions.ValidationError('You must remove all products not come from returned transfer')

        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_returned_trnasfer = fields.Boolean(string="",  )


