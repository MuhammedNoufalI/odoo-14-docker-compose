# -*- coding: utf-8 -*-

from odoo import models, fields, api
from lxml import etree

class AccountMove(models.Model):
    _inherit = 'account.move'

    request_approval_show = fields.Boolean(string="",  )

    def request_approval_button(self):

        for user in self.env.ref('vendor_bill_approval.finance_manager').users:
            reseiver = user.partner_id
            if reseiver and user != self.env.user:
                for inv in self:
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    body = "Dear {}<br></br> This Invoice :{} Need Your Confirmation <br></br> Best Regards".format(
                            user.name,inv.name) + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
                        base_url) + str(
                        inv.id) + '&view_type=form&model=account.move&action=" style="font-weight: bold">' + str(
                        inv.name) + '</a>'
                    msg_id = self.env['mail.message'].sudo().create({
                        'message_type': "comment",
                        "subtype_id": self.env.ref("mail.mt_comment").id,
                        'body': body,
                        'subject': 'Invoice Approval Needed',
                        'partner_ids': [(4, reseiver.id)],
                        'model': inv._name,
                        'res_id': inv.id,
                    })
                    notify_id = self.env['mail.notification'].sudo().create({
                        'mail_message_id': msg_id.id,
                        'res_partner_id': reseiver.id,
                        'notification_type': 'inbox',
                        'notification_status': 'exception',
                    })
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    body =  "Dear {0}<br></br> This Invoice :{1} Need Your Confirmation <br></br> Best Regards".format(reseiver.name,inv.name) + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
                        base_url) + str(
                        inv.id) + '&view_type=form&model=account.move&action=" style="font-weight: bold">' + str(inv.name) + '</a>'
                    if user.email:
                        mails_send = self.env['mail.mail'].sudo().create({
                            'subject': 'Invoice Approval Needed',
                            'body_html': str(body),
                            'notification': True,
                            'auto_delete': True,
                            'email_to': user.email,
                            'message_type': 'email',
                        })

                        mails_send.sudo().send()
        self.request_approval_show = True

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
        edit = self.env.user.has_group('vendor_bill_approval.finance_manager')
        doc = etree.XML(res['arch'])
        if doc :
            if edit:
                if view_type == 'tree':
                    nodes = doc.xpath("//tree")
                    for node in nodes:
                        node.set('edit', '1')

                    res['arch'] = etree.tostring(doc)
                elif view_type == 'form':
                    nodes = doc.xpath("//form")
                    for node in nodes:
                        node.set('edit', '1')
                    res['arch'] = etree.tostring(doc)
            else:
                if view_type in ['tree', 'form', 'kanban']:
                    nodes_tree = doc.xpath("//tree")
                    for node in nodes_tree:
                        node.set('edit', '0')

                        print(node)
                    nodes_form = doc.xpath("//form")
                    for node in nodes_form:
                        node.set('edit', '0')

                        print(node)

                        print(node)
                    res['arch'] = etree.tostring(doc)


        return res

