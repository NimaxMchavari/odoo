# -*- coding: utf-8 -*-

from odoo import fields,models,api
from datetime import date

#from odoo.exceptions import UserError


class SaleOrderPricelistWizard(models.Model):
    _name = 'sale.order.pricelist.wizard'
    _description = 'Pricelist Wizard'
    
    sh_pricelist_id = fields.Many2one('product.pricelist',string="Pricelist")
    pricelist_line = fields.One2many('sale.order.pricelist.wizard.line','pricelist_id',string='PricelistLine Id')
    
    @api.model
    def default_get(self, fields):
        res = super(SaleOrderPricelistWizard, self).default_get(fields)
        res_ids = self._context.get('active_ids')
        if res_ids[0]:
            so_line = res_ids[0]
            so_line_obj = self.env['sale.order.line'].browse(so_line)
            pricelist_list = []
            pricelists = self.env['product.pricelist'].sudo().search([('currency_id','=',so_line_obj.order_id.currency_id.id)])
            if pricelists:
                item_pricelist =()
                for pricelist in pricelists:
                    for item in pricelist.item_ids:
                        if item.categ_id == so_line_obj.product_id.categ_id:
                            item_pricelist = item
                    tf_partner_id = self.env['tf.res.partner']
                    for x in so_line_obj.order_id.partner_id.tf_vendor_parameter_ids:
                        if x.category_id.id == so_line_obj.product_id.categ_id.id:
                            tf_partner_id = x
                    if not tf_partner_id:
                        continue

                    if [x for x in pricelist.item_ids if x.applied_on == '2_product_category'] and\
                            not [x for x in pricelist.item_ids if x.applied_on == '2_product_category' and so_line_obj.product_id.categ_id.id == x.categ_id.id]:
                        continue

                    price_unit = pricelist._compute_price_rule([(so_line_obj.product_id, so_line_obj.product_uom_qty, so_line_obj.order_id.partner_id)], date=date.today(), uom_id=so_line_obj.product_uom.id)[so_line_obj.product_id.id][0]
                    #price_unit = self.so_line_obj.currency_id._convert(price_unit, pricelist.currency_id, self.env.user.company_id, fields.Date.today())
                    if price_unit:
                        margin = price_unit - so_line_obj.product_id.standard_price
                        margin_per = (100 * (price_unit - so_line_obj.product_id.standard_price))/price_unit
                        descuento = 0
                        margin2 = 0
                        if item_pricelist and item_pricelist.as_utilidad > 0:
                            descuento = (1-(so_line_obj.product_id.as_last_purchase_price/(1-item_pricelist.as_utilidad/100)))*100
                            price_unit = so_line_obj.product_id.list_price *(1-descuento/100)
                            margin2 = price_unit * (item_pricelist.as_utilidad / 100)
                        price_based_usd = (so_line_obj.product_id.list_price - (so_line_obj.product_id.list_price * tf_partner_id.partner_discount/100))*tf_partner_id.cost_deal_import/100*(so_line_obj.product_id.product_tmpl_id.tf_import_tax/100)
                        cost_nimax_usd = ((so_line_obj.product_id.list_price - (so_line_obj.product_id.list_price*tf_partner_id.purchase_discount/100))-(so_line_obj.product_id.list_price*tf_partner_id.fulfillment_rebate/100))*(tf_partner_id.cost_deal_import/100)*(so_line_obj.product_id.product_tmpl_id.tf_import_tax/100)
                        #covertimos valores
                        margin_per = self.env.user.company_id.currency_id._convert(margin_per, pricelist.currency_id, self.env.user.company_id,so_line_obj.order_id.date_order)
                        margin2 = self.env.user.company_id.currency_id._convert(margin2, pricelist.currency_id, self.env.user.company_id,so_line_obj.order_id.date_order)
                        cost_nimax_usd = self.env.user.company_id.currency_id._convert(cost_nimax_usd, pricelist.currency_id, self.env.user.company_id,so_line_obj.order_id.date_order)
                        price_based_usd = self.env.user.company_id.currency_id._convert(price_based_usd, pricelist.currency_id, self.env.user.company_id,so_line_obj.order_id.date_order)
                        descuento = self.env.user.company_id.currency_id._convert(descuento, pricelist.currency_id, self.env.user.company_id,so_line_obj.order_id.date_order)
                        price_unit = self.env.user.company_id.currency_id._convert(price_unit, pricelist.currency_id, self.env.user.company_id,so_line_obj.order_id.date_order)
                        list_price = self.env.user.company_id.currency_id._convert(so_line_obj.product_id.list_price, pricelist.currency_id, self.env.user.company_id,so_line_obj.order_id.date_order)
                        as_last_purchase_price = self.env.user.company_id.currency_id._convert(so_line_obj.product_id.as_last_purchase_price, pricelist.currency_id, self.env.user.company_id,so_line_obj.order_id.date_order)
                        wz_line_id = self.env['sale.order.pricelist.wizard.line'].create({'sh_pricelist_id' :pricelist.id,
                                                                                    'sh_unit_price':price_unit,
                                                                                    'sh_unit_measure':so_line_obj.product_uom.id,
                                                                                    'sh_unit_cost':list_price,
                                                                                    'sh_margin':margin2,
                                                                                    'sh_margin_per':margin_per,
                                                                                    'line_id': so_line,
                                                                                    'as_precio_proveedor':as_last_purchase_price,
                                                                                    'as_descuento':descuento,
                                                                                    'price_based_usd': price_based_usd,
                                                                                    'nimax_price_usd': (price_based_usd)/(1-pricelist.expected_earning/100),
                                                                                    'cost_nimax_usd': cost_nimax_usd,
                                                                                    'tf_partner_id':tf_partner_id.id,
                                                                                    })
                        
                        pricelist_list.append(wz_line_id.id)
            res.update({
                
                'pricelist_line':[(6,0,pricelist_list)],
            })
        return res
        
        
        
