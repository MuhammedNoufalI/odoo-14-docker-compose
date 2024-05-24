# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, fields, exceptions,_
from odoo.http import request
from odoo.addons.website_form.controllers.main import WebsiteForm
import base64

import werkzeug
import json
# class WebsiteFormInherit(WebsiteForm):
class WebsiteFormLoan(http.Controller):

    @http.route(['/loan/request/form'], type='http', method="POST", auth="public", website=True)
    def loan_request_form(self, **kwargs):
        vals = self.get_default_vals(kwargs)
        return request.render("loan_portal.loan_portal_request_form",vals)

    @http.route(['/my/loan/requests'], type='http', method="POST", auth="public", website=True)
    def my_loan_requests(self, **kwargs):
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        my_requests = self.get_my_requests()
        return request.render("loan_portal.my_loan_requests",
                              {'my_requests': my_requests})

    @http.route(['/loan/request/create'], type='http', method="POST", auth="public", website=True)
    def portal_loan_request_insert(self, **kwargs):
        try:
            emp = int(kwargs.get('employee'))
            emp = request.env['hr.employee'].browse(emp)
            loan = request.env['hr.loan'].create({
                                                   'date': kwargs.get('date'),
                                                   'payment_date': kwargs.get('start_date'),
                                                   'loan_amount': float(kwargs.get('loan_amount')),
                                                   'employee_id': emp.id,
                                                   'department_id':emp.department_id.id ,
                                                   'job_position':emp.job_id.id ,
                                                   'installment':int(kwargs.get('installment')) if kwargs.get('installment') else 0,
                                                    })

        except Exception as e:
            warn = str(self.prepare_error_msg(e))
            vals = self.get_default_vals(kwargs)
            vals.update({'warn_message':warn})
            return request.render("loan_portal.loan_portal_request_form",vals)
        vals = self.get_default_vals({})
        vals.update({'pass_message': True,'request_id': loan})
        return request.render("loan_portal.loan_portal_request_form",vals)
        # return request.render("custody_portal.request_created", {'request_id': custody})

    @http.route(["/loan/request/<int:request_id>"], type='http', auth="public", website=True)
    def loan_request_view(self, request_id=None, **kw):
        loan_request_id = request.env['hr.loan'].browse(int(request_id))
        return request.render("loan_portal.requests_followup", {'loan_request_id': loan_request_id})
##@@@@@@@@@@@@@@@@@@
    @http.route(['/salary/advance/request/form'], type='http', method="POST", auth="public", website=True)
    def salary_advance_request_form(self, **kwargs):
        vals = self.get_default_salary_vals(kwargs)
        return request.render("loan_portal.salary_advance_portal_request_form", vals)

    @http.route(['/my/salary/advance/requests'], type='http', method="POST", auth="public", website=True)
    def my_requests(self, **kwargs):
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        my_requests = self.get_my_salary_requests()
        return request.render("loan_portal.my_salary_advance_requests",
                              {'my_requests': my_requests})

    @http.route(['/salary/advance/request/create'], type='http', method="POST", auth="public", website=True)
    def portal_request_insert(self, **kwargs):
        try:
            emp = int(kwargs.get('employee'))
            emp = request.env['hr.employee'].browse(emp)
            salary = request.env['salary.advance'].create({
                'date': kwargs.get('date'),
                'advance': float(kwargs.get('advance')),
                'employee_id': emp.id,
                'department': emp.department_id.id,
                'credit': int(kwargs.get('credit')) if (kwargs.get('credit')) else False,
                'debit': int(kwargs.get('debit')) if (kwargs.get('debit')) else False,
                'reason': kwargs.get('reason'),
                'journal': int(kwargs.get('journal')) if (kwargs.get('journal')) else False,
                'exceed_condition': bool(kwargs.get('exceed_condition')) if (kwargs.get('exceed_condition')) else False,
            })

        except Exception as e:
            warn = str(self.prepare_error_msg(e))
            vals = self.get_default_salary_vals(kwargs)
            vals.update({'warn_message': warn})
            return request.render("loan_portal.salary_advance_portal_request_form", vals)
        vals = self.get_default_salary_vals({})
        vals.update({'pass_message': True, 'salary_request_id': salary})
        return request.render("loan_portal.salary_advance_portal_request_form", vals)

    @http.route(["/salary/advance/request/<int:salary_request_id>"], type='http', auth="public", website=True)
    def salary_request_view(self, salary_request_id=None, **kw):
        salary_request_id = request.env['salary.advance'].browse(int(salary_request_id))
        return request.render("loan_portal.salary_requests_followup", {'salary_request_id': salary_request_id})

    ##@@@@@@@@@@@@@@@@@@

    def prepare_error_msg(self, e):
        msg = ''
        if hasattr(e, 'name'):
            msg += e.name
        elif hasattr(e, 'msg'):
            msg += e.msg
        elif hasattr(e, 'args'):
            msg += e.args[0]
        return msg

    def get_default_vals(self,kwargs):
            default_values={}
            employees = self.get_employees()
            if kwargs != {}:
                default_values['date'] = kwargs.get('date')
                default_values['start_date'] = kwargs.get('start_date')
                default_values['loan_amount'] = kwargs.get('loan_amount')
                default_values['installment'] = kwargs.get('installment')
                employee = employees.browse(int(kwargs.get('employee')))
                department = employee.department_id
                job = employee.job_id
            else:
                employee =  employees.filtered(lambda x:x.user_id == request.env.user)
                department = employee.department_id
                job = employee.job_id

                default_values['date'] = fields.date.today()
                default_values['start_date'] = fields.date.today()
                default_values['loan_amount'] = 0.0

            return {
                   'employees': employees.filtered(lambda x:x != employee),
                   'employee': employee,
                   'department': department.name,
                   'job': job.name,
                   'default_values': default_values}
    def get_default_salary_vals(self,kwargs):
            default_values={}
            employees = self.get_employees()
            journals = self.get_journals()
            credits = self.get_credits()
            debits = credits
            emp = request.env['hr.employee']
            print(kwargs)
            if kwargs != {}:
                default_values['date'] = kwargs.get('date')
                default_values['reason'] = kwargs.get('reason')
                default_values['exceed_condition'] = kwargs.get('exceed_condition')
                employee = employees.browse(int(kwargs.get('employee'))) if kwargs.get('employee') else emp
                department = kwargs.get('department')
            else:

                employee = employees[0] if employees else employees
                default_values['date'] = fields.date.today()
                default_values['reason'] = ''
                department = employee.department_id.name


            return {

                'department':department,

                'employees': employees.filtered(lambda x: x != employee),
                'employee': employee,
                'default_values': default_values}
    def get_employees(self):
        return request.env['hr.employee'].sudo().search([('user_id','=',request.env.user.id)])
    def get_departments(self):
        return request.env['hr.department'].sudo().search([])
    def get_jobs(self):
        return request.env['hr.job'].sudo().search([])

    def get_my_requests(self):
        return request.env['hr.loan'].sudo().search([('employee_id.user_id', '=', request.env.user.id)])
    def get_journals(self):
        return request.env['account.journal'].sudo().search([('company_id', '=', request.env.user.company_id.id)])
    def get_credits(self):
        return request.env['account.account'].sudo().search([('company_id', '=', request.env.user.company_id.id)])
    def get_my_salary_requests(self):
        return request.env['salary.advance'].sudo().search([('employee_id.user_id', '=', request.env.user.id)])

