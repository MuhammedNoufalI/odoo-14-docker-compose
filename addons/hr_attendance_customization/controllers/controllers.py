# -*- coding: utf-8 -*-
# from odoo import http


# class HrAttendanceCustomization(http.Controller):
#     @http.route('/hr_attendance_customization/hr_attendance_customization/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_attendance_customization/hr_attendance_customization/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_attendance_customization.listing', {
#             'root': '/hr_attendance_customization/hr_attendance_customization',
#             'objects': http.request.env['hr_attendance_customization.hr_attendance_customization'].search([]),
#         })

#     @http.route('/hr_attendance_customization/hr_attendance_customization/objects/<model("hr_attendance_customization.hr_attendance_customization"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_attendance_customization.object', {
#             'object': obj
#         })
