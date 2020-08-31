# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging
_logger = logging.getLogger(__name__)
class as_accountinvoice(models.Model):
    _inherit = "account.move"

    def _onchange_terms(self):
        invoice_terms =  self.company_id.invoice_terms
        return invoice_terms

    @api.model
    def l10n_mx_edi_retrieve_attachments(self):
        '''Retrieve all the cfdi attachments generated for this invoice.

        :return: An ir.attachment recordset
        '''
        self.ensure_one()
        if not self.l10n_mx_edi_cfdi_name:
            return []
        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', '=', self.l10n_mx_edi_cfdi_name)]
        return self.env['ir.attachment'].search(domain)

    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        if self.l10n_mx_edi_cfdi_name:
            name = str(self.l10n_mx_edi_cfdi_name).split('.')[0]
            invoices = self.env['ir.attachment'].search([('name', '=', name and _("%s.pdf") % name)])
            if not invoices:
                modelo = 'account.move'
                content = self.env.ref('as_sale_pricelist.as_account_invoices_new_mx').render_qweb_pdf(self.id)[0]
                self.env['ir.attachment'].create({
                    'name': name and _("%s.pdf") % name or _("Factura_.pdf"),
                    'type': 'binary',
                    'datas': base64.b64encode(content),
                    'res_model': modelo,
                    'res_id': self.id,
                })
              
        template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            force_email=True
        )
        return {
            'name': _('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

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

    def get_tasa_xml(self,product_id):
        xml = self.l10n_mx_edi_get_xml_etree()
        impuestos = []
        bandera = False
        if xml is not None:
            conceptos = xml.Conceptos.Concepto
            for product in conceptos:
                if product.get('NoIdentificacion')== product_id:
                    for translado in product.Impuestos.Traslados.Traslado:
                        if bandera == False:
                            if translado.attrib != {}:
                                vals={
                                    'Tasa': translado.attrib['TasaOCuota'],
                                    'Base': round(float(translado.attrib['Base']),2),
                                    'Impuesto': round(float(translado.attrib['Impuesto']),2),
                                    'Importe': round(float(translado.attrib['Importe']),2),
                                }
                                bandera = True
                                impuestos.append(vals)

        return impuestos

    def get_product_lot(self,product_id):
        names = ''
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
        for pick in sale_order.picking_ids:
            for move in pick.move_line_ids_without_package:
                if product_id == move.product_id.id:
                    names += str(move.lot_id.name)+', '
        return names
        
    def get_referencia_pedido(self):
        sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
        if sale_order and 'x_studio_orden_de_compra' in sale_order:
            return sale_order.x_studio_orden_de_compra
        else:
            return 'N/A'

    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))

        self.filtered(lambda inv: not inv.invoice_sent).write({'invoice_sent': True})
        if self.user_has_groups('account.group_account_invoice'):
            return self.env.ref('as_sale_pricelist.as_account_invoices_new_mx').report_action(self)
        else:
            return self.env.ref('as_sale_pricelist.as_account_invoices_new_mx').report_action(self)

    def adjuntar_factura_model(self,invoice):
   
        return ''

    def l10n_mx_edi_amount_to_text(self):
        """Method to transform a float amount to text words
        E.g. 100 - ONE HUNDRED
        :returns: Amount transformed to words mexican format for invoices
        :rtype: str
        """
        self.ensure_one()
        currency = self.currency_id.name.upper()
        # M.N. = Moneda Nacional (National Currency)
        # M.E. = Moneda Extranjera (Foreign Currency)
        if currency == 'MXN':
            currency_type = 'M.N'
        elif currency == 'USD':
            currency_type = 'USD'
        else:
            currency_type = 'M.E.'
        # currency_type = 'M.N' if currency == 'MXN' elif currency_type = 'DOLARES' if currency == 'USD' else 'M.E.'
        # Split integer and decimal part
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(amount_i).upper()
        invoice_words = '%(words)s %(amount_d)02d/100 %(curr_t)s' % dict(
            words=words, amount_d=amount_d, curr_t=currency_type)
        return invoice_words