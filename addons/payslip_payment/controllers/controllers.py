# -*- coding: utf-8 -*-
from odoo import http

# class PayslipPayment(http.Controller):
#     @http.route('/payslip_payment/payslip_payment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/payslip_payment/payslip_payment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('payslip_payment.listing', {
#             'root': '/payslip_payment/payslip_payment',
#             'objects': http.request.env['payslip_payment.payslip_payment'].search([]),
#         })

#     @http.route('/payslip_payment/payslip_payment/objects/<model("payslip_payment.payslip_payment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('payslip_payment.object', {
#             'object': obj
#         })