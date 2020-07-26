# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
import logging
import math
import re
import time
import traceback

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)

class ResCurrency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _get_conversion_rate_nimax(self, from_currency, to_currency, company, date, line_id):
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        if line_id:
            line_sale = self.env['sale.order.line'].sudo().search([('id','=',line_id)])
            if line_sale:
                moneda = line_sale.order_id.currency_aux_id
                rate = line_sale.order_id.sale_manual_currency_rate
                if moneda and rate > 0 and line_sale.order_id.sale_manual_currency_rate_active:
                    currency_rates[moneda.id]= rate
        res = currency_rates.get(to_currency.id) / currency_rates.get(from_currency.id)
        return res

    def _convert_nimax(self, from_amount, to_currency, company, date, line_id=None,round=True ):
        """Returns the converted amount of ``from_amount``` from the currency
           ``self`` to the currency ``to_currency`` for the given ``date`` and
           company.

           :param company: The company from which we retrieve the convertion rate
           :param date: The nearest date from which we retriev the conversion rate.
           :param round: Round the result or not
        """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"
        # apply conversion rate
        if self == to_currency:
            to_amount = from_amount
        else:
            to_amount = from_amount * self._get_conversion_rate_nimax(self, to_currency, company, date,line_id)
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount