# -*- coding: utf-8 -*-
# from odoo import http


# class MaternityLeaves(http.Controller):
#     @http.route('/maternity_leaves/maternity_leaves/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/maternity_leaves/maternity_leaves/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('maternity_leaves.listing', {
#             'root': '/maternity_leaves/maternity_leaves',
#             'objects': http.request.env['maternity_leaves.maternity_leaves'].search([]),
#         })

#     @http.route('/maternity_leaves/maternity_leaves/objects/<model("maternity_leaves.maternity_leaves"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('maternity_leaves.object', {
#             'object': obj
#         })
