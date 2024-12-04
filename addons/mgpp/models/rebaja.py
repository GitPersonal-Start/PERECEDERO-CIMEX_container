# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class Rebaja(models.Model):
    _name = 'mgpp.rebaja'
    _description = 'Gestión de Rebajas para Lotes'

    name = fields.Char(string='Código de Rebaja', required=True)
    lote_id = fields.Many2one('mgpp.lote', string='Lote', required=True, ondelete='cascade')
    precio_inicial = fields.Float(string='Precio Inicial', required=True, readonly=True)
    precio_actual = fields.Float(string='Precio Actual', compute='_compute_precio_actual', store=True, readonly=True)
    estado = fields.Selection([
        ('sin_rebaja', 'Sin Rebaja'),
        ('rebajado', 'Rebajado')
    ], string='Estado', default='pendiente', required=True, readonly=True)
    descuento = fields.Selection([
        ('0', 'Sin descuento'),
        ('30', '30%'),
        ('50', '50%'),
        ('70', '70%'),
        ('80', '80%')
    ], default='0', string='Descuento', readonly=True)
    solicitudes_ids = fields.One2many('mgpp.solicitud_rebaja', 'rebaja_id', string='Solicitudes de Rebaja', readonly=True)
    fecha_creacion = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now, readonly=True)
    fecha_finalizacion = fields.Datetime(string='Fecha de Finalización', required=True, readonly=True)
    dias_restantes = fields.Integer(string='Días Restantes', compute='_compute_dias_restantes', store=True, readonly=True)
    fecha_modificacion = fields.Datetime(string='Fecha de Modificación', readonly=True)
    observaciones = fields.Text(string='Observaciones', readonly=True)

    @api.depends('fecha_finalizacion')
    def _compute_dias_restantes(self):
        """Calcula los días restantes hasta la fecha de finalización."""
        for record in self:
            if record.fecha_finalizacion:
                hoy = fields.Date.context_today(record)
                dias = (record.fecha_finalizacion.date() - hoy).days
                record.dias_restantes = max(dias, 0)
            else:
                record.dias_restantes = 0

    @api.depends('solicitudes_ids', 'solicitudes_ids.estado')
    def _compute_precio_actual(self):
        """Calcula el precio actual basado en la solicitud de rebaja ejecutada."""
        for record in self:
            solicitud_ejecutada = record.solicitudes_ids.filtered(lambda s: s.estado == 'ejecutada')
            if solicitud_ejecutada:
                solicitud = solicitud_ejecutada[0]  # Tomar la primera solicitud ejecutada
                porcentaje = float(solicitud.descuento) / 100
                record.precio_actual = record.precio_inicial * (1 - porcentaje)
                record.descuento = solicitud.descuento
                record.estado = 'rebajado'
                record.fecha_modificacion = fields.Datetime.now()
            else:
                record.precio_actual = record.precio_inicial

    @api.model
    def create(self, vals):
        """Crea automáticamente cuatro solicitudes de rebaja al crear la rebaja."""
        rebaja = super().create(vals)
        descuentos = ['30', '50', '70', '80']
        for descuento in descuentos:
            precio_aplicado = rebaja.precio_inicial * (1 - int(descuento) / 100)
            self.env['mgpp.solicitud_rebaja'].create({
                'name': f"{rebaja.name}-{descuento}%",
                'rebaja_id': rebaja.id,
                'descuento': descuento,
                'precio_aplicado': precio_aplicado,
                'estado': 'pendiente',
                'fecha_solicitud': fields.Datetime.now(),
                'observaciones': f"Solicitud de rebaja del {descuento} creada automáticamente.",
            })
        return rebaja
    def action_open_solicitudes(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitudes de Rebaja',
            'view_mode': 'tree,form',
            'res_model': 'mgpp.solicitud_rebaja',
            'domain': [('rebaja_id', '=', self.id)],
        }


