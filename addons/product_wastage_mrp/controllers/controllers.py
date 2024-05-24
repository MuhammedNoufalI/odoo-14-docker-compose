# -*- coding: utf-8 -*-
# from odoo import http


# class ProductWastageMrp(http.Controller):
#     @http.route('/product_wastage_mrp/product_wastage_mrp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_wastage_mrp/product_wastage_mrp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_wastage_mrp.listing', {
#             'root': '/product_wastage_mrp/product_wastage_mrp',
#             'objects': http.request.env['product_wastage_mrp.product_wastage_mrp'].search([]),
#         })

#     @http.route('/product_wastage_mrp/product_wastage_mrp/objects/<model("product_wastage_mrp.product_wastage_mrp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_wastage_mrp.object', {
#             'object': obj
#         })
