# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, fields, exceptions,_
from odoo.http import request
from odoo.addons.website_form.controllers.main import WebsiteForm
import base64

import werkzeug
import json
# class WebsiteFormInherit(WebsiteForm):
class WebsiteFormExpense(http.Controller):

    @http.route(['/expense/request/form'], type='http', method="POST", auth="public", website=True)
    def expense_request_form(self, **kwargs):
        vals = self.get_default_vals(kwargs)
        return request.render("expense_portal.expense_portal_request_form",vals)

    @http.route(['/my/expense/requests'], type='http', method="POST", auth="public", website=True)
    def my_expense_requests(self, **kwargs):
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        my_requests = self.get_my_requests()
        return request.render("expense_portal.my_expense_requests",
                              {'my_requests': my_requests})

    @http.route(['/expense/request/create'], type='http', method="POST", auth="public", website=True)
    def portal_expense_request_insert(self, **kwargs):
        try:
            emp = int(kwargs.get('employee'))
            emp = request.env['hr.employee'].browse(emp)
            expense = request.env['hr.expense'].create({
                                                   'name': kwargs.get('description'),
                                                   'date': kwargs.get('date'),
                                                   'unit_amount': float(kwargs.get('unit_price')),
                                                   'employee_id': emp.id,
                                                   'product_id':int(kwargs.get('product')) ,
                                                   'quantity':int(kwargs.get('quantity')),
                                                   'payment_mode':'own_account',
                                                    })

        except Exception as e:
            warn = str(self.prepare_error_msg(e))
            vals = self.get_default_vals(kwargs)
            vals.update({'warn_message':warn})
            return request.render("expense_portal.expense_portal_request_form",vals)
        vals = self.get_default_vals({})
        vals.update({'pass_message': True,'expense_request_id': expense})
        return request.render("expense_portal.expense_portal_request_form",vals)
        # return request.render("custody_portal.request_created", {'expense_request_id': custody})

    @http.route(["/expense/request/<int:expense_request_id>"], type='http', auth="public", website=True)
    def expense_request_view(self, expense_request_id=None, **kw):
        expense_request_id = request.env['hr.expense'].browse(int(expense_request_id))
        return request.render("expense_portal.requests_followup", {'expense_request_id': expense_request_id})


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
            employee = self.get_employees()
            products = self.get_products()
            if kwargs != {}:
                default_values['date'] = kwargs.get('date')
                default_values['description'] = kwargs.get('description')
                default_values['quantity'] = int(kwargs.get('quantity')) if kwargs.get('quantity') else 1
                default_values['unit_price'] = kwargs.get('unit_price')
                default_values['total'] = kwargs.get('total')
                employee = employee
                product = products.browse(int(kwargs.get('product')))

            else:
                default_values['date'] = fields.date.today()
                default_values['unit_price'] = products[0].standard_price if products[0] else 0
                default_values['quantity'] = 1

                default_values['total'] = products[0].standard_price if products[0] else 0.0
                product = request.env['product.product']

            return {
                   'employees': employee,
                   'employee': employee,
                   'products': products,
                   'product': product,
                   'default_values': default_values}
    def get_employees(self):
        return request.env['hr.employee'].sudo().search([('user_id','=',request.env.user.id)],limit=1)
    def get_products(self):
        return request.env['product.product'].sudo().search([('can_be_expensed','=',True)])
    def get_my_requests(self):
        return request.env['hr.expense'].sudo().search([('employee_id.user_id', '=', request.env.user.id)])