class SolicitudRebaja(models.Model):
    _name = 'mgpp.solicitud_rebaja'
    _description = 'Solicitud de Rebaja'

    name = fields.Char(string='Código de Solicitud', required=True)
    rebaja_id = fields.Many2one('mgpp.rebaja', string='Rebaja', required=True, ondelete='cascade')
    descuento = fields.Selection([
        ('30', '30%'),
        ('50', '50%'),
        ('70', '70%'),
        ('80', '80%')
    ], string='Descuento', required=True)
    precio_aplicado = fields.Float(string='Precio Aplicado', required=True)
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('solicitado', 'Solicitado'),
        ('aprobado', 'Aprobado'),
        ('vencido', 'Vencido'),
        ('ejecutada', 'Ejecutada'),
        ('revisada', 'Revisada')
    ], string='Estado', default='pendiente', required=True)
    fecha_solicitud = fields.Datetime(string='Fecha de Solicitud', default=fields.Datetime.now)
    observaciones = fields.Text(string='Observaciones')

    @api.model
    def action_solicitar(self):
        for record in self:
            if record.estado == 'pendiente':
                record.estado = 'solicitado'
    @api.model
    def create(self, vals):
        """Valida que no existan solicitudes con el mismo porcentaje de descuento para la misma rebaja."""
        existing_solicitudes = self.env['mgpp.solicitud_rebaja'].search([
            ('rebaja_id', '=', vals.get('rebaja_id')),
            ('descuento', '=', vals.get('descuento'))
        ])
        if existing_solicitudes:
            raise ValueError(f"Ya existe una solicitud con el descuento del {vals.get('descuento')}% para este lote de producto.")
        return super(SolicitudRebaja, self).create(vals)
    
# from odoo import models, fields, api
# from datetime import datetime, timedelta

# class Rebaja(models.Model):
#     _name = 'mgpp.rebaja'
#     _description = 'Gestion de Rebajas para Lotes'

#     name = fields.Char(string='Codigo de Rebaja', required=True)
#     lote_id = fields.Many2one('mgpp.lote', string='Lote', required=True, ondelete='cascade')
#     precio_inicial = fields.Float(string='Precio Inicial', required=True)
#     precio_actual = fields.Float(string='Precio Actual', compute='_compute_precio_actual', store=True)
#     estado = fields.Selection([
#         ('pendiente', 'Pendiente'),
#         ('rebajado', 'Rebajado')
#     ], string='Estado', default='pendiente', required=True)
#     descuento = fields.Selection([
#         ('30', '30%'),
#         ('50', '50%'),
#         ('70', '70%'),
#         ('80', '80%')
#     ], string='Descuento', default='30')
#     solicitudes_ids = fields.One2many('mgpp.solicitud_rebaja', 'rebaja_id', string='Solicitudes de Rebaja')
#     fecha_creacion = fields.Datetime(string='Fecha de Creacion', default=fields.Datetime.now)
#     fecha_finalizacion = fields.Datetime(string='Fecha de Finalizacion', required=True)
#     dias_restantes = fields.Integer(string='Dias Restantes', compute='_compute_dias_restantes', store=True)
#     observaciones = fields.Text(string='Observaciones')

#     @api.depends('fecha_finalizacion')
#     def _compute_dias_restantes(self):
#         """Calculo de dias restantes y ajuste del descuento."""
#         for record in self:
#             if record.fecha_finalizacion:
#                 # Calcular dias restantes
#                 hoy = fields.Date.context_today(record)
#                 dias = (record.fecha_finalizacion.date() - hoy).days
#                 record.dias_restantes = max(dias, 0)
#                 # Ajustar el descuento segun los dias restantes
#                 if dias >= 60:
#                     record.descuento = '30'
#                 elif dias >= 30:
#                     record.descuento = '50'
#                 elif dias >= 15:
#                     record.descuento = '70'
#                 elif dias >= 7:
#                     record.descuento = '80'
#             else:
#                 record.dias_restantes = 0

