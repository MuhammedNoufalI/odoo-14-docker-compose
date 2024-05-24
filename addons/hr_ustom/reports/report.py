# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

import io
import base64
class VendBillReportXls(models.AbstractModel):
    _name = 'report.hr_ustom.attendance_xlsx_template'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, records):
        table_header = self.table_header_format(workbook)
        table_header3 = self.table_header_format3(workbook)
        table_content = self.table_content_format(workbook)
        for rec in records:
            worksheet = workbook.add_worksheet(rec.employee_id.name +' / '+ str(rec.id))
            row = 1
            worksheet.write(row, 0,  "Employee :", table_header3)
            worksheet.write(row, 1,  rec.employee_id.name, table_header3)
            row +=1
            worksheet.write(row, 0, "Total Late :", table_header3)
            worksheet.write(row, 1, rec.total_late, table_header3)
            row +=1
            worksheet.write(row, 0, "Total Early :", table_header3)
            worksheet.write(row, 1, rec.total_early, table_header3)
            row +=1
            worksheet.write(row, 0, "Total Over Time :", table_header3)
            worksheet.write(row, 1, rec.total_overtime, table_header3)
            row +=1
            worksheet.write(row, 0, "Total Absent :", table_header3)
            worksheet.write(row, 1, rec.total_absent, table_header3)

            row = 1
            worksheet.write(row, 4, "Date From :", table_header3)
            worksheet.write(row, 5, "{}".format(rec.date_from), table_header3)
            row += 1
            worksheet.write(row, 4, "Date From :", table_header3)
            worksheet.write(row, 5, "{}".format(rec.date_to), table_header3)
            row += 1
            worksheet.write(row, 4, "Absent Deduction :", table_header3)
            worksheet.write(row, 5, rec.deduction, table_header3)
            row += 1
            worksheet.write(row, 4, "Bonus :", table_header3)
            worksheet.write(row, 5, rec.bonus, table_header3)
            row += 1
            worksheet.write(row, 4, "Late Deduction :", table_header3)
            worksheet.write(row, 5, rec.late_deduction, table_header3)
            row += 1
            worksheet.write(row, 4, "Early Deduction :", table_header3)
            worksheet.write(row, 5, rec.early_deduction, table_header3)

            row +=1
            for i in range(0,30):
                worksheet.set_column(0, i, 25)
            ########################################################
            worksheet.write(row, 0, "Date", table_header)
            worksheet.write(row, 1, "Day of Week", table_header)
            worksheet.write(row, 2, "Hour From", table_header)
            worksheet.write(row, 3, "Day of Week", table_header)
            worksheet.write(row, 4, "Hour To", table_header)
            worksheet.write(row, 5, "Check in", table_header)
            worksheet.write(row, 6, "Check out", table_header)
            worksheet.write(row, 7, "Late Check In", table_header)
            worksheet.write(row, 8, "Early Check Out", table_header)
            worksheet.write(row, 9, "Over Time", table_header)
            worksheet.write(row, 10, "Working Hours", table_header)
            row = row + 1
            for line in rec.employee_attendance_line:
                worksheet.write(row, 0, "{}".format(line.date), table_content)
                worksheet.write(row, 1, line.shift_start_day , table_content)
                worksheet.write(row,2, line.hour_from, table_content)
                worksheet.write(row,3, line.shift_end_day, table_content)
                worksheet.write(row, 4, line.hour_to, table_content)
                worksheet.write(row, 5, "{}".format(line.check_in), table_content)
                worksheet.write(row, 6, "{}".format(line.check_out), table_content)
                worksheet.write(row, 7, line.late, table_content)
                worksheet.write(row, 8, line.early, table_content)
                worksheet.write(row, 9, line.over_time, table_content)
                worksheet.write(row, 10, line.worked_hours, table_content)
                row += 1
    def table_header_format(self, workbook):
        return workbook.add_format({
            'bold': 1,
            'border': 1,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'black',
            'font_color': 'white',

        })
    def table_header_format2(self, workbook):
        return workbook.add_format({
            'bold': 1,
            'border': 0,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#7c7d7c',
            'font_color': 'white',

        })
    def table_header_format3(self, workbook):
        return workbook.add_format({
            'bold': 1,
            'border': 0,
            'font_size': 9,
            'align': 'left',
            'valign': 'vcenter',
            'font_color': 'black',

        })
    def table_header_format4(self, workbook):
        return workbook.add_format({
            'bold': 0,
            'border': 0,
            'font_size': 9,
            'align': 'left',
            'valign': 'vcenter',
            'font_color': 'black',

        })
    def table_content_format(self, workbook):
        return workbook.add_format({
            'bold': 0,
            'border': 1,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'black',

        })
    def header_format(self, workbook):
        return workbook.add_format({
            'font_size': 13,
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': 'gray',
            'bold': True
        })
    def header2_format(self, workbook):
        return workbook.add_format({
            'font_size': 14,
            'font_color': 'white',
            'align': 'center',
            'bg_color': '#13024f',
            'bold': True
        })
