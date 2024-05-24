from odoo.http import Controller, request, route, content_disposition
import base64


class XlsxReportDownload(Controller):
    @route("/pos_order/mrp/excel_report", type='http', auth="public")
    def download_excel_report(self, **kwrgs):
        attachment = request.env[kwrgs['model']].with_user(2).search([('id','=', int(kwrgs['id']))])
        report_name = "Pos Order Report"
        data = base64.b64decode(attachment.datas)
        attachment.with_user(2).unlink()
        return request.make_response(data, headers=[
            ('Content-Type', 'application/vnd.ms-excel'),
            ('Content-Disposition', content_disposition(report_name + '.xlsx'))])
