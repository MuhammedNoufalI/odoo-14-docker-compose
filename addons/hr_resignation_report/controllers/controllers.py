# -*- coding: utf-8 -*-
# from odoo import http


# class HrResignationReport(http.Controller):
#     @http.route('/hr_resignation_report/hr_resignation_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_resignation_report/hr_resignation_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_resignation_report.listing', {
#             'root': '/hr_resignation_report/hr_resignation_report',
#             'objects': http.request.env['hr_resignation_report.hr_resignation_report'].search([]),
#         })

#     @http.route('/hr_resignation_report/hr_resignation_report/objects/<model("hr_resignation_report.hr_resignation_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_resignation_report.object', {
#             'object': obj
#         })
