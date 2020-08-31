# # -*- coding: utf-8 -*-

import datetime
from datetime import datetime
import pytz
from odoo import models,fields
from datetime import datetime, timedelta
from time import mktime
from odoo import models, fields, api, _, _lt

class CalculoComisiones(models.AbstractModel):
    _name = 'report.as_sale_pricelist.comision_report_xlsx.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):        
        dict_almacen = []
        dict_aux = []
        filtro = ''
        if data['form']['user_id']:
            filtro+= ' and ru.id in '+ str(data['form']['user_id']).replace('[','(').replace(']',')')
        # if data['form']['partner_id']:
        #     filtro+= ' and rp.id in '+ str(data['form']['partner_id']).replace('[','(').replace(']',')')
        # if data['form']['as_empresa']:
        #     filtro+= ' and ae.id in '+ str(data['form']['as_empresa']).replace('[','(').replace(']',')')

        sheet = workbook.add_worksheet('Detalle de Movimientos')
        titulo1 = workbook.add_format({'font_size': 16, 'align': 'center', 'text_wrap': True, 'bold':True })
        titulo2 = workbook.add_format({'font_size': 14, 'align': 'center', 'text_wrap': True, 'bottom': True, 'top': True, 'bold':True })
        titulo3 = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': True, 'bottom': True, 'top': True, 'bold':True })
        titulo3_number = workbook.add_format({'font_size': 14, 'align': 'right', 'text_wrap': True, 'bottom': True, 'top': True, 'bold':True, 'num_format': '#,##0.00' })
        titulo4 = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': True, 'bottom': True, 'top': True, 'left': True, 'right': True, 'bold':True })

        number_left = workbook.add_format({'font_size': 12, 'align': 'left', 'num_format': '#,##0.00'})
        number_right = workbook.add_format({'font_size': 12, 'align': 'right', 'num_format': '#,##0.00'})
        number_right_bold = workbook.add_format({'font_size': 12, 'align': 'right', 'num_format': '#,##0.00', 'bold':True})
        number_right_col = workbook.add_format({'font_size': 12, 'align': 'right', 'num_format': '#,##0.00','bg_color': 'silver'})
        number_right_col1 = workbook.add_format({'font_size': 12, 'align': 'right', 'num_format': '#,##0.00'})
        number_center = workbook.add_format({'font_size': 12, 'align': 'center', 'num_format': '#,##0.00'})
        number_right_col.set_locked(False)

        letter12 = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': True, 'bold':True})
        letter11 = workbook.add_format({'font_size': 12, 'align': 'center', 'text_wrap': True})
        letter1 = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': True})
        letter2 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold':False})
        letter3 = workbook.add_format({'font_size': 12, 'align': 'right', 'text_wrap': True})
        letter4 = workbook.add_format({'font_size': 12, 'align': 'left', 'text_wrap': True, 'bold': True})
        letter5 = workbook.add_format({'font_size': 12, 'align': 'right', 'text_wrap': True, 'bold': True})
        letter_locked = letter3
        letter_locked.set_locked(False)

        # Aqui definimos en los anchos de columna
        sheet.set_column('A:A',35, letter1)
        sheet.set_column('B:B',12, letter1)
        sheet.set_column('C:C',12, letter1)
        sheet.set_column('D:D',12, letter1)
        sheet.set_column('E:E',15, letter1)
        sheet.set_column('F:F',15, letter1)
        sheet.set_column('G:G',15, letter1)
        sheet.set_column('H:H',20, letter1)
        sheet.set_column('I:I',25, letter1)
        sheet.set_column('J:J',15, letter1)
        sheet.set_column('K:K',15, letter1)

        fecha_inicial = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        fecha_final = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        # Titulos, subtitulos, filtros y campos del reporte
        fecha = (datetime.now() - timedelta(hours=4)).strftime('%d/%m/%Y %H:%M:%S')
        sheet.merge_range('A1:C1', 'Nombre Empresa: '+self.env.user.company_id.name, letter1)
        sheet.merge_range('A2:C2', 'Dirección: '+self.env.user.company_id.street, letter1)
        sheet.merge_range('A3:C3', 'Telefono: '+self.env.user.company_id.phone, letter1)
        sheet.merge_range('A4:C4', self.env.user.company_id.city+'-'+self.env.user.company_id.country_id.name)
        sheet.merge_range('D1:I1', 'Usuario Impresión: '+self.env.user.name, letter1)
        sheet.merge_range('D2:I2', 'Fecha y Hora Impresión: '+fecha, letter1)
         
        sheet.merge_range('A5:G5', 'REPORTE CALCULO DE COMISIONES', titulo1)
        sheet.set_row(4, 40)
        sheet.merge_range('A6:G6', 'DEL '+fecha_inicial+' AL '+fecha_final, letter11)
        filas = 7
        sheet.write(filas, 0, 'VENDEDOR',titulo4) #cliente/proveedor
        sheet.write(filas, 1, 'FECHA INICIO',titulo4) #cliente/proveedor
        sheet.write(filas, 2, 'FECHA FINAL',titulo4) #cliente/proveedor
        sheet.write(filas, 3, 'TOTAL MARGEN VENTAS $US',titulo4) #cliente/proveedor
        sheet.write(filas, 4, '% DE COMISION <= LIMITE 1',titulo4) #cliente/proveedor
        sheet.write(filas, 5, 'A PAGAR MXP',titulo4) #cliente/proveedor
        sheet.write(filas, 6, 'TOTAL VENTAS',titulo4) #cliente/proveedor
        total_margen = 0.0 
        total_pagar = 0.0 
        total_ventas = 0.0 
        sheet.set_row(filas,30,titulo4)
        filas += 1
        cantidad = 0
        query_ids = ("""
            select ru.id from res_users ru
            inner join res_partner rp on ru.partner_id = rp.id
            where 
            ru.active=True
            """+filtro+"""
        """)

        self.env.cr.execute(query_ids)

        users = [j for j in self.env.cr.fetchall()]
        for partner in users:
            query_movements = ("""
                select 
                rp.name,sum(margin_usd),sum(thp.total_usd)
                from tf_history_promo thp
                inner join sale_order so on thp.sale_id = so.id
                inner join res_users ru on ru.id = thp.salesman_id
                inner join res_partner rp on ru.partner_id = rp.id
                where 
                so.state not in ('cancel','draft') and
                thp.fecha_factura::date BETWEEN '"""+str(data['form']['start_date'])+"""' AND  '"""+str(data['form']['end_date'])+"""'"""+filtro+""" 
                and ru.id="""+str(partner[0])+"""
                and thp.last_applied_promo=True
                and thp.invoice_name != ''
                group by 1
                """)
            #_logger.debug(query_movements)
            self.env.cr.execute(query_movements)
            historico_prom = [k for k in self.env.cr.fetchall()]
            for history in historico_prom:
                cantidad+=1
                sheet.write(filas, 0, history[0]) 
                sheet.write(filas, 1, fecha_inicial) 
                sheet.write(filas, 2, fecha_final) 
                sheet.write(filas, 3, history[1],number_right_col1) 
                query_ids = ("""
                select as_desde,as_hasta,as_comision,as_division from as_tabla_comisiones 
                where 
                as_desde <= """+str(history[1])+""" and """+str(history[1])+""" <= as_hasta limit 1
                """)

                self.env.cr.execute(query_ids)
                history_table = [j for j in self.env.cr.fetchall()]
                porcentaje = 0.0
                pagar = 0.0
                if history_table:
                    porcentaje = float(history[1])/float(history_table[0][1])
                    if history_table[0][3]==True:
                        pagar = history_table[0][2] * porcentaje
                    else:
                        pagar = history_table[0][2]
                    total_margen += float(history[1])
                    total_pagar += pagar
                sheet.write(filas, 4,  str(round(porcentaje*100,2))+str('%'),number_right_col1)
                sheet.write(filas, 5,  pagar,number_right_col1)
                sheet.write(filas, 6,  history[2],number_right_col1)
                total_ventas += float(history[2])
                filas += 1

        sheet.merge_range('A'+str(filas+1)+':C'+str(filas+1),'TOTAL ', number_right_col)
        sheet.write(filas, 4,  0.0,number_right_col)
        sheet.write(filas, 3, total_margen, number_right_col) 
        sheet.write(filas, 5, total_pagar, number_right_col) 
        sheet.write(filas, 6, total_ventas, number_right_col) 