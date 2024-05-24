from odoo import models
import datetime
from datetime import date, datetime, time, timedelta
from pytz import timezone
import xlsxwriter
import xlwt


class PartnerXlsx(models.AbstractModel):
    _name = 'report.bom_structure_excel_report.all_product_excel'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, boms):

        sheet = workbook.add_worksheet("BoM Structure & Cost Excel Report")
        bold = workbook.add_format({'bold': True})
        sheet.set_column('A:A',70)

        sheet.set_column('B:G',25)
        sheet.set_column('H:I',40)

        header_format1 = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'align': 'center',
            'font_color': 'Blue',
            'bold': True,
            'valign': 'vcenter',
            'border_color': 'black',
            'fg_color': 'yellow',
            })
        header_format2 = workbook.add_format({
            'font_size': 18,
            'border': 1,
            'align': 'center',
            'font_color': 'black',
            'bold': True,
            'valign': 'vcenter',
            'border_color': 'black',
            })
        header_format3 = workbook.add_format({
            'font_size': 14,
            'border': 1,
            'align': 'center',
            'font_color': 'black',
            'bold': True,
            'valign': 'vcenter',
            'border_color': 'black',
            'fg_color': '#C0C0C0'})

        row = 0

        for obj in boms:
            bom_id = self.env['mrp.bom'].browse(obj.id)
            candidates = bom_id.product_id or bom_id.product_tmpl_id.product_variant_ids
            quantity = bom_id.product_qty
            data = {}
            docs = []
            print(data)
            print('================================', candidates)
            # for product_variant_id in candidates:
            for product_variant_id in candidates.ids:
                data = self.env['report.mrp.report_bom_structure']._get_pdf_line(bom_id.id,
                                                                                 product_id=product_variant_id,
                                                                                 qty=quantity, unfolded=True)
                docs.append(data)
            #     print(docs)
            #
            # print(obj.product_tmpl_id.name)
            # print(obj.code)
            for line in docs:
                if line and line.get('components') or line.get('lines'):
                    sheet.merge_range('A1:F1', 'BoM Structure & Cost', header_format2)
                    row+=1
                    sheet.write(row,0, line['bom_prod_name'],bold )
                    row += 2
                    if line['bom'].code:
                        sheet.write(row, 0, 'Reference:',bold )
                        sheet.write(row,1, line['bom'].code,bold )
                        row += 1
                    row +=1
                    currency_id = line['currency']

                    # Table
                    sheet.write(row, 0, 'Product',header_format3 )
                    sheet.write(row, 1, 'BoM',header_format3 )
                    sheet.write(row, 2, 'Quantity', header_format3)
                    sheet.write(row, 3, 'Unit of Measure',header_format3 )
                    sheet.write(row, 4, 'Product Cost',header_format3 )
                    sheet.write(row, 5, 'BoM Cost', header_format3)

                    row += 1
                    sheet.write(row, 0, line['bom_prod_name'],header_format1 )
                    sheet.write(row, 1, line['code'],header_format1 )
                    bom_qty = format(line['bom_qty'], '.2f',)
                    sheet.write(row, 2, bom_qty,header_format1 )
                    sheet.write(row, 3, line['bom'].product_uom_id.name,header_format1 )
                    price_unit = format(line['price'], '.2f')
                    total_price = format(line['total'], '.2f')
                    if currency_id and currency_id.position == 'after':
                        price_unit = str(price_unit) + ' ' + currency_id.symbol
                        total_price = str(total_price) + ' ' + currency_id.symbol
                    if currency_id and currency_id.position == 'before':
                        price_unit = currency_id.symbol + ' ' + str(price_unit)
                        total_price = currency_id.symbol + ' ' + str(total_price)
                    sheet.write(row, 4, price_unit,header_format1 )
                    sheet.write(row, 5, total_price,header_format1 )

                    row += 1
                    print(len(line['lines']))
                    print('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz')
                    print(line['lines'])
                    print(line.get('lines'))
                    i = 1

                    for l in line['lines']:

                        if l['level'] != 0 and l['level'] !=1 and l['level'] !=2:
                            space_td = '       ' * (l['level'])
                        elif l['level'] == 1:
                            space_td =str(i) +' -'+ '   ' * (l['level'])
                            i += 1
                            j = 1
                        elif l['level'] == 2:
                            space_td ='   '+str(j) +' -'+  '   ' * (l['level'])
                            j += 1

                        else:
                            space_td = '       '
                        product_name = space_td + ' ' + l['name']
                        print(l['level'])
                        print(product_name)
                        sheet.write(row, 0, product_name, )
                        if l.get('code'):
                            sheet.write(row, 1, l['code'], )
                        quantity = format(l['quantity'], '.2f')
                        sheet.write(row, 2, quantity, )
                        if self.user_has_groups('uom.group_uom'):
                            sheet.write(row, 3, l['uom'], )
                        if 'prod_cost' in l:
                            price_unit = format(l['prod_cost'], '.2f')
                            if currency_id and currency_id.position == 'after':
                                price_unit = str(price_unit) + ' ' + currency_id.symbol
                            if currency_id and currency_id.position == 'before':
                                price_unit = currency_id.symbol + ' ' + str(price_unit)
                            sheet.write(row, 4, price_unit, )

                        total_price = format(l['bom_cost'], '.2f')
                        if currency_id and currency_id.position == 'after':
                            total_price = str(total_price) + ' ' + currency_id.symbol
                        if currency_id and currency_id.position == 'before':
                            total_price = currency_id.symbol + ' ' + str(total_price)
                        sheet.write(row, 5, total_price, )
                        row += 1
                    row += 1
                    sheet.write(row, 3, 'Unit Cost', )
                    product_cost_total = line['price'] / line['bom_qty']
                    product_cost_total = format(product_cost_total, '.2f')
                    if currency_id and currency_id.position == 'after':
                        product_cost_total = str(product_cost_total) + ' ' + currency_id.symbol
                    if currency_id and currency_id.position == 'before':
                        product_cost_total = currency_id.symbol + ' ' + str(product_cost_total)
                    sheet.write(row, 4, product_cost_total, )
                    bom_cost_total = line['total'] / line['bom_qty']
                    bom_cost_total = format(bom_cost_total, '.2f')
                    if currency_id and currency_id.position == 'after':
                        bom_cost_total = str(bom_cost_total) + ' ' + currency_id.symbol
                    if currency_id and currency_id.position == 'before':
                        bom_cost_total = currency_id.symbol + ' ' + str(bom_cost_total)
                    sheet.write(row, 5, bom_cost_total, )
                    row += 4
                else:
                    sheet.merge_range(0, 1, 0, 6, 'No data available.', )
                    row += 4
