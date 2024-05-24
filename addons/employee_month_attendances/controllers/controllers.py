# -*- coding: utf-8 -*-
# from odoo import http


# class EmployeeMonthAttendances(http.Controller):
#     @http.route('/employee_month_attendances/employee_month_attendances/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/employee_month_attendances/employee_month_attendances/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('employee_month_attendances.listing', {
#             'root': '/employee_month_attendances/employee_month_attendances',
#             'objects': http.request.env['employee_month_attendances.employee_month_attendances'].search([]),
#         })

#     @http.route('/employee_month_attendances/employee_month_attendances/objects/<model("employee_month_attendances.employee_month_attendances"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('employee_month_attendances.object', {
#             'object': obj
#         })
