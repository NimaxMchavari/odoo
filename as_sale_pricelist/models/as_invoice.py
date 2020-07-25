# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)
class as_accountinvoice(models.Model):
    _inherit = "account.move"

    def get_promocion(self,line_id):
        vasl=0
        query_movements = ("""
            select order_line_id from sale_order_line_invoice_rel 
            where
            invoice_line_id = """+str(line_id)+"""
            """)
        #_logger.debug(query_movements)
        self.env.cr.execute(query_movements)
        ids = [k for k in self.env.cr.fetchall()]
        name= ''
        if ids != []:
            line = self.env['sale.order.line'].search([('id','in',ids)],limit=1)
            ultima_promo = self.env['tf.history.promo'].search([('sale_id','=',line.order_id.id),('product_id','=',line.product_id.id),('last_applied_promo','=',True)],order="write_date desc", limit=1)
            if ultima_promo:
                name = str(ultima_promo.promo_id.id)+' : '+str(ultima_promo.promo_id.name)
            else:
                name =' '
        return name

    def get_product_lot(self,product_id):
        names = ''
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
        for pick in sale_order.picking_ids:
            for move in pick.move_line_ids_without_package:
                if product_id == move.product_id.id:
                    names += str(move.lot_id.name)
        return names
        
    def get_referencia_pedido(self):
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
        if sale_order and 'x_studio_orden_de_compra' in sale_order:
            return sale_order.x_studio_orden_de_compra
        else:
            return 'N/A'