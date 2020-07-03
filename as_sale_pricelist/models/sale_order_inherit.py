# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, ValidationError
    
class SaleOrderLine(models.Model):
    _inherit="sale.order.line"
    
    margin2 = fields.Float('Margen 2', digits='Product Price', default=0)
    as_pricelist_id = fields.Many2one('product.pricelist', string='Lista de Precios',readonly=True,store=True)
    as_log_price = fields.Boolean('Log de price Unit',default=True)
    RECALCULATED_PRICE_UNIT = fields.Float('RECALCULATED PRICE UNIT')
    NIMAX_PRICE_MXP = fields.Float('NIMAX PRICE MXP')
    COST_NIMAX_USD = fields.Float('COST NIMAX USD')
    COST_NIMAX_MXP = fields.Float('COST NIMAX MXP')
    MARGIN_MXP = fields.Float('MARGIN MXP')
    MARGIN_USD = fields.Float('MARGIN USD')
    TOTAL_USD = fields.Float('TOTAL USD')
    TOTAL_MXP = fields.Float('TOTAL MXP')
    as_margin_porcentaje = fields.Float('Margen Porcentaje',compute='get_margin_porcentaje',store=True)

    coupon_ids = fields.Many2many('sale.coupon.program', string='Coupons')
    RECALCULATED_COST_NIMAX_USD = fields.Float('RECALCULATED COST NIMAX USD')

    @api.depends('COST_NIMAX_USD','RECALCULATED_PRICE_UNIT')
    def get_margin_porcentaje(self):
        for sale_line in self:
            moneda_mxn = self.env['res.currency'].search([('id','=',33)])
            moneda_usd = self.env['res.currency'].search([('id','=',2)])
            if moneda_usd != sale_line.currency_id:
                price = moneda_mxn._convert(sale_line.price_unit,moneda_usd, self.env.user.company_id, fields.Date.today())
            else:
                price = sale_line.price_unit
            price_total_unit = price*sale_line.product_uom_qty
            price_total_cost = sale_line.COST_NIMAX_USD*sale_line.product_uom_qty
            if price_total_unit > 0:
                sale_line.as_margin_porcentaje = ((price_total_unit-price_total_cost)/price_total_unit)*100
        
    # apply pricelist
    def pricelist_apply(self):
        pricelists = self.env['product.pricelist'].sudo().search([('currency_id','=',self.order_id.currency_id.id)])
        pricelist = []
        for price in pricelists:
            pricelist.append(price.id)
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order.pricelist.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_sh_pricelist_id': pricelist},
            }
        
    # apply promo
    def promo_apply(self):
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'as.sale.order.promo.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'promo_apply_dis_per': 'promo_apply_dis_per'},
            }

    @api.onchange('price_unit','product_uom_qty')
    def get_margin_utilidad(self):
        moneda_mxn = self.env['res.currency'].search([('id','=',33)])
        moneda_usd = self.env['res.currency'].search([('id','=',2)])
        for sale_line in self:
            if moneda_mxn == sale_line.currency_id:
                new_amrgin= (sale_line.price_unit*sale_line.product_uom_qty)-(sale_line.COST_NIMAX_MXP*sale_line.product_uom_qty)
                sale_line.MARGIN_MXP=new_amrgin
                sale_line.MARGIN_USD=moneda_mxn._convert(new_amrgin,moneda_usd, self.env.user.company_id, fields.Date.today())
                sale_line.get_margin_porcentaje()
                sale_line.TOTAL_MXP = sale_line.price_unit * sale_line.product_uom_qty
                sale_line.TOTAL_USD = moneda_mxn._convert(sale_line.TOTAL_MXP,moneda_usd, self.env.user.company_id, fields.Date.today())
                sale_line.RECALCULATED_PRICE_UNIT = moneda_mxn._convert(sale_line.price_unit, moneda_usd,self.env.user.company_id, fields.Date.today())
                sale_line.NIMAX_PRICE_MXP = sale_line.price_unit
            else:
                new_amrgin= (sale_line.price_unit*sale_line.product_uom_qty)-(sale_line.COST_NIMAX_USD*sale_line.product_uom_qty)
                sale_line.MARGIN_USD=new_amrgin
                sale_line.MARGIN_MXP=moneda_usd._convert(new_amrgin,moneda_mxn, self.env.user.company_id, fields.Date.today())
                sale_line.get_margin_porcentaje()
                sale_line.TOTAL_USD = sale_line.price_unit * sale_line.product_uom_qty
                sale_line.TOTAL_MXP = moneda_usd._convert(sale_line.TOTAL_USD,moneda_mxn, self.env.user.company_id, fields.Date.today())
                sale_line.RECALCULATED_PRICE_UNIT = sale_line.price_unit
                sale_line.NIMAX_PRICE_MXP = moneda_usd._convert(sale_line.price_unit,moneda_mxn, self.env.user.company_id, fields.Date.today())
            tf_partner_id = self.env['tf.res.partner']
            for x in sale_line.order_id.partner_id.tf_vendor_parameter_ids:
                if x.category_id.id == sale_line.product_id.categ_id.id:
                    tf_partner_id = x
            if sale_line.as_pricelist_id and sale_line.as_log_price:
                self.env['tf.history.promo'].create(dict(
                    # promotion_id=,
                    vendor_id=tf_partner_id.partner_id.id,
                    product_id=sale_line.product_id.id,
                    customer_id=sale_line.order_id.partner_id.id,
                    customer_type=tf_partner_id.partner_type.id,
                    as_pricelist_id = sale_line.as_pricelist_id.id,
                    category_id=sale_line.product_id.categ_id.id,
                    qty=sale_line.product_uom_qty,
                    recalculated_price_unit=sale_line.RECALCULATED_PRICE_UNIT,
                    recalculated_price_unit_mxp=sale_line.NIMAX_PRICE_MXP,
                    recalculated_cost_nimax_usd=sale_line.COST_NIMAX_USD,
                    recalculated_cost_nimax_mxp=sale_line.COST_NIMAX_MXP,
                    margin_mxp=sale_line.MARGIN_MXP,
                    margin_usd=sale_line.MARGIN_USD,
                    total_usd=sale_line.TOTAL_USD,
                    total_mxp=sale_line.TOTAL_MXP,
                    # last_applied_promo=,
                    salesman_id=sale_line.order_id.user_id.id,

                    sale_id=sale_line.order_id.id,
                ))
            sale_line.as_log_price=True


            

