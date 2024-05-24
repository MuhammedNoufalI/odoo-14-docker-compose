# -*- coding: utf-8 -*-

import json
import logging

import pytz

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import requests
from odoo import fields, models, SUPERUSER_ID
from datetime import date, datetime, timedelta

from odoo.tools.float_utils import float_round

from odoo.exceptions import ValidationError

_logger = logging.getLogger('Dual Link API')


class DualLinkPlaces(models.Model):
    _name = 'dual.link.place'

    name = fields.Char(string="Place Name")
    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    company_id = fields.Many2one(
        'res.company', string="Company", related="dual_link_id.company_id", store=1)


class DualLink(models.Model):
    _name = 'dual.link'

    name = fields.Char(string="Name")
    auth_server_url = fields.Char(string="Auth Server URL")
    server_url = fields.Char(string="Server URL")

    username = fields.Char(string="Username")
    password = fields.Char(string="Password")

    latest_token = fields.Char(string="Latest Token")
    business_id = fields.Many2one('dual.link.place', string="Business", )
    company_id = fields.Many2one('res.company', string="Company")
    pos_config_id = fields.Many2one('pos.config', string="Cashier POS")

    last_orders_sync = fields.Datetime(string="Last Orders Sync")
    last_product_sync = fields.Datetime(string="Last Product Sync")

    specific_date_orders = fields.Datetime(string="Sync Orders Start Date")
    specific_enddate_orders = fields.Datetime(string="Sync Orders End Date")

    workers_count = fields.Char(string="Workers Count")
    categories_count = fields.Char(string="Categories Count")
    products_count = fields.Char(string="Products Count")
    orders_count = fields.Char(string="Orders Count")
    cashdesk_count = fields.Char(string="Cashdesks Count")

    income_account = fields.Many2one(
        'account.account', string="Income Account")
    difference_account = fields.Many2one(
        'account.account', string="Difference Account")
    outcome_account = fields.Many2one(
        'account.account', string="Outcome Account")
    get_order_id = fields.Char(string='Get Sepcific Order')
    get_product_name = fields.Char(string='Get Specific product')
    is_close_session = fields.Boolean(string='Close Session')

    def convert_TZ_UTC(self, TZ_datetime):
        date_time_obj = datetime.strptime(TZ_datetime, '%Y-%m-%dT%H:%M:%S%z')
        return date_time_obj

    def convert_TZ_UTCx(self, TZ_datetime):
        date_time_obj = str(TZ_datetime).split('.')[0] if len(
            str(TZ_datetime).split('.')) > 0 else str(TZ_datetime)
        date_time_obj = datetime.strptime(date_time_obj, '%Y-%m-%d %H:%M:%S')
        timezone = pytz.timezone("Asia/Dubai")
        with_timezone = timezone.localize(date_time_obj)
        return datetime.strptime(str(with_timezone.astimezone(timezone)).split('+')[0], '%Y-%m-%d %H:%M:%S')

    def convert_to_utc(self, datetime):
        timezone = pytz.timezone("Asia/Kolkata")
        last_sync = datetime.astimezone(timezone)
        return (last_sync)

    def convert_order_date(self, TZ_datetime):
        date_time_obj = datetime.strptime(TZ_datetime, '%Y-%m-%dT%H:%M:%S%z')
        datetime_obj = date_time_obj.astimezone(pytz.UTC)
        return datetime_obj - timedelta(hours=5, minutes=30)

    def sync_all(self):
        self.get_access_token_info()
        self.sync_dl_taxes()
        self.sync_dl_payment_methods()
        self.sync_dl_workers()
        self.sync_dl_cash_desks()
        self.sync_dl_categories()
        self.sync_dl_products()

    def action_view_pos_config(self):
        for rec in self:
            return {
                "name": 'Cash Desks',
                "view_mode": "kanban,tree,form",
                "res_model": "pos.config",
                "type": "ir.actions.act_window",
                "domain": [("dual_link_id", "=", rec.id)],
            }

    def action_view_products(self):
        for rec in self:
            return {
                "name": 'Products List',
                "view_mode": "kanban,tree,form",
                "res_model": "product.product",
                "type": "ir.actions.act_window",
                "domain": [("dual_link_id", "=", rec.id)],
            }

    def action_view_categories(self):
        for rec in self:
            return {
                "name": 'Categories List',
                "view_mode": "tree,form",
                "res_model": "pos.category",
                "type": "ir.actions.act_window",
                "domain": [("dual_link_id", "=", rec.id)],
            }

    def action_view_orders(self):
        for rec in self:
            return {
                "name": 'Orders List',
                "view_mode": "tree,form",
                "res_model": "pos.order",
                "type": "ir.actions.act_window",
                "domain": [("dual_link_id", "=", rec.id)],
            }

    def api_send_request(self, name, url, payload=False, headers=False, method=False):
        if not method:
            method = "POST"
        if not payload:
            payload = {}
        if not headers:
            headers = {
                'Content-Type': 'application/json',
                'dl-environment': 'test'
            }
        request = requests.request(method, url, headers=headers, data=payload)
        _logger.info('%s API Request  %s' % (name, request))
        response = request.json()
        return response

    # Get single or all tokens and store it in fields
    def get_access_token_info(self, dl_ids=False, company_ids=False):
        if not company_ids:
            company_ids = self.env['res.company'].search([])
        if not dl_ids:
            dl_ids = self.env['dual.link'].search(
                [('company_id', 'in', company_ids.ids)])
        _logger.info(dl_ids)
        for dl in dl_ids:
            try:
                dl.get_login_access()
            except Exception:
                raise ValidationError("Connection Error")

    def get_login_access(self):
        for dl in self:
            url = str(dl.auth_server_url) + "/token"
            payload = json.dumps({
                "grant_type": "password",
                "username": dl.username,
                "password": dl.password,
            })
            data = dl.api_send_request('Login', url=url, payload=payload)
            token_info = data.get('data')
            dl.latest_token = token_info.get(
                'access_token') if token_info else ''
            dl.get_business_info()

    def get_business_info(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            url = str(dl.auth_server_url) + "/business"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            data = dl.api_send_request(
                'Get Business Info', url=url, headers=headers)
            if data.get('data'):
                for business in data.get('data'):
                    if business.get('status') == 1:
                        urls = business.get("urls")
                        if urls:
                            dl.server_url = urls.get("APIServerURL")
                    is_exist = self.env['dual.link.place'].search([
                        ('source_ref', '=', business.get('id')),
                        ('dual_link_id', '=', dl.id),
                    ])
                    if not is_exist:
                        is_exist = self.env['dual.link.place'].create({
                            'name': business.get('name'),
                            'source_ref': business.get('id'),
                            'dual_link_id': dl.id
                        })
                    else:
                        is_exist.write({
                            'name': business.get('name')
                        })

    # Sync Functions
    def sync_dl_categories(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            url = str(dl.server_url) + "/entity/" + \
                str(dl.business_id.source_ref).upper() + "/ProductCategory"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            data = dl.api_send_request(
                'Get Categories List', url=url, headers=headers, method="GET")
            for category in data.get('data'):
                # Checking POS Category
                is_exist = self.env['pos.category'].search([
                    ('source_ref', '=', category.get('identifier')),
                    ('dual_link_id', '=', dl.id)
                ])
                if not is_exist:
                    is_exist = self.env['pos.category'].create({
                        'name': category.get('name'),
                        'source_ref': category.get('identifier'),
                        'dual_link_id': dl.id
                    })
                else:
                    is_exist.write({
                        'name': category.get('name')
                    })
                # Product Category
                is_product_c_exist = self.env['product.category'].search([
                    ('source_ref', '=', category.get('identifier')),
                    ('dual_link_id', '=', dl.id)
                ])
                if not is_product_c_exist:
                    is_product_c_exist = self.env['product.category'].create({
                        'name': category.get('name'),
                        'source_ref': category.get('identifier'),
                        'dual_link_id': dl.id
                    })
                else:
                    is_product_c_exist.write({
                        'name': category.get('name')
                    })

                for sub_category in category.get('subCategories'):
                    # POS Category
                    get_sub_category = self.env['pos.category'].search([
                        ('source_ref', '=', sub_category),
                        ('dual_link_id', '=', dl.id)
                    ])
                    if get_sub_category:
                        if is_exist.source_ref != get_sub_category.source_ref:
                            get_sub_category.parent_id = is_exist.id
                    # Product Category
                    get_sub_category = self.env['product.category'].search([
                        ('source_ref', '=', sub_category),
                        ('dual_link_id', '=', dl.id)
                    ])
                    if get_sub_category:
                        if is_exist.source_ref != get_sub_category.source_ref:
                            get_sub_category.parent_id = is_product_c_exist.id
            dl.categories_count = len(self.env['pos.category'].search([
                ('dual_link_id', '=', dl.id)
            ]))

    def sync_dl_workers(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            url = str(dl.server_url) + "/entity/" + \
                str(dl.business_id.source_ref).upper() + "/Employee"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            data = dl.api_send_request(
                'Get Workers List', url=url, headers=headers, method="GET")
            for employee in data.get('data'):
                if employee.get("name") == "DANY":
                    continue
                is_exist = self.env['hr.employee'].search([
                    ('source_ref', '=', employee.get('identifier')),
                    ('dual_link_id', '=', dl.id)
                ])
                if not is_exist:
                    is_exist = self.env['hr.employee'].search([
                        ('name', '=', employee.get('name'))])
                    if not is_exist:
                        is_exist = self.env['hr.employee'].create({
                            'name': employee.get('name'),
                            'source_ref': employee.get('identifier'),
                            'dual_link_id': dl.id,
                            'dl_password': employee.get('password') if employee.get('password') else 123,
                            'pin_code': employee.get('pincode')
                        })
                    else:
                        is_exist.write({
                            'name': employee.get('name'),
                            'dual_link_id': dl.id,
                            'source_ref': employee.get('identifier'),
                            'dl_password': employee.get('password') if employee.get('password') else 123,
                            'pin_code': employee.get('pincode')
                        })
                else:
                    is_exist.write({
                        'name': employee.get('name'),
                        'dl_password': employee.get('password') if employee.get('password') else 123,
                        'pin_code': employee.get('pincode')
                    })
                if not is_exist.user_id:
                    partner = self.env['res.partner'].create({
                        'company_id': dl.company_id.id,
                        'name': employee.get('name'),
                    })
                    user = self.env['res.users'].create({
                        'company_id': dl.company_id.id,
                        'name': employee.get('name'),
                        'login': employee.get('name'),
                        'password': employee.get('password') if employee.get('password') else 123,
                        'partner_id': partner.id
                    })
                    if user:
                        is_exist.user_id = user.id

            dl.workers_count = len(self.env['hr.employee'].search([
                ('dual_link_id', '=', dl.id)
            ]))

    def sync_dl_cash_desks(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            url = str(dl.server_url) + "/entity/" + \
                str(dl.business_id.source_ref).upper() + "/CashDesk"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            data = dl.api_send_request(
                'Get Cash Desk List', url=url, headers=headers, method="GET")
            for cash_desk in data.get('data'):
                is_exist = self.env['pos.config'].search([
                    ('source_ref', '=', cash_desk.get('identifier')),
                    ('dual_link_id', '=', dl.id)
                ])
                _logger.info('is_exist {}'.format(is_exist))
                if not is_exist:
                    if not dl.pos_config_id.source_ref:
                        dl.pos_config_id.name = cash_desk.get('name')
                        dl.pos_config_id.source_ref = cash_desk.get(
                            'identifier')
                        dl.pos_config_id.dual_link_id = dl.id
                        _logger.info('old config {}'.format(
                            dl.pos_config_id.read()))
                    else:
                        new_config = dl.pos_config_id.copy()
                        _logger.info('new config {}'.format(new_config.read()))
                        new_config.name = cash_desk.get('name')
                        new_config.source_ref = cash_desk.get('identifier')
                        _logger.info('new config {}'.format(new_config.read()))
                else:
                    is_exist.write({
                        'name': cash_desk.get('name')
                    })
            dl.cashdesk_count = len(self.env['pos.config'].search([
                ('dual_link_id', '=', dl.id)
            ]))

    def parse_product_object(self, data, dl):
        today = date.today() + timedelta(days=1)
        next_date = today.strftime("%Y-%m-%d") + str(" 18:30:00")
        next_date = datetime.strptime(next_date, '%Y-%m-%d %H:%M:%S')
        next_date = self.convert_to_utc(next_date)
        tax_exist = False
        for product in data.get('data'):
            if not product.get('deletedAt'):  # .get('deletedAt')
                # check product is exist or not
                is_exist = self.env['product.product'].search([
                    ('source_ref', '=', product.get('identifier')),
                    ('dual_link_id', '=', dl.id)
                ])
                if product.get('category'):
                    category = self.env['pos.category'].search([
                        ('source_ref', '=', product.get(
                            'category').get('identifier')),
                        ('dual_link_id', '=', dl.id),
                    ])
                    product_category = self.env['product.category'].search([
                        ('source_ref', '=', product.get(
                            'category').get('identifier')),
                        ('dual_link_id', '=', dl.id),
                    ])
                    if product.get("tax"):
                        tax = product.get("tax")
                        tax_exist = self.env['account.tax'].search([
                            ('source_ref', '=', tax.get('identifier')),
                            ('dual_link_id', '=', dl.id),
                        ])
                        if not tax_exist:
                            tax_exist = self.env['account.tax'].create({
                                'source_ref': tax.get('identifier'),
                                'dual_link_id': dl.id,
                                'company_id': dl.company_id.id,
                                'name': tax.get('name'),
                                'amount': float(tax.get('taxQuantity')) * 100,
                                'price_include': True
                            })
                        if not is_exist:
                            if category:
                                # checking Tax
                                vals = {
                                    'name': product.get('name'),
                                    'source_ref': product.get('identifier'),
                                    'dual_link_id': dl.id,
                                    'company_id': dl.company_id.id,
                                    'type': 'consu',
                                    'categ_id': product_category.id if product_category else main_category.id,
                                    'available_in_pos': True,
                                    'pos_categ_id': category.id,
                                    'standard_price': product.get('costPrice'),
                                    'list_price': product.get('price'),
                                    'responsible_id': 2
                                }

                                if product.get('stockElaborationType') == 0:
                                    vals.update({
                                        'type': 'product'
                                    })
                                else:
                                    vals.update({
                                        'type': 'consu'
                                    })
                                # 'property_account_income_id': dl.income_account.id,
                                # 'property_account_expense_id': dl.outcome_account.id,
                                # 'property_account_creditor_price_difference': dl.outcome_account.id,

                                is_exist = self.env['product.product'].create(
                                    vals)
                                _logger.info('Product Insert %s - %s' %
                                             (product.get('name'), is_exist))
                        else:
                            if category:
                                vals = {
                                    'name': product.get('name'),
                                    'source_ref': product.get('identifier'),
                                    'dual_link_id': dl.id,
                                    'company_id': dl.company_id.id,
                                    'type': 'consu',
                                    'categ_id': product_category.id if product_category else main_category.id,
                                    'available_in_pos': True,
                                    'pos_categ_id': category.id,
                                    'list_price': product.get('price'),
                                    'responsible_id': 2
                                }
                                if product.get('stockElaborationType') == 0:
                                    vals.update({
                                        'type': 'product'
                                    })
                                else:
                                    vals.update({
                                        'type': 'consu'
                                    })

                                is_exist.write(vals)

                        _logger.info("Product >> {}".format(is_exist.name))
                        if tax_exist:
                            is_exist.write({
                                'taxes_id': [(6, 0, tax_exist.ids)]
                            })

                        is_exist.check_and_create_variants(dl)
                        is_exist.clean_variant_parent()
                        # self.sync_dl_product_type(dl, is_exist)
        dl.products_count = len(self.env['product.product'].search([
            ('dual_link_id', '=', dl.id)
        ]))
        dl.last_product_sync = next_date.now()
        self.env['product.template'].sudo().compute_dual_link_id()

    def sync_specific_product(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            _logger.info('Start Sync {}'.format(dl))
            # UOM
            uom = self.env['uom.uom'].search([
                ('name', '=', 'Units')
            ])

            # Sync categories first to get any missing categories
            # dl.sync_dl_categories()

            # # Get Main Category for (categ_id) field
            # if no category found use this
            main_category = self.env['product.category'].search([
                ('dual_link_id', '=', dl.id)
            ], limit=1)
            # if no catgeory found create it
            if not main_category:
                main_category = self.env['product.category'].create({
                    'name': 'Bar',
                    'dual_link_id': dl.id
                })
            else:
                main_category.write({
                    'dual_link_id': dl.id
                })
            if dl.get_product_name:
                product_name = dl.get_product_name
            else:
                raise ValidationError("Add a product name !")
            url = str(dl.server_url) + "/entity/" + \
                str(dl.business_id.source_ref).upper() + "/Product"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }

            payload = json.dumps({
                "where": [
                    {"type": "item", "value": str(
                        product_name), "key": "name", "comparator": "="}
                ],
                "includeRelationships": ["tax", "category"],
                # "includeRelationships": ["category.tax", "stockCategory", "product"]
            })
            data = dl.api_send_request(
                'Get Products List', url=url, payload=payload, headers=headers, method="POST")
            res = self.parse_product_object(data, dl)

    def sync_product_from_orderline(self, source_ref):
        dls = self
        _logger.info('Start Sync {}'.format(dls))
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            _logger.info('Start Sync {}'.format(dl))
            # UOM
            uom = self.env['uom.uom'].search([
                ('name', '=', 'Units')
            ])

            # Sync categories first to get any missing categories
            dl.sync_dl_categories()

            # # Get Main Category for (categ_id) field
            # if no category found use this
            main_category = self.env['product.category'].search([
                ('dual_link_id', '=', dl.id)
            ], limit=1)
            # if no catgeory found create it
            if not main_category:
                main_category = self.env['product.category'].create({
                    'name': 'Bar',
                    'property_account_expense_categ_id': dl.income_account.id,
                    'property_account_income_categ_id': dl.outcome_account.id,
                    'dual_link_id': dl.id
                })
            else:
                main_category.write({
                    'dual_link_id': dl.id
                })

            url = str(dl.server_url) + "/entity/" + \
                str(dl.business_id.source_ref).upper() + "/Product"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }

            payload = json.dumps({
                "where": [
                    {"type": "item", "value": str(
                        source_ref), "key": "identifier", "comparator": "="}
                ],
                "includeRelationships": ["tax", "category"],
            })
            data = dl.api_send_request(
                'Get Products List', url=url, payload=payload, headers=headers, method="POST")
            tax_exist = False
            is_exist = False
            for product in data.get('data'):
                if True:
                    # if not product.get('deletedAt'):  # .get('deletedAt')
                    # check product is exist or not
                    is_exist = self.env['product.product'].search([
                        ('source_ref', '=', product.get('identifier')),
                        ('dual_link_id', '=', dl.id)
                    ])
                    if product.get('category'):
                        category = self.env['pos.category'].search([
                            ('source_ref', '=', product.get(
                                'category').get('identifier')),
                            ('dual_link_id', '=', dl.id),
                        ])
                        product_category = self.env['product.category'].search([
                            ('source_ref', '=', product.get(
                                'category').get('identifier')),
                            ('dual_link_id', '=', dl.id),
                        ])
                    if product.get("tax"):
                        tax = product.get("tax")
                        tax_exist = self.env['account.tax'].search([
                            ('source_ref', '=', tax.get('identifier')),
                            ('dual_link_id', '=', dl.id),
                        ])
                        if not tax_exist:
                            tax_exist = self.env['account.tax'].create({
                                'source_ref': tax.get('identifier'),
                                'dual_link_id': dl.id,
                                'company_id': dl.company_id.id,
                                'name': tax.get('name'),
                                'amount': float(tax.get('taxQuantity')) * 100,
                                'price_include': True
                            })
                    if not is_exist:
                        if category:
                            # checking Tax
                            vals = {
                                'name': product.get('name'),
                                'source_ref': product.get('identifier'),
                                'dual_link_id': dl.id,
                                'company_id': dl.company_id.id,
                                'type': 'consu',
                                'categ_id': product_category.id if product_category else main_category.id,
                                'available_in_pos': True,
                                'pos_categ_id': category.id,
                                'standard_price': product.get('costPrice'),
                                'list_price': product.get('price'),
                                'responsible_id': 2
                            }
                            if product.get('stockElaborationType') == 0:
                                vals.update({
                                    'type': 'product'
                                })
                            else:
                                vals.update({
                                    'type': 'consu'
                                })

                            is_exist = self.env['product.product'].create(vals)
                            _logger.info('Product Insert %s - %s' %
                                         (product.get('name'), is_exist))
                            _logger.info("Product >> {}".format(is_exist.name))
                            if tax_exist:
                                is_exist.write({
                                    'taxes_id': [(6, 0, tax_exist.ids)]
                                })

                            is_exist.check_and_create_variants(dl)
                            # is_exist.clean_variant_parent()
            dl.products_count = len(self.env['product.product'].search([
                ('dual_link_id', '=', dl.id)
            ]))
            self.env['product.template'].sudo().compute_dual_link_id()
            self.env.cr.commit()
            return is_exist

    def sync_dl_products_bydate(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            _logger.info('Start Sync {}'.format(dl))
            # UOM
            uom = self.env['uom.uom'].search([
                ('name', '=', 'Units')
            ])
            last_sync = dl.last_product_sync
            if not last_sync:
                raise ValidationError("Please update last product sync date")
            else:
                last_sync = self.convert_to_utc(last_sync)
            # Sync categories first to get any missing categories
            dl.sync_dl_categories()

            # # Get Main Category for (categ_id) field
            # if no category found use this
            main_category = self.env['product.category'].search([
                ('dual_link_id', '=', dl.id)
            ], limit=1)
            # if no catgeory found create it
            if not main_category:
                main_category = self.env['product.category'].create({
                    'name': 'Bar',
                    'dual_link_id': dl.id
                })
            else:
                main_category.write({
                    'dual_link_id': dl.id
                })

            url = str(dl.server_url) + "/entity/" + \
                str(dl.business_id.source_ref).upper() + "/Product"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            payload = json.dumps({
                "where": [
                    {"type": "item", "value": str(
                        last_sync), "key": "createdAt", "comparator": ">"}
                ],
                "includeRelationships": ["tax", "category"],
            })
            data = dl.api_send_request(
                'Get Products List', url=url, payload=payload, headers=headers, method="POST")
            res = self.parse_product_object(data, dl)

    def sync_dl_products(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            _logger.info('Start Sync {}'.format(dl))
            # UOM
            uom = self.env['uom.uom'].search([
                ('name', '=', 'Units')
            ])

            # Sync categories first to get any missing categories
            dl.sync_dl_categories()

            # # Get Main Category for (categ_id) field
            # if no category found use this
            main_category = self.env['product.category'].search([
                ('dual_link_id', '=', dl.id)
            ], limit=1)
            # if no catgeory found create it
            if not main_category:
                main_category = self.env['product.category'].create({
                    'name': 'Bar',
                    'dual_link_id': dl.id
                })
            else:
                main_category.write({
                    'dual_link_id': dl.id
                })

            url = str(dl.server_url) + "/entity/" + \
                str(dl.business_id.source_ref).upper() + "/Product"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            payload = json.dumps({
                "includeRelationships": ["tax", "category"],
            })
            data = dl.api_send_request(
                'Get Products List', url=url, payload=payload, headers=headers, method="POST")
            res = self.parse_product_object(data, dl)

    def sync_dl_product_type(self, dl, product_id):
        url = str(dl.server_url) + "/api/v4/place/" + str(
            dl.business_id.source_ref).upper() + "/Product"
        headers = {
            'Content-Type': 'application/json',
            'dl-environment': 'test',
            'authorization': 'Bearer ' + str(dl.latest_token)
        }
        payload = json.dumps({
            "where": [
                {"type": "item", "value": product_id.source_ref,
                    "key": "product", "comparator": "="}
            ],
            "includeRelationships": ["tax", "category", "category.tax"]
        })
        data = dl.api_send_request(
            'Get Product Type List', url=url, payload=payload, headers=headers, method="POST")
        for product in data.get('data'):
            if product.get('stockElaborationType') == 0:
                product_id.write({
                    'type': 'product'
                })
            else:
                product_id.write({
                    'type': 'consu'
                })

    def sync_dl_payment_methods(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            cash_payment_method = self.env['pos.payment.method'].search([
                ('company_id', '=', dl.company_id.id),
                ('is_cash_count', '=', True),
            ], limit=1)
            config_ids = self.env['pos.config'].search([
                ('company_id', '=', dl.company_id.id),
                ('dual_link_id', '=', dl.id),
            ])
            url = str(dl.server_url) + "/entity/" + str(
                dl.business_id.source_ref).upper() + "/PayMethod"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            data = dl.api_send_request(
                'Get Payment List', url=url, headers=headers, method="GET")
            for payment_method in data.get('data'):
                is_method_exist = self.env['pos.payment.method'].search([
                    ('dual_link_id', '=', dl.id),
                    ('source_ref', '=', payment_method.get('identifier')),
                ], limit=1)
                if not is_method_exist:
                    is_method_exist = self.env['pos.payment.method'].create({
                        'dual_link_id': dl.id,
                        'source_ref': payment_method.get('identifier'),
                        'company_id': dl.company_id.id,
                        'name': payment_method.get('name'),
                        'config_ids': [(6, 0, config_ids.ids)],
                        'receivable_account_id': cash_payment_method.receivable_account_id.id
                    })
                    _logger.info('Payment Method record {}'.format(
                        is_method_exist.read()))

    def sync_dl_make_payment(self, dl, order):
        url = str(dl.server_url) + "/entity/" + str(
            dl.business_id.source_ref).upper() + "/CashDeskLine"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + str(dl.latest_token)
        }
        payload = json.dumps({
            "where": [
                {"type": "item", "value": order.source_ref,
                    "key": "archivedDocument", "comparator": "="}
            ],
            "includeRelationships": ["payMethod.image"]
        })
        data = dl.api_send_request(
            'Get Payment List', url=url, payload=payload, headers=headers, method="POST")
        for payment in data.get('data'):
            if payment.get('type') in [1, 2]:
                payment_method = payment.get('payMethod')
                cash_payment_method = self.env['pos.payment.method'].search([
                    ('company_id', '=', dl.company_id.id),
                    ('is_cash_count', '=', True),
                ], limit=1)
                if not payment_method:
                    # Cash Payment
                    order.session_id.state = 'opened'
                    if cash_payment_method:
                        vals = {
                            'pos_order_id': order.id,
                            'company_id': dl.company_id.id,
                            'session_id': order.session_id.id,
                            'source_ref': payment.get('identifier'),
                            # 'amount': sum(order.lines.mapped('price_subtotal_incl')),
                            'amount': payment.get('money'),
                            'payment_method_id': cash_payment_method.id
                        }
                        if payment.get('type') == 2:
                            vals['payment_type'] = 'outbound'
                            vals['amount'] = float(payment.get('money')) * -1
                        is_payment_exist = self.env['pos.payment'].create(vals)
                    _logger.info('Payment Created %s' %
                                 is_payment_exist.read())
                else:
                    # Checking Method
                    is_method_exist = self.env['pos.payment.method'].search([
                        ('dual_link_id', '=', dl.id),
                        ('source_ref', '=', payment_method.get('identifier')),
                    ], limit=1)
                    order.session_id.state = 'opened'
                    vals = {
                        'pos_order_id': order.id,
                        'company_id': dl.company_id.id,
                        'session_id': order.session_id.id,
                        'source_ref': payment.get('identifier'),
                        'amount': payment.get('money'),
                        'payment_method_id': is_method_exist.id
                    }
                    if payment.get('type') == 2:
                        vals['amount'] = float(payment.get('money')) * -1

                    is_payment_exist = self.env['pos.payment'].create(vals)
                    _logger.info('Payment Created %s' %
                                 is_payment_exist.read())

    def sync_dl_orders_lines(self, dl, source_ref):
        url = str(dl.server_url) + "/entity/" + str(
            dl.business_id.source_ref).upper() + "/ArchivedTicketLinesGroup"
        headers = {
            'Content-Type': 'application/json',
            'authorization': str(dl.latest_token)
        }
        payload = json.dumps({
            "where": [
                {"type": "item", "value": source_ref,
                    "key": "archivedDocument", "comparator": "="}
            ],
        })
        data = dl.api_send_request(
            'Get Orders List', url=url, payload=payload, headers=headers, method="POST")
        lines_obj = []
        log_obj = []
        total_amount = 0
        total_tax = 0
        for line in data.get('data'):
            _logger.info("CLONED {}".format(line.get('wasCloned')))
            if not line.get('wasCloned'):
                domain = [
                    ('source_ref', '=', line.get('productID')),
                    ('dual_link_id', '=', dl.id)
                ]
                if line.get('formatID'):
                    domain = [
                        ('product_source_ref', '=', line.get('productID')),
                        ('source_ref', '=', line.get('formatID')),
                        ('dual_link_id', '=', dl.id)
                    ]
                product = self.env['product.product'].search(domain, limit=1)
                print('product is', product.name)
                tax_percent = 0
                discount_p = 0
                if not product:
                    product = self.sync_product_from_orderline(
                        line.get('productID'))
                if product:
                    total_price = line.get('totalPrice') if line.get(
                        'totalPrice') != 0 else line.get('totalInvited')
                    qty = len(line.get('archivedTicketLines'))
                    _logger.info(
                        'total_price is %s and listprice is %s' % (total_price, float(line.get('productBasePrice'))))

                    taxes = False
                    if product.taxes_id:
                        taxes = [(6, 0, product.taxes_id.ids)]
                        tax_percent = sum(
                            [line.amount for line in product.taxes_id.children_tax_ids])

                        if product.taxes_id.subtax_ids:
                            taxes = [(6, 0, product.taxes_id.subtax_ids.ids)]
                    if line.get('totalDiscount') > 0:
                        untax_amt = (line.get('productBasePrice')
                                     * qty)*(100/(100+tax_percent))
                        discount_p = (
                            (untax_amt - line.get('totalDiscount'))/untax_amt)*100
                    line_taxes = line.get('subtaxesDict') if line.get(
                        'subtaxesDict') else False
                    vals = {
                        'pack_lot_ids': [],
                        'product_id': product.id,
                        'source_ref': line.get('id'),
                        'qty': qty if total_price >= 0 else qty * -1,
                        'dual_link_id': dl.id,
                        'discount': discount_p,
                        'price_unit': float(line.get('productBasePrice')),
                        'price_subtotal': float(line.get('totalPriceBase')),
                        'price_subtotal_incl': float(line.get('totalPrice'))
                    }
                    log_obj.append((0, 0, {
                        'product_id': product.id if product else False,
                        'product_name': line.get('productName'),
                        'product_ref': line.get('productID'),
                        'format_name': line.get('formatName'),
                        'qty': len(line.get('archivedTicketLines')),
                        'is_cloned': line.get('wasCloned'),
                        'price': line.get('totalPrice') if line.get('totalPrice') != 0 else line.get('totalInvited'),
                        'total_price': len(line.get('archivedTicketLines')) * (
                            line.get('totalPrice') if line.get('totalPrice') != 0 else line.get('totalInvited'))
                    }))
                    if taxes:
                        vals['tax_ids'] = taxes
                    if vals not in lines_obj:
                        lines_obj.append((0, 0, vals))
                    total_amount += float(line.get('totalPrice'))
                    total_tax += float(line.get("totalTaxes"))

        return [lines_obj, total_amount, total_tax, log_obj]

    def get_config_id_from_cashdesk(self, dl, session_id):
        url = str(dl.server_url) + "/entity/" + str(
            dl.business_id.source_ref).upper() + "/CashDeskSession"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': str(dl.latest_token)
        }
        payload = json.dumps({
            "where": [
                {"type": "item", "value": session_id,
                    "key": "identifier", "comparator": "="},
            ]
        })
        data = dl.api_send_request(
            'Get Session List', url=url, payload=payload, headers=headers, method="POST")
        for session in data.get('data'):
            return self.env['pos.config'].search([
                ('source_ref', '=', session.get('cashDesk'))
            ])

    def sync_dl_taxes(self):
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])

        for dl in dls:
            url = str(dl.server_url) + "/entity/" + str(
                dl.business_id.source_ref).upper() + "/Tax"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            data = dl.api_send_request(
                'Get Tax List', url=url, headers=headers, method="GET")
            for tax in data.get('data'):
                self.sync_tax_obj(tax, dl)
            url = str(dl.server_url) + "/entity/" + str(
                dl.business_id.source_ref).upper() + "/SubTax"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            data = dl.api_send_request(
                'Get Sub Tax List', url=url, headers=headers, method="GET")
            for tax in data.get('data'):
                self.sync_tax_obj(tax, dl)

    def sync_tax_obj(self, tax, dl):
        tax_exist = self.env['account.tax'].search([
            ('source_ref', '=', tax.get('identifier')),
            ('dual_link_id', '=', dl.id),
        ])
        main_tax = False
        if tax.get('identifier'):
            main_tax = self.env['account.tax'].search([
                ('source_ref', '=', tax.get('identifier'))
            ])
        if not tax_exist:
            vals = {
                'source_ref': tax.get('identifier'),
                'dual_link_id': dl.id,
                'company_id': dl.company_id.id,
                'name': tax.get('name'),
                'amount': float(tax.get('taxQuantity')) * 100,
                'price_include': True
            }
            if main_tax:
                vals['main_id'] = main_tax.id
            self.env['account.tax'].create(vals)
        else:
            if main_tax:
                tax_exist.write({
                    'main_id': main_tax.id
                })

    def parse_order_object(self, data, dl):
        sessions_used = []
        count = 0
        last_order_date = False
        latest_session_id = False
        dual_log = self.env['dual.link.log'].sudo()
        for order in data.get('data'):
            is_order_exist = self.env['pos.order'].search([
                ('source_ref', '=', order.get('identifier')),
                ('dual_link_id', '=', dl.id),
            ])
            if not is_order_exist:
                last_order_date = self.convert_TZ_UTC(
                    order.get('legalDate'))
                last_order_date = last_order_date.strftime(
                    '%Y-%m-%d %H:%M:%S')
                # TODO: Sessions and orders insert
                if order.get('cashDeskSession'):
                    latest_session_id = order.get('cashDeskSession')

                    session_open = self.convert_TZ_UTC(
                        order.get('sessionBeginDate'))
                    order_date = self.convert_TZ_UTC(
                        order.get('legalDate'))
                    d_format = "%Y-%m-%d %H:%M:%S"

                    is_exist = self.env['pos.session'].search([
                        ('dl_session_ref', '=', order.get('cashDeskSession')),
                        ('dual_link_id', '=', dl.id),
                        ('company_id', '=', dl.company_id.id)
                    ])
                    if is_exist and is_exist.state in ['closing_control', 'closed']:
                        continue
                    _logger.info('check pos session {}'.format(is_exist))
                    # Get Session Details
                    url = str(dl.server_url) + "/entity/" + str(
                        dl.business_id.source_ref).upper() + "/CashDeskSession"
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': str(dl.latest_token)
                    }
                    payload = json.dumps({
                        "where": [
                            {"type": "item", "value": str(order.get('cashDeskSession')), "key": "identifier",
                                "comparator": "="},
                        ],
                        "orderby": [{"beginDate": "asc"}]
                    })
                    data = dl.api_send_request('Get Session List', url=url, payload=payload, headers=headers,
                                               method="POST")
                    session = {}
                    for session_obj in data.get('data'):
                        session = session_obj
                        break
                    if not is_exist:
                        _logger.info('check_point {}'.format(session))
                        config_id = self.get_config_id_from_cashdesk(
                            dl, order.get('cashDeskSession'))
                        _logger.info(
                            'config_id selected {}'.format(config_id.read()))
                        # checking date
                        if session and session.get('begindate') and "." not in str(session.get('begindate')):
                            session['begindate'] = session['begindate'] + '.000000'

                        session_start_date = self.convert_TZ_UTC(
                            order.get('legalDate'))
                        session_start_date = session_start_date.strftime(
                            '%Y-%m-%d %H:%M:%S')
                        is_exist = self.env['pos.session'].create({
                            'source_ref': session.get('id') if session.get('id') else order.get('cashDeskSession'),
                            'dl_session_ref': order.get('cashDeskSession'),
                            'config_id': config_id.id,
                            'dual_link_id': dl.id,
                            'update_stock_at_closing': False,
                            'company_id': dl.company_id.id,
                            'start_at': session_start_date,
                            'state': 'opened',
                            'dl_session_is_open': True,
                            'user_id': 2
                        })
                        _logger.info('session created {}'.format(is_exist))
                    else:
                        is_exist.write({
                            'dl_session_is_open': session.get('isOpen'),
                            'company_id': dl.company_id.id
                        })
                    sessions_used.append(is_exist.id)
                    # Make it updating for every order line
                    is_exist.update({
                        'update_stock_at_closing': False,
                    })
                    _logger.info(
                        'session details >>>>> {}'.format(is_exist.read()))
                    is_order_exist = self.env['pos.order'].search([
                        ('source_ref', '=', order.get('id')),
                        ('dual_link_id', '=', dl.id),
                    ])
                    price_list = self.env['product.pricelist'].search(
                        [], limit=1)
                    amount_total = order.get('totalPrice') if order.get('totalPrice') != 0 else order.get(
                        'totalinvited')
                    date_order = self.convert_order_date(
                        order.get('legalDate'))
                    date_order = date_order.strftime('%Y-%m-%d %H:%M:%S')
                    if is_exist:
                        lines_obj = self.sync_dl_orders_lines(
                            dl, order.get('identifier'))
                        vals = {
                            'fiscal_position_id': False,
                            "pricelist_id": price_list.id,
                            "name": order.get('documentID'),
                            "source_ref": order.get('identifier'),
                            "session_id": is_exist.id,
                            "dual_link_id": dl.id,
                            "lines": lines_obj[0],
                            "company_id": dl.company_id.id,
                            "amount_total": lines_obj[1],
                            "amount_tax": lines_obj[2],
                            "amount_return": 0,
                            "amount_paid": lines_obj[1],
                            "state": 'draft',
                            "date_order": date_order,
                        }
                        _logger.info('vals object {}'.format(vals))

                        if not is_order_exist:
                            is_order_exist = self.env['pos.order'].create(
                                vals)
                            dual_log.create({
                                'name': 'Fetching %s' % order.get('documentID'),
                                'message': 'N/A',
                                'is_order': True,
                                'order_ids': [(6, 0, [is_order_exist.id])],
                                'line_ids': [(6, 0, is_order_exist.lines.ids)],
                                'api_lines': lines_obj[3]
                            })
                            count = count + 1
                            _logger.info('is_order_exist created {}'.format(
                                is_order_exist.read()))
                            self.sync_dl_make_payment(dl, is_order_exist)
                            _logger.info(
                                'real order {}'.format(is_order_exist))
                        if not is_order_exist.dl_picking_created:
                            _logger.info("Order Picking will start for .. {}".format(
                                is_order_exist.read()))
                            _logger.info(
                                "Order Lines Picking will start for .. {}".format(is_order_exist.lines.read()))
                            is_order_exist.with_user(SUPERUSER_ID).with_company(
                                dl.company_id).create_order_picking()
                            is_order_exist.dl_picking_created = True

                        is_order_exist.state = 'paid'
        # Closing Sessions
        session_ids = self.env['pos.session'].search(
            [('id', 'in', sessions_used)])
        for session in session_ids:
            session.state = 'opened'
        dl.orders_count = len(self.env['pos.order'].search([
            ('dual_link_id', '=', dl.id)
        ]))

    def sync_specific_order(self):
        documentID = self.get_order_id
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])
        for dl in dls:
            last_sync = dl.last_orders_sync
            if not last_sync:
                today = date.today()
                last_sync = today.strftime("%Y-%m-%d") + str(" 00:00:00")
            else:
                last_sync = self.convert_to_utc(last_sync)
            url = str(dl.server_url) + "/entity/" + str(
                dl.business_id.source_ref).upper() + "/ArchivedDocument"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            payload = json.dumps({
                "where": [
                    {"type": "item", "value": documentID,
                        "key": "documentID", "comparator": "="}
                ],
                "orderby": [{"date": "asc"}, {"documentID": "desc"}]
            })
            data = dl.api_send_request(
                'Get Orders List', url=url, payload=payload, headers=headers, method="POST")
            res = self.parse_order_object(data, dl)

    def cron_sync_specific_date_order(self):
        dls = self
        today = date.today()
        if not dls:
            dls = self.env['dual.link'].search([])
        for dl in dls:
            start_date = today - timedelta(days=1)
            sync_date = start_date.strftime("%Y-%m-%d") + str(" 01:30:00")
            sync_date = datetime.strptime(sync_date, '%Y-%m-%d %H:%M:%S')
            sync_end_date = today.strftime("%Y-%m-%d") + str(" 01:29:00")
            sync_end_date = datetime.strptime(
                sync_end_date, '%Y-%m-%d %H:%M:%S')
            sync_date = self.convert_to_utc(sync_date)
            sync_date_end = self.convert_to_utc(sync_end_date)
            url = str(dl.server_url) + "/entity/" + str(
                dl.business_id.source_ref).upper() + "/ArchivedDocument"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            payload = json.dumps({
                "where": [
                    {"type": "item", "value": "",
                        "key": "documentID", "comparator": "!="},
                    {"type": "operator", "value": "and"},
                    {"type": "item", "value": str(
                        sync_date), "key": "legalDate", "comparator": ">"},
                    {"type": "operator", "value": "and"},
                    {"type": "item", "value": str(
                        sync_date_end), "key": "legalDate", "comparator": "<"}
                ],
                "orderby": [{"date": "asc"}, {"documentID": "desc"}]
            })
            data = dl.api_send_request(
                'Get Orders List', url=url, payload=payload, headers=headers, method="POST")
            res = self.parse_order_object(data, dl)

    def sync_specific_date_orders(self):
        dual_log = self.env['dual.link.log'].sudo()
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])
        for dl in dls:
            sync_date = dl.specific_date_orders
            sync_end_date = dl.specific_enddate_orders
            if not sync_date or not sync_end_date:
                raise ValidationError("Please Input a Specific Date")
            else:
                sync_date = self.convert_to_utc(sync_date)
                sync_date_end = self.convert_to_utc(sync_end_date)
            url = str(dl.server_url) + "/entity/" + str(
                dl.business_id.source_ref).upper() + "/ArchivedDocument"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            payload = json.dumps({
                "where": [
                    {"type": "item", "value": "",
                        "key": "documentID", "comparator": "!="},
                    {"type": "operator", "value": "and"},
                    {"type": "item", "value": str(
                        sync_date), "key": "legalDate", "comparator": ">"},
                    {"type": "operator", "value": "and"},
                    {"type": "item", "value": str(
                        sync_date_end), "key": "legalDate", "comparator": "<"}
                ],
                "orderby": [{"date": "asc"}, {"documentID": "desc"}]
            })
            data = dl.api_send_request(
                'Get Orders List', url=url, payload=payload, headers=headers, method="POST")
            res = self.parse_order_object(data, dl)

    def sync_dl_orders(self):
        dual_log = self.env['dual.link.log'].sudo()
        dls = self
        if not dls:
            dls = self.env['dual.link'].search([])
        for dl in dls:
            last_sync = dl.last_orders_sync
            if not last_sync:
                today = date.today()
                last_sync = today.strftime("%Y-%m-%d") + str(" 00:00:00")
            else:
                last_sync = self.convert_to_utc(last_sync)
            url = str(dl.server_url) + "/entity/" + str(
                dl.business_id.source_ref).upper() + "/ArchivedDocument"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': str(dl.latest_token)
            }
            payload = json.dumps({
                "where": [
                    {"type": "item", "value": "",
                        "key": "documentID", "comparator": "!="},
                    {"type": "operator", "value": "and"},
                    {"type": "item", "value": str(
                        last_sync), "key": "legalDate", "comparator": ">"}
                ],
                "orderby": [{"date": "asc"}, {"documentID": "desc"}]
            })
            data = dl.api_send_request(
                'Get Orders List', url=url, payload=payload, headers=headers, method="POST")
            res = self.parse_order_object(data, dl)

    def check_sessions_state(self, dl, session_id):
        if session_id:
            d_format = "%Y-%m-%d %H:%M:%S"
            sessions = self.env['pos.session'].search([
                ('state', '=', 'opened'),
                ('dl_session_ref', '!=', session_id.source_ref),
            ])
            for session in sessions:
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
                    if rec and rec.get('endDate'):
                        end_date = self.convert_TZ_UTC(rec.get('endDate'))
                        end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')
                    if not rec:
                        end_date = False
                        # closing the session
                        # session.action_pos_session_closing_control()
                    last_order = self.env['pos.order'].sudo().search([
                        ('session_id', '=', session.id)
                    ], order='id desc', limit=1)
                    if dl.is_close_session:
                        session.with_user(SUPERUSER_ID).with_company(
                            dl.company_id)._check_pos_session_balance()
                        session.with_user(SUPERUSER_ID).with_company(dl.company_id).write(
                            {'state': 'closing_control',
                             'stop_at': end_date.strftime(d_format) if end_date else last_order.date_order})
                        if not session.config_id.cash_control:
                            session.with_user(SUPERUSER_ID).with_company(
                                dl.company_id).action_pos_session_close()
