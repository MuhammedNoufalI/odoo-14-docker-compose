# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.exceptions import AccessError, MissingError
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception, Response
from datetime import datetime, timedelta
from odoo.addons.portal.controllers.mail import _message_post_helper
from datetime import date
from collections import ChainMap
from pytz import timezone, utc
from time import gmtime, strftime
import calendar
import base64
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
import json
from datetime import date

from odoo import models, fields, api, exceptions, _
from odoo.osv import osv


class PortalAccount(PortalAccount):
    # MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id"]
    # OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "mobile"]
    @http.route(['/my/employee/data'], type='http', auth="public", website=True)
    def portal_hr_employee_detail(self, **kw):
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)

        if employee:
            level = ['master', 'bachelor', 'other', ]
            marital = ['single', 'married', 'cohabitant', 'widower', 'divorced']
            return request.render("employee_portal.website_hr_employee_portal",
                                  {'employee': employee or [], 'level': level, 'marital': marital,
                                   })
        else:
            return request.render("web.login")

    @http.route(['/my/employee/data/insert'], type='http', method="post", auth="public", website=True)
    def portal_hr_employee_detail_submit(self, **kw):
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        marital = ['single', 'married', 'cohabitant', 'widower', 'divorced']
        level = ['master', 'bachelor', 'other', ]

        employee.name = kw['full_name']
        employee.birthday = kw['birthday']
        employee.place_of_birth = kw['place_of_birth']
        employee.marital = kw['marital']
        employee.certificate = kw['certificate']
        employee.study_school = kw['study_school']
        employee.study_field = kw['study_field']
        return request.render("employee_portal.website_hr_employee_portal",
                              {'employee': employee or [], 'level': level, 'marital': marital,
                               'message': 'Your Profile has been Updated'})

    @http.route(['/my/requests'], type='http', auth="public", website=True)
    def portal_requests_detail(self, **kw):
        return request.render("employee_portal.website_hr_request_portal")

    @http.route(['/my/leaves'], type='http', auth="public", website=True)
    def portal_hr_leaves_detail(self, **kw):
        leaves_types = request.env['hr.leave.type'].sudo().search([])
        # conditions_types = request.env['leave.condition'].sudo().search_read([], ['name'])
        return request.render("employee_portal.website_hr_leaves",
                              {
                                  'leaves_types': leaves_types or [],
                                  # 'conditions_types': conditions_types or [],
                              })
    @http.route(['/attendances'], type='http', auth="public", website=True)
    def portal_employee_attendance(self, **kw):
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        attendance = request.env['hr.attendance'].sudo().search([('employee_id', '=', employee[0].id)])
        import datetime
        attendance_final = []
        if attendance:
            for line in attendance:
                attendance_dic = {'employee_id': line.employee_id.name,
                                  'check_in': line.check_in,
                                  'check_out': line.check_out,
                                  }
                attendance_final.append(attendance_dic)
        return request.render("employee_portal.website_employee_attendance", {'attendance': attendance_final or []})

    @http.route(['/my/leaves/history'], type='http', auth="public", website=True)
    def portal_hr_leaves_history(self, **kw):
        login_employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        if login_employee:
            remaining_leaves = login_employee[0].remaining_leaves
            leaves_history = request.env['hr.leave'].sudo().search([('employee_id', '=', login_employee[0].id)])
            active_leaves_history = request.env['hr.leave'].sudo().search(
                [('employee_id', '=', login_employee[0].id), ('state', 'in', ['draft', 'confirm'])])
            return request.render("employee_portal.website_hr_leaves_history",
                                  {'leaves_history': leaves_history or [], 'remaining_leaves': remaining_leaves,
                                   'active_leaves_history': active_leaves_history},
                                  )

    @http.route(['/my/payslip/history'], type='http', auth="public", website=True)
    def portal_hr_payslip_history(self, **kw):
        login_employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        if login_employee:
            payslip_history = request.env['hr.payslip'].sudo().search([('employee_id', '=', login_employee[0].id)])
            return request.render("employee_portal.website_hr_payslip_history",
                                  {'payslip_history': payslip_history or []})

    @http.route(['/my/payslip/history/id=<int:payslip_id>'], type='http', auth="public", website=True)
    def portal_hr_payslip_history_line(self, payslip_id, **kw):
        login_employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.uid)], limit=1)
        if login_employee:
            pdf, _ = request.env.ref('hr_payroll.action_report_payslip').sudo().render(payslip_id)
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)


    def prepare_error_msg(self, e):
        msg = ''
        if hasattr(e, 'name'):
            msg += e.name
        elif hasattr(e, 'msg'):
            msg += e.msg
        elif hasattr(e, 'args'):
            msg += e.args[0]
        return msg