#     @api.depends('solicitudes_ids', 'solicitudes_ids.solicitud_valida')
#     def _compute_precio_actual(self):
#         """Calculo del precio actual basado en la solicitud valida."""
#         for record in self:
#             solicitud_valida = record.solicitudes_ids.filtered(lambda s: s.solicitud_valida)
#             if solicitud_valida:
#                 porcentaje = float(solicitud_valida.descuento) / 100
#                 record.precio_actual = record.precio_inicial * (1 - porcentaje)
#             else:
#                 record.precio_actual = record.precio_inicial

#     @api.model
#     def _crear_solicitudes(self, descuento):
#         """Crea solicitudes de rebaja segun los dias restantes."""
#         for record in self:
#             # Crear las solicitudes
#             solicitud = self.env['mgpp.solicitud_rebaja'].create({
                
#             })
#             porcentaje = None

#             # Determinar el porcentaje de descuento segun los dias restantes
#             if record.dias_restantes >= 60:
#                 porcentaje = '30'
#             elif 30 <= record.dias_restantes < 60:
#                 porcentaje = '50'
#             elif 15 <= record.dias_restantes < 30:
#                 porcentaje = '70'
#             elif 7 <= record.dias_restantes < 15:
#                 porcentaje = '80'

#             # Si hay un porcentaje valido, crear una nueva solicitud
#             if porcentaje:
#                 # Desactivar otras solicitudes validas
#                 record.solicitudes_ids.write({'solicitud_valida': False})

#                 # Crear la nueva solicitud
#                 nueva_solicitud = self.env['mgpp.solicitud_rebaja'].create({
#                     'name': f"{record.name}-{porcentaje}%",
#                     'rebaja_id': record.id,
#                     'descuento': porcentaje,
#                     'precio_aplicado': record.precio_inicial * (1 - int(porcentaje) / 100),
#                     'estado': 'pendiente',
#                     'fecha_solicitud': fields.Datetime.now(),
#                     'solicitud_valida': True,
#                     'observaciones': f"Creado automaticamente al alcanzar {record.dias_restantes} dias restantes.",
#                 })

#                 # Actualizar el precio actual basado en la nueva solicitud valida
#                 record.precio_actual = nueva_solicitud.precio_aplicado
#     def crea_solicitud(self, vals):
#         for record in self:
#             self.env['mgpp.solicitud_rebaja'].create({
#                 'name': f"{record.name}-{vals}%",
#                     'rebaja_id': record.id,
#                     'descuento': porcentaje,
#                     'precio_aplicado': record.precio_inicial * (1 - int(porcentaje) / 100),
#                     'estado': 'pendiente',
#                     'fecha_solicitud': fields.Datetime.now(),
#                     'solicitud_valida': True,
#                     'observaciones': f"Creado automaticamente al alcanzar {record.dias_restantes} dias restantes.",
#             })


#     @api.model
#     def create(self, vals):
#         rebaja = super().create(vals)
#         rebaja._crear_solicitudes()  # Crear solicitudes inmediatamente
#         return rebaja

# class SolicitudRebaja(models.Model):
#     _name = 'mgpp.solicitud_rebaja'
#     _description = 'Solicitud de Rebaja'

#     name = fields.Char(string='Codigo de Solicitud', required=True)
#     rebaja_id = fields.Many2one('mgpp.rebaja', string='Rebaja', required=True, ondelete='cascade')
#     descuento = fields.Selection([
#         ('30', '30%'),
#         ('50', '50%'),
#         ('70', '70%'),
#         ('80', '80%')
#     ], string='Descuento', required=True)
#     precio_aplicado = fields.Float(string='Precio Aplicado', required=True)
#     estado = fields.Selection([
#         ('pendiente', 'Pendiente'),
#         ('solicitado', 'Solicitado'),
#         ('aprobado', 'Aprobado'),
#         ('vencido', 'Vencido'),
#         ('ejecutada', 'Ejecutada'),
#         ('revisada', 'Revisada')
#     ], string='Estado', default='pendiente', required=True)
#     fecha_solicitud = fields.Datetime(string='Fecha de Solicitud', default=fields.Datetime.now)
#     solicitud_valida = fields.Boolean(string='Solicitud Valida', default=False)
#     observaciones = fields.Text(string='Observaciones')
    
    