class SaleOrder(models.Model):
    _inherit = "sale.order"

            
    as_margin = fields.Float(string='Margen(en %)', store=True, readonly=True, compute='_amount_all_marigin', tracking=4)
    as_aprobe = fields.Boolean(string='Aporbar Venta',default=False)

    @api.depends('order_line.price_unit','order_line.product_uom_qty','order_line.COST_NIMAX_USD')
    def _amount_all_marigin(self):
        total_price = 0.0
        total_cost = 0.0
        total_margin = 0.0
        for order in self:
            for line in order.order_line:
                moneda_mxn = self.env['res.currency'].search([('id','=',33)])
                moneda_usd = self.env['res.currency'].search([('id','=',2)])
                if moneda_usd != line.currency_id:
                    price = moneda_mxn._convert(line.price_unit,moneda_usd, self.env.user.company_id, fields.Date.today())
                else:
                    price = line.price_unit
                total_price += price * line.product_uom_qty
                total_cost += line.COST_NIMAX_USD * line.product_uom_qty
                line.get_margin_utilidad()
            if total_price > 0:
                total_margin += (total_price-total_cost)/total_price
            order.update({
                'as_margin': total_margin*100,
            })
    
    @api.onchange('partner_id','pricelist_id')
    def _default_currecy_aux(self):
        if self.pricelist_id:
            self.currency_aux_id = self.currency_id  
        else:
            self.currency_aux_id = 2

    @api.onchange('currency_aux_id')
    def _default_currecy(self):
        if self.partner_id:
            tarifa = self.env['product.pricelist'].search([('as_tarifa_base','=',True),('currency_id','=',self.currency_aux_id.id)],limit=1)
            if tarifa:
                self.pricelist_id = tarifa
            else:
                raise ValidationError('Debe crear tarifa base para calculo de moneda')

    last_promo_id = fields.Many2one('sale.coupon.program', 'Last Sale Promo')
    currency_aux_id = fields.Many2one("res.currency", string="Moneda",default=2, required=True)
    
    def get_promocion(self,line_id):
        line = self.env['sale.order.line'].search([('id','=',line_id)])
        ultima_promo = self.env['tf.history.promo'].search([('sale_id','=',self.id),('product_id','=',line.product_id.id),('last_applied_promo','=',True)])
        name= ''
        if ultima_promo:
            name = str(ultima_promo.promo_id.id)+' : '+str(ultima_promo.promo_id.name)
        else:
            name =' '
        return name
        
    def action_confirm(self):
        margin_minimo = self.env['ir.config_parameter'].sudo().get_param('as_sale_pricelist.as_margin_minimo')
        margin_global = self.env['ir.config_parameter'].sudo().get_param('as_sale_pricelist.as_margin_global')
        if self.as_aprobe == False:
            access = False
            no_access = False
            for line in self.order_line:
                if (line.as_margin_porcentaje  > 0) and (line.as_margin_porcentaje  < float(margin_minimo)):
                    access= True
                elif (float(line.as_margin_porcentaje) < float(margin_global)):
                    no_access = True
            if access:
                action = self.env.ref('as_sale_pricelist.action_aprobe_sales_qweb').read()[0]
                action.update({
                    'context': {
                        'default_as_sale': self.id,
                    
                    },
                })
                return action  
            elif no_access:
                raise ValidationError('No se puede confirmar la venta, modifique sus precios')
        product=[]
        res = super(SaleOrder, self).action_confirm()

        for rec in self:
            for line in rec.order_line:
                for promo in line.coupon_ids:
                    # if promo.PROMO_count <= promo.PROMO_countdown:
                    #     raise ValidationError('Not Much Promos are allowed!\n Promo Name is : %s'%promo.name)
                    # promo.PROMO_countdown += 1
                    if (promo.tf_max_gifted_qty - promo.tf_gifted_qty) <= 0:
                        raise ValidationError('Not Much Promos are allowed!\n Promo Name is : %s' % promo.name)
                    if promo.as_type == 'DEMO':
                        promo.tf_gifted_qty += line.product_uom_qty
                    elif promo.as_type == 'ESPECIAL':
                        promo.tf_gifted_qty += line.product_uom_qty
                tf_history_id = self.env['tf.history.promo'].search([('sale_id', '=', rec.id),('product_id', '=', line.product_id.id)], order='create_date desc', limit=1)
                if tf_history_id:
                    tf_history_id.last_applied_promo = True
            for line in rec.order_line:
                if not line.as_pricelist_id:
                    product.append(line.product_id.name)
        if product != []:
            raise ValidationError('EXISTEN LINEAS PRODUCTO SIN PRECIO BASE : %s' % str(product))
                

        return res

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()

        for rec in self:
            for line in rec.order_line:
                for promo in line.coupon_ids:
                    # promo.PROMO_countdown -= 1

                    if promo.as_type == 'DEMO':
                        promo.tf_gifted_qty -= line.product_uom_qty
                    elif promo.as_type == 'ESPECIAL':
                        promo.tf_gifted_qty -= line.product_uom_qty
        return res