# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import UserError
import functools
import json
import datetime
import pytz
import base64
import werkzeug


def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):

        try:
            auth = request.httprequest.headers.get('Authorization')
            if not auth:
                raise UserError("Authorisation Header Not Found")
            if not auth.startswith('Basic '):
                raise UserError("Format Error in the Authorisation Header")
            user_pass64 = auth.strip('Basic ')
            # user_pass = base64.b64decode(user_pass64)
            # if user_pass != 'apiuser:apiuser':
            #     raise UserError("Authorization Error")
            if user_pass64 != '9b816457176198a9f7f10d3570a2c740b71b96c5':
                raise UserError("Authorization failed")
        except:
            raise UserError("Authorization failed")
        return func(self, *args, **kwargs)

    return wrap


class HcAttendanceApi(http.Controller):

    @validate_token
    @http.route('/add_emp_attendance', type="json", auth="none", methods=['POST'])
    def add_employee_attendance(self, **kw):

        response_vals = {
            "statusCode": 200,
            "statusDescription": "failed",
            "error": "Error in Creating Attendance Raw Data."
        }

        # {"params":
        #     {
        #         "att_data": "[{'employee_id': 'Employee ID',
        #         'punched_time': 'dd/mm/yyyy HH:MM:SS',
        #         'device_id': 'Device ID',
        #         'is_checkin': true/false,
        #         'state': 'STATE'}]"
        #     }}

        def create_api_logs():
            log_vals = {
                'name': 'add_emp_attendance',
                'input': kw,
                'output': response_vals,
                'status_description': response_vals['statusDescription'],
                'datetime': datetime.datetime.now(),
                'status_code': response_vals['statusCode'],
                'return_message': response_vals['datas'] if 'datas' in response_vals else response_vals[
                    'error'] if 'error' in response_vals else None,
            }
            request.env['hc.api.logs'].sudo().create(log_vals)

        try:
            if 'att_data' not in kw.keys() or not kw.get('att_data'):
                raise UserError("Wrong Input Data.")
            att_data = kw.get('att_data')
            if not att_data:
                raise UserError("Employee Data Not Found.")
            raw_attendance_details = []
            for datas in att_data:
                if 'employee_id' not in datas.keys() or not datas.get(
                        'employee_id') or 'punched_time' not in datas.keys() or not datas.get(
                    'punched_time') or 'device_id' not in datas.keys() or not datas.get(
                    'device_id') or 'state' not in datas.keys() or not datas.get('state'):
                    raise UserError("Wrong Employee Data.")
                employee_id = request.env['hr.employee'].sudo().search([('employee_id', '=', datas.get('employee_id'))],
                                                                       limit=1)
                device_id = request.env['hc.attendance.device'].sudo().search([('device_id', '=', datas.get('device_id'))], limit=1)
                if not device_id:
                    raise UserError("Device ID Not Found.")
                if not employee_id:
                    raise UserError("Employee Not Found.")
                datas['employee_id'] = employee_id.id

                local = pytz.timezone("Asia/Dubai")
                naive = datetime.datetime.strptime(datas.get('punched_time'), '%Y-%m-%d %H:%M:%S')
                local_dt = local.localize(naive, is_dst=None)
                utc_dt = local_dt.astimezone(pytz.utc)

                datas['punched_time'] = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                datas['is_checkin'] = datas.get('is_checkin')
                vals = {
                    'employee_id': datas['employee_id'],
                    'branch_id': device_id.branch_id.id,
                    'punched_time': datas['punched_time'],
                    'is_checkin': datas['is_checkin'],
                    'state': datas.get('state'),
                }
                raw_attendance_details.append(vals)
            for val in raw_attendance_details:
                raw_data = request.env['hc.raw.attendance'].sudo().create(val)
            # for datas in att_data:
            #     raw_data = request.env['hc.raw.attendance'].sudo().create(datas)
            response_vals = {
                "statusCode": 200,
                "statusDescription": "success",
                # "raw_data_id": raw_data.id,
                "datas": "Created Attendance Raw Data Successfully."}

        except Exception as e:
            response_vals["error"] = str(e)
        create_api_logs()
        return json.loads(json.dumps(response_vals))


