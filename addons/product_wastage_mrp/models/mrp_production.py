# -*- coding: utf-8 -*-

import json
import datetime
import math
import operator as py_operator
import re

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date

SIZE_BACK_ORDER_NUMERING = 3


class StockMove(models.Model):
    _inherit = 'stock.move'

    yeild_wastage = fields.Float(string="Wastage(%)", required=False, )
    yeild_wastage_amount = fields.Float(string="Wastage", required=False )

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        source_location = self.location_src_id
        waste_amount = bom_line.yeild_wastage * product_uom_qty / 100
        data = {
            'sequence': bom_line.sequence if bom_line else 10,
            'name': self.name,
            'date': self.date_planned_start,
            'date_deadline': self.date_planned_start,
            'bom_line_id': bom_line.id if bom_line else False,
            'picking_type_id': self.picking_type_id.id,
            'product_id': product_id.id,
            'yeild_wastage': bom_line.yeild_wastage,
            'yeild_wastage_amount': waste_amount,
            'product_uom_qty': product_uom_qty + waste_amount,
            'product_uom': product_uom.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.with_company(self.company_id).property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': operation_id,
            'price_unit': product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'state': 'draft',
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
        }
        return data


