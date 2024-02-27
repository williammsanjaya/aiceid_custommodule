# -*- coding: utf-8 -*-

from odoo import models, fields, api



class PurchaseOrder(models.Model):
    _inherit = ['purchase.order']

    ponumber = fields.Char(
        string='PA Number',
        required=True,
        tracking=True,
        index=True, copy=False)
    
    po_date_created = fields.Date(string='PO Date Created', required=True, index=True, copy=False, default=fields.Datetime.now)
