# -*- coding: utf-8 -*-
# from odoo import http


# class VendorBillApproval(http.Controller):
#     @http.route('/vendor_bill_approval/vendor_bill_approval/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vendor_bill_approval/vendor_bill_approval/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vendor_bill_approval.listing', {
#             'root': '/vendor_bill_approval/vendor_bill_approval',
#             'objects': http.request.env['vendor_bill_approval.vendor_bill_approval'].search([]),
#         })

#     @http.route('/vendor_bill_approval/vendor_bill_approval/objects/<model("vendor_bill_approval.vendor_bill_approval"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vendor_bill_approval.object', {
#             'object': obj
#         })
