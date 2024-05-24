# -*- coding: utf-8 -*-


from collections import namedtuple
import json
import time

from itertools import groupby
from odoo import api, fields, models, _
from datetime import datetime,date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from operator import itemgetter


class stock_pickings(models.Model):
    _inherit = 'stock.picking'

    material_request = fields.Integer(string="Transfer Request", required=False, )
    # is_location_user = fields.Boolean(string="",compute='check_user_location'  )

    # @api.depends('is_location_user','location_id','location_dest_id')
    # def check_user_location(self):
    #     for rec in self:
    #         if rec.material_request > 0:
    #             if self.env.user in rec.location_id.responsible_ids or self.env.user in rec.location_dest_id.responsible_ids:
    #                 rec.is_location_user =True

    # def button_validate(self):
    #     self.ensure_one()
    #
    #     if self.material_request > 0:
    #         for rec in self.env['stock.picking'].search([('material_request','=',self.material_request),('id','!=',self.id)]):
    #             for int_trans in self.env['request.delivery'].search([('id','=',self.material_request)]):
    #                 if rec.location_id == int_trans.provider_id:
    #                     if rec.state != 'done':
    #                         raise UserError('You can not validate until ' + str(self.location_id.name) + ' validate the order of transfer')
    #
    #
    #
    #     if not self.move_lines and not self.move_line_ids:
    #         raise UserError(_('Please add some items to move.'))
    #
    #     # If no lots when needed, raise error
    #     picking_type = self.picking_type_id
    #     precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #     no_quantities_done = all(
    #         float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids)
    #     no_reserved_quantities = all(
    #         float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
    #         self.move_line_ids)
    #     if no_reserved_quantities and no_quantities_done:
    #         raise UserError(_(
    #             'You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))
    #
    #     if picking_type.use_create_lots or picking_type.use_existing_lots:
    #         lines_to_check = self.move_line_ids
    #         if not no_quantities_done:
    #             lines_to_check = lines_to_check.filtered(
    #                 lambda line: float_compare(line.qty_done, 0,
    #                                            precision_rounding=line.product_uom_id.rounding)
    #             )
    #
    #         for line in lines_to_check:
    #             product = line.product_id
    #             if product and product.tracking != 'none':
    #                 if not line.lot_name and not line.lot_id:
    #                     raise UserError(
    #                         _('You need to supply a Lot/Serial number for product %s.') % product.display_name)
    #
    #     if no_quantities_done:
    #         view = self.env.ref('stock.view_immediate_transfer')
    #         wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
    #         return {
    #             'name': _('Immediate Transfer?'),
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'stock.immediate.transfer',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'target': 'new',
    #             'res_id': wiz.id,
    #             'context': self.env.context,
    #         }
    #
    #     if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
    #         view = self.env.ref('stock.view_overprocessed_transfer')
    #         wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'stock.overprocessed.transfer',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'target': 'new',
    #             'res_id': wiz.id,
    #             'context': self.env.context,
    #         }
    #
    #     # Check backorder should check for other barcodes
    #     if self._check_backorder():
    #         return self.action_generate_backorder_wizard()
    #     self.action_done()
    #     return


