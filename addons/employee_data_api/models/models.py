from dateutil.tz import UTC
from odoo import models, fields, api, _
import time
import requests
import json
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_is_zero, float_compare
from datetime import date, timedelta, datetime


class EmployeeDataSync(models.Model):
    _inherit = 'hr.attendance'

    device_check_in = fields.Char("Device Check in")
    device_check_out = fields.Char("Device Check Out")

    def get_employee_record(self):
        url_attendance = 'http://myrra.lenvica.com/AttendHRM_MIS/dll/mis.dll/zk_teco/get_punch_data'
        headers = {
            "Content-Type": "application/json",
            "id_token": 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJEZWxwaGkgSk9TRSBMaWJyYXJ5IiwiaWF0IjoxNjY3Mjk0NjI0LCJleHAiOjE2NjczMDE4MjQsImVtcGlkIjoxMTgsInVzcmlkIjoxMDMsIndncmlkIjoxMDEsImFwcHR5cGUiOjF9.mPu5LbW_sd5MKdj5n-3xrltaFVNVCgHJkrRsJBH5fiI'
        }

        response_attendance = requests.get(url_attendance, headers=headers)
        a = response_attendance.json()

        url_employee = 'http://myrra.lenvica.com/AttendHRM_MIS/dll/mis.dll/login/admin?uname=demo&password=demo'
        response_employee = requests.get(url_employee)
        b = response_employee.json()

        for rec in a['punches']:
            if self.env['hr.employee'].browse([('barcode', '=', rec['BadgeNumber'])]):
                emp_record = self.env['hr.employee'].update({
                    'company_id': rec['CompanyName'],
                    'barcode': rec['BadgeNumber'],
                })

            if self.env['hr.employee'].search([('registration_number', '=', rec['BadgeNumber'])]):
                name = self.env['hr.employee'].search([('registration_number', '=', rec['BadgeNumber'])])
                name1 = name.name
                nns = name1
                if rec['PunchDateTime']:
                    if rec["PunchType"] == 1:
                        attendance_record = self.env['hr.attendance'].sudo().create({
                            'employee_id': self.env['hr.employee'].search(
                                [('registration_number', '=', rec['BadgeNumber'])]).id,
                            'check_in': datetime.strptime(rec['PunchDateTime'], "%d-%m-%Y %H:%M:%S").astimezone(
                                UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'check_out': datetime.strptime(rec['PunchDateTime'], "%d-%m-%Y %H:%M:%S").astimezone(
                                UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'checkin_device_id': self.env['attendance.device'].search([]).serialnumber == rec[
                                'DeviceId'],
                        })

    def update_employee_record(self):
        url_attendance = 'http://myrra.lenvica.com/AttendHRM_MIS/dll/mis.dll/zk_teco/get_punch_data'
        headers = {
            "Content-Type": "application/json",
            "id_token": 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJEZWxwaGkgSk9TRSBMaWJyYXJ5IiwiaWF0IjoxNjY3Mjk0NjI0LCJleHAiOjE2NjczMDE4MjQsImVtcGlkIjoxMTgsInVzcmlkIjoxMDMsIndncmlkIjoxMDEsImFwcHR5cGUiOjF9.mPu5LbW_sd5MKdj5n-3xrltaFVNVCgHJkrRsJBH5fiI'
        }

        response_attendance = requests.get(url_attendance, headers=headers)
        a = response_attendance.json()
        for rec in a['punches']:
            if self.env['hr.employee'].search([('registration_number', '=', rec['BadgeNumber'])]):
                if rec['PunchDateTime']:
                    if rec["PunchType"] == 0:
                        for emp in self.env['hr.attendance'].search([]).employee_id:
                            if emp.id == self.env['hr.employee'].search(
                                    [('registration_number', '=', rec['BadgeNumber'])]).id:
                                attendance_record2 = self.env['hr.attendance'].sudo().update({
                                    'check_out': datetime.strptime(rec['PunchDateTime'],
                                                                   "%d-%m-%Y %H:%M:%S").astimezone(UTC).strftime(
                                        DEFAULT_SERVER_DATETIME_FORMAT),
                                })
