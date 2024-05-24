# -*- coding: utf-8 -*-

from odoo import fields, models
import logging
import json
_logger = logging.getLogger('Dual Link API - product')


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")

    def compute_dual_link_id(self):
        products = self.search([])
        for rec in products:
            product_id = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', rec.id)], limit=1)
            rec.dual_link_id = product_id.dual_link_id.id

    def product_vendor_taxes_sql(self):
        self._cr.execute("""
                    DELETE FROM product_supplier_taxes_rel WHERE tax_id='19'
                """)
        products = self.search([])
        for product in products:
            self._cr.execute("""
                        INSERT INTO product_supplier_taxes_rel (prod_id,tax_id) VALUES ('%s', '%s')
                    """ % (product.id, 89))

    def product_vendor_taxes_orm(self):
        products = self.search([])
        tax = self.env['account.tax'].browse(89)
        for product in products:
            product.write({
                'supplier_taxes_id': [(6, 0, [tax.id])]
            })


class InheritProductProduct(models.Model):
    _inherit = 'product.product'

    source_ref = fields.Char(string="Source Reference")
    dual_link_id = fields.Many2one('dual.link', string="Dual Link System")
    product_source_ref = fields.Char(string="Main Product Reference")

    def clean_variant_parent(self):
        for rec in self:
            variants = self.env['product.product'].search([
                ('product_source_ref', '=', rec.source_ref),
            ])
            if variants:
                _logger.info(
                    'WILL DELETE VARIANTS of product {}'.format(rec.name))
                self._cr.execute("""
                                    DELETE FROM product_product WHERE id='%s'
                                """ % rec.id)
                # rec.unlink()

    def check_and_create_variants(self, dl):
        for rec in self:
            url = str(dl.server_url) + "/entity/" + \
                str(dl.business_id.source_ref).upper() + "/ProductFormat"
            headers = {
                'Content-Type': 'application/json',
                'dl-environment': 'test',
                'authorization': 'Bearer ' + str(dl.latest_token)
            }
            payload = json.dumps({
                "where": [
                    {"type": "item", "value": rec.source_ref,
                        "key": "product", "comparator": "="}
                ],
                "includeRelationships": ["format"]
            })
            data = dl.api_send_request(
                'Get Variants List', url=url, payload=payload, headers=headers, method="POST")
            for variant in data.get('data'):
                is_exist = self.env['product.product'].sudo().search([
                    ('source_ref', '=', variant.get('format').get('identifier')),
                    ('product_source_ref', '=', self.source_ref),
                    ('company_id', '=', dl.company_id.id),
                ])
                _logger.info("Product {} - Format Test {}".format(self.source_ref,
                             variant.get('format').get('identifier')))
                vals = {
                    'name': variant.get('format').get('name') + ' ' + self.name,
                    'list_price': variant.get('price'),
                    'company_id': dl.company_id.id,
                    # 'property_account_income_id': dl.income_account.id,
                    # 'property_account_expense_id': dl.outcome_account.id,
                    'type': 'consu',
                    'categ_id': self.categ_id.id,
                    'pos_categ_id': self.pos_categ_id.id,
                    'product_source_ref': self.source_ref,
                    'source_ref': variant.get('format').get('identifier'),
                    'available_in_pos': True,
                    'dual_link_id': dl.id,
                    'standard_price': variant.get('price'),
                    'responsible_id': 2
                }
                if self.taxes_id:
                    vals['taxes_id'] = [(6, 0, self.taxes_id.ids)]

                if not is_exist:
                    self.create(vals)
                else:
                    is_exist.write(vals)