class request_delivery(models.Model):
    _name = 'request.delivery'
    _inherit = ['mail.thread']


    name = fields.Char(string="Name", required=False, default='New',readonly=True,track_visibility="always")
    move_type = fields.Selection(string="Delivery Type", selection=[('direct', 'Partial'), ('one', 'All at once'), ], required=True,default='direct')
    picking_type_id = fields.Many2one(comodel_name="stock.picking.type", string="Requester Picking Type", required=True,domain=[('code','=','internal')])
    provider_picking_type_id = fields.Many2one(comodel_name="stock.picking.type", string="Provider Picking Type", required=True,domain=[('code','=','internal')])
    requester_id = fields.Many2one('stock.location', 'Destination Location', required=True,track_visibility="always",)
    provider_id = fields.Many2one('stock.location', 'Source Location', required=True,domain=[('usage','=','internal')],track_visibility="always")
    state = fields.Selection(string="State", selection=[('draft', 'Draft'),('awaiting_confirmation', 'waiting Confirmation'), ('confirmed', 'Confirmed'),('finished', 'Finished') ], required=False, default='draft',track_visibility="always")
    hide_trans_mat_button = fields.Boolean(string="Hid TM Button",default=False  )
    hide_confirm_button = fields.Boolean(string="Hid Confirm Button",default=True, ) #compute='check_provider_user_to_confirm'
    hide_note_message = fields.Boolean(string="",default=True,compute='check_provider_user_to_confirm' )
    hide_note_message_requester = fields.Boolean(string="",default=True,compute='check_provider_user_to_confirm' )
    pack_operation_product_ids = fields.One2many(comodel_name="request.pack.operation", inverse_name="request_delivery_id", string="Products", required=False, )
    transfer_count = fields.Integer(string="Transfers", required=False,compute='get_total_transfers' )
    date = fields.Date(string="Date", required=False,default=date.today() )
    user_id = fields.Many2one(comodel_name="res.users", string="Created By",invisible=True, required=False,default=lambda self:self.env.user)
    source_company_id = fields.Many2one(comodel_name="res.company", string="Source Company", required=False, )
    destination_company_id = fields.Many2one(comodel_name="res.company", string="Destination Company", required=False, )

    def request_confirm_button(self):
        self.state = 'awaiting_confirmation'

        # location_owner = []
        # for user in self.provider_id.responsible_ids:
        #
        #     location_owner.append(user.partner_id.id)
        # print (location_owner, ';;;;;;;;;;;lllllllllllllll')
        # post_vars = {'subject': "Internal Transfer Notification",
        #              'body': 'This Transfer Request Need Your Confirmation: <a target=_BLANK href="/web?#id=' + str(
        #                  self.id) + '&view_type=form&model=request.delivery&action=" style="font-weight: bold">' + str(
        #                  self.name) + '</a>',
        #              'partner_ids': location_owner}  # Where "4" adds the ID to the list
        # thread_pool = self.env['mail.thread']
        # thread_pool.message_post(
        #     type="notification",
        #     subtype="mt_comment",
        #     **post_vars)

    @api.depends('hide_confirm_button','hide_note_message')
    def check_provider_user_to_confirm(self):
        pass
        # if self.env.user in self.provider_id.responsible_ids:
        #     self.hide_confirm_button = True
        # for rec in self.env['stock.picking'].search([('material_request','=',self.id)]):
        #     if rec.location_id.id == self.provider_id.id:
        #         if rec.state != 'done':
        #             if self.hide_confirm_button == True:
        #                  self.hide_note_message = True
        #
        #     if self.env.user in self.requester_id.responsible_ids:
        #         if rec.location_dest_id.id == self.requester_id.id:
        #             if rec.state != 'done':
        #                     self.hide_note_message_requester = True



    @api.depends('transfer_count')
    def get_total_transfers(self):
        # if self.state == 'awaiting_confirmation':
        self.transfer_count = self.env['stock.picking'].search_count([('material_request', '=', self.id)])
                 # += 1

    def open_linked_transfer_material_request(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'name': 'Transfer Material',
            'domain': [('material_request', '=', self.id)],
            'target': 'current',

        }

    def confirm_button(self):
        self.state = 'confirmed'

    @api.model
    def create(self, vals):
        records = self.env['stock.location'].search([('id','=',vals['requester_id'])]).complete_name
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('material.request') + ' / ' + records or '/'

        return super(request_delivery, self).create(vals)

    @api.onchange('requester_id')
    def filter_requester(self):
        for rec in self.env['stock.picking.type'].search([]):
            if rec.warehouse_id.lot_stock_id.id == self.requester_id.id and rec.code == 'internal':
                self.picking_type_id = rec.id


    @api.onchange('provider_id')
    def filter_provider(self):
        for rec in self.env['stock.picking.type'].search([]):
            if rec.warehouse_id.lot_stock_id.id == self.provider_id.id and rec.code == 'internal':
                self.provider_picking_type_id = rec.id

    @api.onchange('source_company_id')
    def filter_source_company(self):
        domain = {}
        if self.source_company_id:
            # self.asset_id = None

            domain['provider_id'] = [('usage', '=', 'internal'),
                                  ('company_id', '=', self.source_company_id.id)]

        return {'domain': domain}

    @api.onchange('destination_company_id')
    def filter_destination_company(self):
        domain = {}
        if self.destination_company_id:
            # self.asset_id = None

            domain['requester_id'] = [('usage', '=', 'internal'),
                                     ('company_id', '=', self.destination_company_id.id)]

        return {'domain': domain}