class SaleOrderPricelistWizardLine(models.Model):
    _name = 'sale.order.pricelist.wizard.line'
    _description = 'Pricelist Wizard'
    
    pricelist_id = fields.Many2one('sale.order.pricelist.wizard',"Pricelist Id")
    sh_pricelist_id = fields.Many2one('product.pricelist',"Pricelist",required=True)
    sh_unit_measure = fields.Many2one('uom.uom','Unit')
    sh_unit_price = fields.Float('Unit Price')
    sh_unit_cost = fields.Float('Unit Cost')
    sh_margin = fields.Float('Margin')
    sh_margin_per = fields.Float('Margin %')
    line_id =fields.Many2one('sale.order.line')
    tf_partner_id = fields.Many2one('tf.res.partner',"Partner program")
      
    as_precio_proveedor = fields.Float(string='Precio Compra') # Precio de la ultima compra
    # as_precio_nimax = fields.Float(string='Precio NIMAX') # Precio de venta Nimax
    # as_utilidad = fields.Float(string='Utilidad') # Utilidad esperada
    as_descuento = fields.Float(string='Descuento') # Descuento calculado percent_price
    # as_precio_final = fields.Float(string='Precio de Venta Final')
    # as_product_id = fields.Many2one('product.product', string='Product ID',  required=True, ondelete='cascade', index=True, copy=False)      

    price_based_usd = fields.Float('PRICE BASE USD')
    nimax_price_usd = fields.Float('Precio NIMAX')
    cost_nimax_usd = fields.Float('Costo NIMAX')

    COST_NIMAX_MXP = fields.Float('COST NIMAX MXP')

    def update_sale_line_unit_price(self):
        if self.line_id:
            #se convierte de dolares a pesos mexicanos
            moneda_mxn = self.env['res.currency'].search([('id','=',33)])
            moneda_usd = self.env['res.currency'].search([('id','=',2)])
            price_unit = self.nimax_price_usd
            RECALCULATED_PRICE_UNIT = self.line_id.currency_id._convert(price_unit, moneda_usd, self.env.user.company_id, fields.Date.today())
            monto_mxp=self.line_id.currency_id._convert(self.nimax_price_usd, moneda_mxn, self.env.user.company_id, fields.Date.today())
            NIMAX_PRICE_MXP = monto_mxp
            COST_NIMAX_USD = self.line_id.currency_id._convert(self.cost_nimax_usd, moneda_usd, self.env.user.company_id, fields.Date.today())
            COST_NIMAX_MXP = self.line_id.currency_id._convert(self.cost_nimax_usd, moneda_mxn, self.env.user.company_id, fields.Date.today())
            MARGIN_MXP = (NIMAX_PRICE_MXP*self.line_id.product_uom_qty)-(COST_NIMAX_MXP*self.line_id.product_uom_qty)
            MARGIN_USD = (RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty)-(COST_NIMAX_USD*self.line_id.product_uom_qty)
            TOTAL_USD = RECALCULATED_PRICE_UNIT*self.line_id.product_uom_qty
            TOTAL_MXP = NIMAX_PRICE_MXP * self.line_id.product_uom_qty


            self.line_id.write({
                'price_unit':price_unit,
                'margin2':self.sh_margin,
                'as_pricelist_id':self.sh_pricelist_id,
                'RECALCULATED_PRICE_UNIT': RECALCULATED_PRICE_UNIT,
                'NIMAX_PRICE_MXP': NIMAX_PRICE_MXP,
                'COST_NIMAX_USD': COST_NIMAX_USD,
                'COST_NIMAX_MXP': COST_NIMAX_MXP,
                'MARGIN_MXP': MARGIN_MXP,
                'MARGIN_USD': MARGIN_USD,
                'TOTAL_USD': TOTAL_USD,
                'TOTAL_MXP': TOTAL_MXP,
                'as_log_price': False,
                                })
        

            self.env['tf.history.promo'].create(dict(
                # promotion_id=,
                vendor_id=self.tf_partner_id.partner_id.id,
                product_id=self.line_id.product_id.id,
                customer_id=self.line_id.order_id.partner_id.id,
                customer_type=self.tf_partner_id.partner_type.id,
                as_pricelist_id = self.sh_pricelist_id.id,
                category_id=self.line_id.product_id.categ_id.id,
                qty=self.line_id.product_uom_qty,
                recalculated_price_unit=self.line_id.RECALCULATED_PRICE_UNIT,
                recalculated_price_unit_mxp=self.line_id.NIMAX_PRICE_MXP,
                recalculated_cost_nimax_usd=self.line_id.COST_NIMAX_USD,
                recalculated_cost_nimax_mxp=self.line_id.COST_NIMAX_MXP,
                margin_mxp=self.line_id.MARGIN_MXP,
                margin_usd=self.line_id.MARGIN_USD,
                total_usd=self.line_id.TOTAL_USD,
                total_mxp=self.line_id.TOTAL_MXP,
                # last_applied_promo=,
                salesman_id=self.line_id.order_id.user_id.id,

                sale_id=self.line_id.order_id.id,
            ))










