from odoo import models, fields, api, _
import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import base64


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def generate_report(self, order_vals, date_start=None, date_end=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        date_format = workbook.add_format({'font_size': '12px', 'num_format': 'dd/mm/yy hh:mm'})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        sub_head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10px'})
        txt = workbook.add_format({'font_size': '10px'})
        sheet.merge_range('B2:I3', 'Pos Order Report', head)
        sheet.set_column(0, 14, 15)
        # sheet.write('B6', 'From:', cell_format)
        # sheet.merge_range('C6:D6', date_start, date_format)
        # sheet.write('F6', 'To:', cell_format)
        # sheet.merge_range('G6:H6', date_end, date_format)

        sheet.write('A8', 'Order Date:', cell_format)
        sheet.write('B8', 'Order# :', cell_format)
        sheet.write('C8', 'Session# :', cell_format)
        sheet.write('D8', 'Product Code:', cell_format)
        sheet.write('E8', 'Product Name:', cell_format)
        sheet.write('F8', 'Quantity:', cell_format)
        sheet.write('G8', 'UOM:', cell_format)
        sheet.write('H8', 'Unit Price:', cell_format)
        sheet.write('I8', 'Total Price:', cell_format)
        sheet.write('J8', 'Margin:', cell_format)
        sheet.write('K8', 'BOM:', cell_format)
        sheet.write('L8', 'Components:', cell_format)
        sheet.write('M8', 'C. QTY:', cell_format)
        sheet.write('N8', 'C. UOM:', cell_format)
        sheet.write('O8', 'C. Cost:', cell_format)
        i = 8
        for line in order_vals:
            sheet.write(i, 0, line['order_date'], date_format)
            sheet.write(i, 1, line['order_name'], cell_format)
            sheet.write(i, 2, line['session'], cell_format)
            for order_line in line['line_ids']:
                sheet.write(i, 3, order_line['product_code'], cell_format)
                sheet.write(i, 4, order_line['product_name'], cell_format)
                sheet.write(i, 5, order_line['qty'], cell_format)
                sheet.write(i, 6, order_line['uom'], cell_format)
                sheet.write(i, 7, order_line['unit_price'], cell_format)
                sheet.write(i, 8, order_line['total_price'], cell_format)
                sheet.write(i, 9, order_line['margin'], cell_format)
                sheet.write(i, 10, order_line['bom'], cell_format)
                for bom_lines in order_line['component_vals']:
                    sheet.write(i, 11, bom_lines['component'], cell_format)
                    sheet.write(i, 12, bom_lines['c_qty'], cell_format)
                    sheet.write(i, 13, bom_lines['c_uom'], cell_format)
                    sheet.write(i, 14, bom_lines['c_cost'], cell_format)
                    i += 1
            i += 1
        workbook.close()
        output.seek(0)
        xlsdata = output.getvalue()
        output.close()
        return xlsdata

    def get_report_values(self, date_start=None, date_end=None):
        order_vals_list = []
        for order in self:
            order_vals = {
                'order_date': order.date_order,
                'order_name': order.name,
                'session': order.session_id.name,
                'line_ids': order.lines.generate_order_line_values()
            }
            order_vals_list.append(order_vals)
        data = self.generate_report(order_vals_list)
        fb = base64.encodebytes(data)
        attachment = self.env['ir.attachment'].with_user(2).create({
            'name': 'Employee Performance Report.xls',
            'type': 'binary',
            'datas': fb,
        })
        url = "/pos_order/mrp/excel_report?id=%s&model=%s" % (attachment.id, 'ir.attachment')
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'no_destroy': True,
            'target': 'current'
        }


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    def get_component_cost(self, line):
        picking = self.env['stock.picking'].search([('pos_order_id', '=', self.order_id.id)])
        if not picking:
            picking = self.env['stock.picking'].search([('pos_session_id', '=', self.order_id.session_id.id)])
        move_id = picking.move_ids_without_package.filtered(lambda x: x.bom_line_id.id == line.id)
        valuation_line = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move_id.id)], limit=1)
        return valuation_line.quantity, valuation_line.value

    def get_component_cost_from_product(self, product):
        picking = self.env['stock.picking'].search([('pos_order_id', '=', self.order_id.id)])
        if not picking:
            picking = self.env['stock.picking'].search([('pos_session_id', '=', self.order_id.session_id.id)])
        move_id = picking.move_ids_without_package.filtered(lambda x: x.product_id.id == product.id)
        valuation_line = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move_id.id)], limit=1)
        return valuation_line.quantity, valuation_line.value

    def get_sub_product_values(self, product):
        inner_bom = self.env['mrp.bom'].search(
            [('product_tmpl_id', '=', product.product_tmpl_id.id), ('type', '=', 'phantom')], order='sequence asc',
            limit=1)
        inner_components = []
        inner_total_c_cost = 0

        for line in inner_bom.bom_line_ids:

            if not self.env['mrp.bom'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id), ('type', '=', 'phantom')]):
                c_qty, c_value = self.get_component_cost(line)
                inner_total_c_cost += abs(c_value)
                vals = {
                    'component': line.product_id.name,
                    'c_qty': abs(c_qty),
                    'c_uom': line.product_id.uom_id.name,
                    'c_cost': abs(c_value)
                }
                inner_components.append(vals)
            else:
                inner_sub_comp, carry_cost = self.get_sub_product_values(line.product_id)
                inner_total_c_cost += carry_cost
                for rec in inner_sub_comp:
                    inner_components.append(rec)
        return inner_components, inner_total_c_cost

    def get_component_values(self):
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id), ('type', '=', 'phantom')], order='sequence asc', limit=1)
        components = []
        total_c_cost = 0
        if bom:
            for line in bom.bom_line_ids:
                if not self.env['mrp.bom'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id), ('type', '=', 'phantom')]):
                    c_qty, c_value = self.get_component_cost(line)
                    total_c_cost += abs(c_value)
                    vals = {
                        'component': line.product_id.name,
                        'c_qty': abs(c_qty),
                        'c_uom': line.product_id.uom_id.name,
                        'c_cost': abs(c_value)
                    }
                    components.append(vals)
                else:
                    sub_comp, outer_carry_cost = self.get_sub_product_values(line.product_id)
                    total_c_cost += outer_carry_cost
                    for rec in sub_comp:
                        components.append(rec)
        else:

            c_qty, c_value = self.get_component_cost_from_product(self.product_id)
            total_c_cost += abs(c_value)
            vals = {
                'component': self.product_id.name,
                'c_qty': abs(c_qty),
                'c_uom': self.product_uom_id.name,
                'c_cost': abs(c_value)
            }
            components.append(vals)
        return components, total_c_cost

    def generate_order_line_values(self):
        line_values = []
        for line in self:
            bom = self.env['mrp.bom'].search(
                [('product_tmpl_id', '=', line.product_id.product_tmpl_id.id), ('type', '=', 'phantom')],order='sequence asc', limit=1)
            component_vals, total_c_cost = line.get_component_values()
            vals = {
                'product_code': line.product_id.default_code,
                'product_name': line.product_id.name,
                'qty': line.qty,
                'unit_price': line.price_unit,
                'total_price': line.price_unit * line.qty,
                'margin': (line.price_unit * line.qty) - total_c_cost,
                'uom': line.product_uom_id.name,
                'bom': bom.product_tmpl_id.name if bom else None,
                'component_vals': component_vals
            }
            line_values.append(vals)
        return line_values
