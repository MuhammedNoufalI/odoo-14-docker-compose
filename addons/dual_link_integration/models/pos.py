# -*- coding: utf-8 -*-

from odoo import fields, models, _, api, SUPERUSER_ID
import logging
import json
from datetime import date, datetime

_logger = logging.getLogger('Dual Link API - pos_order')


class InheritPosSession(models.Model):
    _inherit = 'pos.session'

    def close_dl_session(self):
        for session in self:
            dl = session.dual_link_id
            d_format = "%Y-%m-%d %H:%M:%S"
            url = str(dl.server_url) + "/entity/" + str(
                dl.business_id.source_ref).upper() + "/CashDeskSession"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            payload = json.dumps({
                "where": [
                    {"type": "item", "value": session.dl_session_ref,
                        "key": "identifier", "comparator": "="},
                ]
            })
            data = dl.api_send_request('Get Session State List', url=url, payload=payload, headers=headers,
                                       method="POST")
            rec = False
            for record in data.get('data'):
                rec = record
                if rec.get('beginWorkerID'):
                    employee = self.env['hr.employee'].search([
                        ('source_ref', '=', rec.get('beginWorkerID'))
                    ])
                    if employee:
                        session.dl_worker_open = employee.id
                        if employee.user_id:
                            session.user_id = employee.user_id.id

                if rec.get('endWorkerID'):
                    employee = self.env['hr.employee'].search([
                        ('source_ref', '=', rec.get('endWorkerID'))
                    ])
                    if employee:
                        session.dl_worker_close = employee.id

            if not rec or (rec and not rec.get('isOpen')):
                _logger.info('Session details {}'.format(session.read()))
                if rec and rec.get('endDate'):
                    if "." not in str(rec.get('endDate')):
                        end_date = datetime.strptime(
                            rec.get('endDate'), '%Y-%m-%dT%H:%M:%S%z')
                        end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        rec['endDate'] = rec['endDate']
                        end_date = datetime.strptime(
                            rec.get('endDate'), '%Y-%m-%dT%H:%M:%S%z')
                        end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')
                if not rec:
                    end_date = False
                    # closing the session
                    session.action_pos_session_closing_control()
                last_order = self.env['pos.order'].sudo().search([
                    ('session_id', '=', session.id)
                ], order='id desc', limit=1)
                # session.with_user(SUPERUSER_ID).with_company(dl.company_id)._check_pos_session_balance()
                session.with_user(SUPERUSER_ID).with_company(dl.company_id).write(
                    {'state': 'closing_control',
                     'stop_at': end_date if end_date else last_order.date_order})
                if not session.config_id.cash_control:
                    session.with_user(SUPERUSER_ID).with_company(
                        dl.company_id).action_pos_session_close()


class InheritPosConfig(models.Model):
    _inherit = 'pos.config'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    company_id = fields.Many2one('res.company', string="Company")


class InheritPosOrder(models.Model):
    _inherit = 'pos.order'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    company_id = fields.Many2one('res.company', string="Company")
    dl_picking_created = fields.Boolean(
        string="DL Picking Created", default=False)

    def create_order_picking(self):
        self.with_user(SUPERUSER_ID).with_company(
            self.dual_link_id.company_id)._create_order_picking()

    def onchange_amount_all(self):
        self._onchange_amount_all()


class InheritPosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'
    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")


class InheritPosPayment(models.Model):
    _inherit = 'pos.payment'
    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")


class InheritPosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    price_unit = fields.Float(string='Unit Price', digits='POS Unit Price')
    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    full_product_name = fields.Char(
        string="Full Product Name", related="product_id.display_name", store=1)

    def onchange_product_id(self):
        self._onchange_product_id()

    def onchange_qty(self):
        self._onchange_qty()


class InheritPosSession(models.Model):
    _inherit = 'pos.session'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    company_id = fields.Many2one('res.company', string="Company")
    dl_session_ref = fields.Char(string="DL Session Reference")
    dl_session_is_open = fields.Boolean(string="DL Still Open")
    dl_worker_open = fields.Many2one('hr.employee', string="DL Opened By")
    dl_worker_close = fields.Many2one('hr.employee', string="DL Closed By")


    @api.constrains('config_id')
    def _check_pos_config(self):
        return True
