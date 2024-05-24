# -*- coding: utf-8 -*-
# from odoo import http


# class ParentalLeaves(http.Controller):
#     @http.route('/parental_leaves/parental_leaves/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/parental_leaves/parental_leaves/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('parental_leaves.listing', {
#             'root': '/parental_leaves/parental_leaves',
#             'objects': http.request.env['parental_leaves.parental_leaves'].search([]),
#         })

#     @http.route('/parental_leaves/parental_leaves/objects/<model("parental_leaves.parental_leaves"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('parental_leaves.object', {
#             'object': obj
#         })
