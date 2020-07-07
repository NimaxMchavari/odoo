# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, time
import logging
import base64
_logger = logging.getLogger(__name__)
class tfResPartner(models.Model):
    _name = "tf.history.promo"

    # promotion_id = fields.Many2one('sale.coupon.program')

    vendor_id = fields.Many2one('res.partner', 'Vendor')
    product_id = fields.Many2one('product.product', 'Product')
    customer_id = fields.Many2one('res.partner', 'Customer')
    customer_type = fields.Many2one('as.partner.type', 'Type Customer')
    category_id = fields.Many2one('product.category', 'Product Category')
    qty = fields.Float('Qty')
    recalculated_price_unit = fields.Float('Recalculated Price Unit')
    recalculated_price_unit_mxp = fields.Float('Recalculated Price Unit MXP')
    recalculated_cost_nimax_usd = fields.Float('Recalculated Cost Nimax USD')
    recalculated_cost_nimax_mxp = fields.Float('Recalculated Cost Nimax MXP')
    margin_mxp = fields.Float('Margin MXP')
    margin_usd = fields.Float('Margin USD')
    total_usd = fields.Float('Total USD')
    total_mxp = fields.Float('Total MXP')
    last_applied_promo = fields.Boolean('Last Applied Promo')
    salesman_id = fields.Many2one('res.users', 'Salesman')
    as_pricelist_id = fields.Many2one('product.pricelist', string='Tarifa')

    sale_id = fields.Many2one('sale.order', 'Sale Order')
    fecha_venta = fields.Datetime(string='Fecha Venta', compute="_get_invoiced_ver",store=True)
    promo_id = fields.Many2one('sale.coupon.program', 'Promotion')

    sale_order_line = fields.Many2one('sale.order.line')
    state_sale = fields.Selection([('draft', 'Quotation'),('sent', 'Quotation Sent'),('sale', 'Sales Order'),('done', 'Locked'),('cancel', 'Cancelled'),], string='Estado venta', related="sale_id.state")
    
    @api.depends('sale_id')
    def _get_invoiced_ver(self):
        for history in self:
            if history.sale_id:
                for order in history.sale_id:
                    invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.type in ('out_invoice', 'out_refund'))
                    history.invoice_ids = invoices
                    history.fecha_venta = order.date_order

            else:
                history.invoice_ids = []
                history.fecha_venta = datetime.now()

    invoice_ids = fields.Many2many("account.move", string='Facturas de Cliente', compute="_get_invoiced_ver",store=True)
    invoice_name = fields.Char(string='Facturas de Cliente', related='invoice_ids.name',store=True)
