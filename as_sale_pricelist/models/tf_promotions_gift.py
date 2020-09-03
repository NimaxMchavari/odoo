# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

as_type = ([
    ('NORMAL', 'Normal'),
    ('DEAL', 'Oportunidad'),
    ('DEMO', 'Demo'),
    ('ESPECIAL', 'Precio Especial'),
    ('FABRICANTE', 'Rebate'),
])


class tfGiftCouponProgram(models.Model):
    _name = "tf.gift.coupon.program"

    coupon_id = fields.Many2one('sale.coupon.program', string='Promo')
    name = fields.Selection(as_type, string='Tipo de Promocion', default='NORMAL')
    max_gifted_qty = fields.Float('MAX GIFT QTY')
    gifted_qty = fields.Float('Gifted')
    balance = fields.Float('Balance', compute='_compute_balance')

    def _compute_balance(self):
        for rec in self:
            rec.balance = rec.max_gifted_qty - rec.gifted_qty