class request_pack_operation(models.Model):
    _name = 'request.pack.operation'
    _description = 'Products and quantity that delivered to delivery order'


    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )

    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="Uom", required=False, )
    product_qty = fields.Float(string="To Do",  required=False, )

    request_delivery_id = fields.Many2one(comodel_name="request.delivery", string="", required=False, )
    on_hand = fields.Float(string="On Hand",  required=False,compute='get_qty_on_hand' )
    is_user_branshs = fields.Boolean(string="",default=False,)  #compute='show_qty_onhand_field'

    @api.depends('product_id')
    def get_qty_on_hand(self):
        qty = 0.0
        for rec in self:
            rec.on_hand = 0.0
            if rec.product_id:
                branch = rec.request_delivery_id.provider_id.id

                for rec2 in self.env['stock.quant'].search([('product_id', '=', rec.product_id.id),('location_id', '=', branch)]):
                    qty += rec2.inventory_quantity
                rec.on_hand = qty
            else:
                rec.on_hand = 0.0

    @api.onchange('product_id')
    def get_uom(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    # @api.depends('is_user_branshs')
    # def show_qty_onhand_field(self):
    #     for rec in self:
    #         if rec.request_delivery_id.provider_id.responsible_ids:
    #             if self.env.user in rec.request_delivery_id.provider_id.responsible_ids:
    #                 rec.is_user_branshs = True






class NewModule(models.TransientModel):
    _name = 'transite.locations'

    transit_location_id = fields.Many2one('stock.location', 'Transit Location', required=True,domain=[('usage','=','transit')])
    transfer_material_id = fields.Integer(string="TM ID", required=False, )

    def confirm_to_delivery(self):
        # self.hide_trans_mat_button = True

        records = self.env['stock.picking']
        products_list = []
        tm = self.env['request.delivery'].search([('id','=',self.transfer_material_id)])
        tm.write({'hide_trans_mat_button': True,'state':'finished'})
        for rec in tm.pack_operation_product_ids:
            products_list.append((0, 0, {
                'product_id': rec.product_id.id,
                'name': rec.product_id.name,
                'product_uom': rec.product_uom_id.id,
                'product_uom_qty': rec.product_qty,
                'quantity_done': rec.product_qty,
            }))
        records1 = records.sudo().create({
            'move_type': tm.move_type,
            'origin': tm.name,
            'picking_type_id': tm.picking_type_id.id,
            'state': 'draft',
            'location_id':self.transit_location_id.id ,
            'material_request': tm.id,
            'location_dest_id': tm.requester_id.id,
            'company_id': tm.destination_company_id.id,
            'move_lines': products_list,
        })
        records1.sudo().company_id = tm.destination_company_id.id

        recordes2 = records.sudo().create({
            'move_type': tm.move_type,
            'origin': tm.name,
            'picking_type_id': tm.provider_picking_type_id.id,
            'state': 'draft',
            'location_id': tm.provider_id.id,
            'company_id': tm.source_company_id.id,
            'location_dest_id': self.transit_location_id.id,
            'material_request': tm.id,
            'move_lines': products_list,
        })

        recordes2.sudo().company_id = tm.source_company_id.id



# class Adjustment(models.Model):
#     _name = 'stock.inventory'
#     _inherit = ['stock.inventory', 'mail.thread']
#
#     partner_id = fields.Many2one(track_visibility='always')
#     state = fields.Selection(track_visibility='onchange')
#     location_id = fields.Many2one(track_visibility='always')
#     filter = fields.Selection(track_visibility='onchange')


# class StockLocation(models.Model):
#     _inherit = 'stock.location'
#
#     responsible_ids = fields.Many2many(comodel_name="res.users", string="Responsible", required=False, )


