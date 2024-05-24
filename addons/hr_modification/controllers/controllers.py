# -*- coding: utf-8 -*-
# from odoo import http


# class HrModification(http.Controller):
#     @http.route('/hr_modification/hr_modification/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_modification/hr_modification/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_modification.listing', {
#             'root': '/hr_modification/hr_modification',
#             'objects': http.request.env['hr_modification.hr_modification'].search([]),
#         })

#     @http.route('/hr_modification/hr_modification/objects/<model("hr_modification.hr_modification"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_modification.object', {
#             'object': obj
#         })
