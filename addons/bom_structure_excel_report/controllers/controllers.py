# -*- coding: utf-8 -*-
# from odoo import http


# class BomStructureExcelReport(http.Controller):
#     @http.route('/bom_structure_excel_report/bom_structure_excel_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bom_structure_excel_report/bom_structure_excel_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bom_structure_excel_report.listing', {
#             'root': '/bom_structure_excel_report/bom_structure_excel_report',
#             'objects': http.request.env['bom_structure_excel_report.bom_structure_excel_report'].search([]),
#         })

#     @http.route('/bom_structure_excel_report/bom_structure_excel_report/objects/<model("bom_structure_excel_report.bom_structure_excel_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bom_structure_excel_report.object', {
#             'object': obj
#         })
