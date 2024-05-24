# -*- coding: utf-8 -*-
# from odoo import http


# class LoanPaid(http.Controller):
#     @http.route('/loan_paid/loan_paid/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/loan_paid/loan_paid/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('loan_paid.listing', {
#             'root': '/loan_paid/loan_paid',
#             'objects': http.request.env['loan_paid.loan_paid'].search([]),
#         })

#     @http.route('/loan_paid/loan_paid/objects/<model("loan_paid.loan_paid"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('loan_paid.object', {
#             'object': obj
#         })
