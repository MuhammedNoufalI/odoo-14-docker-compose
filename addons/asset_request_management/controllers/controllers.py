# -*- coding: utf-8 -*-
# from odoo import http


# class AssetRequestManagement(http.Controller):
#     @http.route('/asset_request_management/asset_request_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/asset_request_management/asset_request_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('asset_request_management.listing', {
#             'root': '/asset_request_management/asset_request_management',
#             'objects': http.request.env['asset_request_management.asset_request_management'].search([]),
#         })

#     @http.route('/asset_request_management/asset_request_management/objects/<model("asset_request_management.asset_request_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('asset_request_management.object', {
#             'object': obj
#         })
