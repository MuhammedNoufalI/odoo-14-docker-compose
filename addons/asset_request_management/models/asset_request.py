# -*- coding: utf-8 -*-

from odoo import models, fields, api,exceptions
from datetime import datetime,date

class AssetRequest(models.Model):
    _name = 'asset.request'
    _rec_name = 'name'
    _description = ''

    name = fields.Char(string="Description", required=False, )
    asset_group_id = fields.Many2one(comodel_name="asset.group", string="Asset Group", required=False, )
    asset_id = fields.Many2one(comodel_name="account.asset", string="Asset", required=False, )
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    location_id = fields.Many2one(comodel_name="stock.location", string="Location", required=False, )
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'),('cancel','Canceled') ], default="draft" )
    show_send_doo_button = fields.Boolean(string="",  )
    po_state = fields.Char(string="Po State", required=False,compute='get_po_information' )
    asset_state = fields.Char(string="Asset from Po", required=False,compute='get_po_information' )
    bill_state = fields.Char(string="Bill State", required=False,compute='get_po_information' )
    asset_transfer_count = fields.Integer(string="", required=False,compute='get_transfer_count' )
    po_count = fields.Integer(string="", required=False,compute='get_purchase_count' )

    @api.depends()
    def get_transfer_count(self):
        self.asset_transfer_count = self.env['asset.transfer'].search_count([('asset_request_id','=',self.id)])

    @api.depends()
    def get_purchase_count(self):
        self.po_count = self.env['purchase.order'].search_count([('asset_request_id', '=', self.id)])

    @api.depends()
    def get_po_information(self):
        self.po_state = ''
        self.asset_state = ''
        self.bill_state = ''
        for rec in self.env['purchase.order'].search([('asset_request_id','=',self.id)],limit=1):
            self.po_state = rec.state
            for inv in rec.invoice_ids:
                self.bill_state = inv.state
                if inv.asset_ids:
                    self.asset_state = 'Asset Created'
                else:
                    self.asset_state = 'Asset not created yet'

    @api.onchange('asset_group_id','asset_id')
    def asset_info(self):
        self.employee_id = self.asset_id.employee_id.id or False
        self.location_id = self.asset_id.location_id.id or False

    def send_user_notification(self,group):
        for user in group.users:
            reseiver = user.partner_id
            if reseiver:
                for asset_req in self:
                    msg_id = self.env['mail.message'].sudo().create({
                        'message_type': "comment",
                        "subtype_id": self.env.ref("mail.mt_comment").id,
                        'body': "Dear Sir<br></br> This Asset Request :{} Need Your Confirmation <br></br> Best Regards".format(
                            asset_req.name),
                        'subject': 'Asset Request Approval Needed',
                        'partner_ids': [(4, user.id)],
                        'model': asset_req._name,
                        'res_id': asset_req.id,
                    })
                    notify_id = self.env['mail.notification'].sudo().create({
                        'mail_message_id': msg_id.id,
                        'res_partner_id': user.partner_id.id,
                        'notification_type': 'inbox',
                        'notification_status': 'exception',
                    })
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    body =  "Dear Sir<br></br> This Asset Request :{} Need Your Confirmation <br></br> Best Regards".format(asset_req.name) + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
                        base_url) + str(
                        asset_req.id) + '&view_type=form&model=asset.request&action=" style="font-weight: bold">' + str(asset_req.name) + '</a>'
                    if user.email:
                        mails_send = self.env['mail.mail'].sudo().create({
                            'subject': 'Asset Request Approval Needed',
                            'body_html': str(body),
                            'notification': True,
                            'auto_delete': True,
                            'email_to': user.email,
                            'message_type': 'email',
                        })

                        mails_send.sudo().send()

    def send_doo_approvals(self):
        self.show_send_doo_button = True
        doo_group_approvals = self.env.ref('asset_request_management.doo_approvals')
        self.send_user_notification(doo_group_approvals)

    def button_confirm(self):
        ctx = self._context
        if not self.asset_id and ctx.get('from_transfer'):
            if self.location_id:
                self.asset_id.location_id = self.location_id.id
            if self.employee_id:
                self.asset_id.employee_id = self.employee_id.id
            self.state = 'confirmed'
        if not self.asset_id and not ctx.get('from_transfer'):
            raise exceptions.ValidationError('You can not confirm without select asset, you can make po or transfer asset')
        if self.asset_id:
            if self.location_id:
                self.asset_id.location_id = self.location_id.id
            if self.employee_id:
                self.asset_id.employee_id = self.employee_id.id
            self.state = 'confirmed'

    def button_cancel(self):
        self.state = 'cancel'

    def create_purchase_order(self):
        po = self.env['purchase.order']
        partner_id = None
        price = 0.0
        if self.asset_group_id.product_id.seller_ids:
            partner_id = self.asset_group_id.product_id.seller_ids[0].name
            price = self.asset_group_id.product_id.seller_ids[0].price

        po_line = []
        po_line.append((0,0,{
            'product_id':self.asset_group_id.product_id.id,
            'name':self.asset_group_id.product_id.name,
            'product_qty':1,
            'product_uom':self.asset_group_id.product_id.uom_id.id,
            'price_unit':price if price else 1,
            'date_planned':datetime.today(),
        }))

        return {
            'name': 'Purchase Order',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {'default_order_line':po_line,'default_partner_id':partner_id.id if partner_id else False,'default_asset_request_id':self.id},
        }

    # purchase_count = fields.Integer(string="",compute='get_purchase_count'  )
    #
    # @api.depends()
    # def get_purchase_count(self):
    #     self.purchase_count = self.env['purchase.order'].search_count([('asset_request_id','=',self.id)])

    def open_related_purchase_orders(self):
        return {
            'name': 'Related Purchase Order',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain':[('asset_request_id','=',self.id)],
        }

    def create_asset_transfer(self):
        return {
            'name': 'asset Transfer',
            'view_mode': 'form',
            'res_model': 'asset.transfer',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {'default_asset_request_id': self.id},
        }

    def open_related_asset_transfer(self):
        return {
            'name': 'asset Transfer',
            'view_mode': 'tree,form',
            'res_model': 'asset.transfer',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [('asset_request_id', '=', self.id)],
        }









