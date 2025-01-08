# -*- coding: utf-8 -*-            
from datetime import date, timedelta
from odoo import models, fields, api

class FechaValidacion(models.Model):
    _name = 'mgpp.fecha_validacion'
    _description = 'Fecha de Validación de Solicitudes'

    fechas_validacion = fields.Date(string="Fecha de Validación", required=True, unique=True)
    name = fields.Char(string="Descripción", compute='_compute_name', store=True)
    solicitudes_ids = fields.One2many('mgpp.solicitud_rebaja', 'fecha_validacion_id', string="Solicitudes Asociadas")
    cantidad_solicitudes = fields.Integer(string="Cantidad de Solicitudes", compute='_compute_cantidad_solicitudes', store=True)
    seleccionado = fields.Boolean(string="Seleccionado", default=False, readonly=True)
    @api.depends('solicitudes_ids')
    def _compute_cantidad_solicitudes(self):
        for record in self:
            record.cantidad_solicitudes = len(record.solicitudes_ids)

    @api.depends('fechas_validacion')
    def _compute_name(self):
        for record in self:
            record.name = f"Fecha: {record.fechas_validacion}"


class Codigo23(models.Model):
    _name = 'mgpp.codigo23'
    _description = 'Código Único 23 para Solicitudes'

    name = fields.Char(string="Código 23", required=True)
    fecha_validacion_id = fields.Many2one(
        'mgpp.fecha_validacion',
        string="Fecha de Validación",
        required=True,
        domain="[('id', 'in', valid_fecha_ids),('seleccionado', '=', False)]",
        help="Selecciona una Fecha de Validación que contenga al menos una solicitud pendiente de aprobación.", ondelete='cascade'
    )
    solicitudes_ids = fields.Many2many(
        'mgpp.solicitud_rebaja',
        string="Solicitudes Asociadas",
        compute='_compute_solicitudes_ids',
        store=False,  # Campo computado no persistente
        help="Selecciona solo solicitudes con estado 'Pendiente de Aprobación' y asociadas a la Fecha de Validación seleccionada."
    )
    cantidad_solicitudes = fields.Integer(
        string="Cantidad de Solicitudes",
        compute='_compute_cantidad_solicitudes',
        store=True
    )
    estado = fields.Selection(
        [('sin_aplicar', 'Sin Aplicar'), ('aplicado', 'Aplicado')],
        string="Estado",
        default='sin_aplicar',
        required=True
    )
    valid_fecha_ids = fields.Many2many(
        'mgpp.fecha_validacion',
        compute='_compute_valid_fecha_ids',
        string="Fechas Válidas"
    )
    circular_ids = fields.One2many(
        'mgpp.circular', 'codigo23_id', string="Circulares Enviadas"
    )
    @api.depends('fecha_validacion_id')
    def _compute_solicitudes_ids(self):
        for record in self:
            if record.fecha_validacion_id:
                solicitudes = self.env['mgpp.solicitud_rebaja'].search([
                    ('estado', '=', 'pendiente_aprobacion'),
                    ('codigo_23_aplicado', '=', False),
                    ('fecha_validacion_id', '=', record.fecha_validacion_id.id)
                ])
                record.solicitudes_ids = solicitudes
            else:
                record.solicitudes_ids = False

    @api.depends('solicitudes_ids')
    def _compute_cantidad_solicitudes(self):
        for record in self:
            record.cantidad_solicitudes = len(record.solicitudes_ids)

    @api.depends('solicitudes_ids')
    def _compute_valid_fecha_ids(self):
        for record in self:
            # Obtener fechas de validación que tienen al menos una solicitud pendiente de aprobación
            valid_ids = self.env['mgpp.fecha_validacion'].search([
                ('solicitudes_ids', '!=', False),
                ('solicitudes_ids.estado', '=', 'pendiente_aprobacion')
            ]).ids
            record.valid_fecha_ids = valid_ids
            
            
            
            
    def enviar_circular_a_establecimientos(self):
        for record in self:
            # Obtener ubicaciones de lote relacionadas con las solicitudes
            ubicaciones = record.solicitudes_ids.mapped('lote_id.ubicacion_lote_ids')
            
            # Crear circulares para cada establecimiento
            for ubicacion in ubicaciones:
                circular_vals = {
                    'name': f"Circular para {ubicacion.establecimiento_id.name} - {record.name}",
                    'codigo23_id': record.id,
                    'complejo_id': ubicacion.complejo_id.id,
                    'establecimiento_id': ubicacion.establecimiento_id.id,
                    'sucursal_id': ubicacion.complejo_id.sucursal_id.id,  # Asumiendo que el Complejo tiene relación con Sucursal
                }
                self.env['mgpp.circular'].create(circular_vals)
        
            
            
            
            
            
            
    # def enviar_circular_a_complejos(self):
    #     """Envía una circular con el Código 23 a los complejos relacionados."""
    #     for record in self:
    #         # Obtener complejos relacionados con las solicitudes
    #         complejos = record.solicitudes_ids.mapped('lote_id.ubicacion_lote_ids.complejo_id')
            
    #         for complejo in complejos:
    #             self.env['mgpp.circular'].create({
    #                 'name': f"Circular para {complejo.name} - {record.name}",
    #                 'codigo23_id': record.id,
    #                 'complejo_id': complejo.id,
    #             })
    
                
                
                
                
                
                
    # def aplicar_circular(self):
    #     """Crea una instancia en la clase CircularPrecios por cada solicitud y lote asociado, 
    #     vinculando con la empresa correspondiente."""
    #     circular_precios_obj = self.env['mgpp.circular_precios']
    #     ubicacion_lote_obj = self.env['mgpp.ubicacion_lote']

    #     for solicitud in self.solicitudes_ids:
    #         for lote in solicitud.rebaja_id.lote_id:
    #             # Buscar la ubicación del lote para obtener el complejo
    #             ubicacion_lote = ubicacion_lote_obj.search([('lote_id', '=', lote.id)], limit=1)
    #             if not ubicacion_lote:
    #                 continue  # Si no hay ubicación asociada, omitir este lote
                
    #             # Encontrar la instancia de miempresa correspondiente al complejo
    #             miempresa = self.env['mgpp.miempresa'].search([('complejo_id', '=', ubicacion_lote.complejo_id.id)], limit=1)
    #             if not miempresa:
    #                 continue  # Si no hay empresa asociada, omitir este lote
                
    #             # Crear la instancia de CircularPrecios
    #             circular_precios_obj.create({
    #                 'name': f'Circular-{self.name}',
    #                 'lote_id': lote.id,
    #                 'solicitud_rebaja_id': solicitud.id,
    #                 'miempresa_id': miempresa.id,  # Vincular con la empresa encontrada
    #                 'fecha_emision': fields.Date.today(),
    #                 'fecha_ejecucion': fields.Date.today() + timedelta(days=7),  # Ajustar según la lógica
    #             })

    #     # Cambiar el estado de la instancia actual
    #     self.estado = 'aplicado'
class Circular(models.Model):
    _name = 'mgpp.circular'
    _description = 'Circular para Complejos'

    name = fields.Char(string="Título", required=True)
    codigo23_id = fields.Many2one('mgpp.codigo23', string="Código 23", required=True, ondelete='cascade')
    complejo_id = fields.Many2one('mgpp.complejo', string="Complejo", required=True, ondelete='cascade')
    establecimiento_id = fields.Many2one('mgpp.establecimiento', string="Establecimiento", required=True, ondelete='cascade')
    sucursal_id = fields.Many2one('mgpp.sucursal', string="Sucursal", required=True, ondelete='cascade')
    fecha_envio = fields.Datetime(string="Fecha de Envío", default=fields.Datetime.now) 
    
    @api.model
    def get_circular_domain(self):
        """Construye un dominio dinámico basado en el usuario conectado."""
        user = self.env.user
        domain = []

        # Buscar la sucursal, complejo, o establecimiento al que pertenece el usuario
        sucursal = self.env['mgpp.sucursal'].search([('usuario_ids', 'in', [user.id])], limit=1)
        if sucursal:
            # Usuario pertenece a una Sucursal
            domain = [('sucursal_id', '=', sucursal.id)]
        else:
            complejo = self.env['mgpp.complejo'].search([('usuario_ids', 'in', [user.id])], limit=1)
            if complejo:
                # Usuario pertenece a un Complejo
                domain = [('complejo_id', '=', complejo.id)]
            else:
                establecimiento = self.env['mgpp.establecimiento'].search([('usuario_ids', 'in', [user.id])], limit=1)
                if establecimiento:
                    # Usuario pertenece a un Establecimiento
                    domain = [('establecimiento_id', '=', establecimiento.id)]

        return domain  
# class CircularPrecios(models.Model):
#     _name = 'mgpp.circular_precios'
#     _description = 'Circular de Precios'

#     name = fields.Char(string="Código Circular", required=True)
#     lote_id = fields.Many2one('mgpp.lote', string='Lote', required=True)
#     lote_producto = fields.Char(string='Producto del Lote', compute='_compute_lote_info', store=True)
#     lote_name = fields.Char(string='Nombre del Lote', compute='_compute_lote_info', store=True)
    
#     solicitud_rebaja_id = fields.Many2one('mgpp.solicitud_rebaja', string='Solicitud de Rebaja', required=True)
#     solicitud_codigo = fields.Char(string='Código de Solicitud', compute='_compute_solicitud_info', store=True)
#     solicitud_name = fields.Char(string='Nombre de Solicitud', compute='_compute_solicitud_info', store=True)
#     solicitud_descuento = fields.Float(string='Descuento', compute='_compute_solicitud_info', store=True)
#     solicitud_fecha = fields.Date(string='Fecha de Solicitud', compute='_compute_solicitud_info', store=True)
#     solicitud_precio_aplicado = fields.Float(string='Precio Aplicado', compute='_compute_solicitud_info', store=True)
    
#     estado = fields.Selection([
#         ('no_aplicado', 'No Aplicado'),
#         ('aplicado', 'Aplicado')
#     ], string="Estado", default='no_aplicado', required=True)
#     fecha_emision = fields.Date(string='Fecha de Emisión', required=True, default=fields.Date.today)
#     fecha_ejecucion = fields.Date(string='Fecha de Ejecución', required=True)
#     miempresa_id = fields.Many2one('mgpp.miempresa', string='Mi Empresa', ondelete='cascade')

#     @api.depends('lote_id')
#     def _compute_lote_info(self):
#         for record in self:
#             record.lote_producto = record.lote_id.producto_id.name if record.lote_id and record.lote_id.producto_id else ''
#             record.lote_name = record.lote_id.codigo_lote if record.lote_id else ''

#     @api.depends('solicitud_rebaja_id')
#     def _compute_solicitud_info(self):
#         for record in self:
#             solicitud = record.solicitud_rebaja_id
#             record.solicitud_codigo = solicitud.codigo_23 if solicitud else ''
#             record.solicitud_name = solicitud.name if solicitud else ''
#             record.solicitud_descuento = solicitud.descuento_rebaja if solicitud else 0.0
#             record.solicitud_fecha = solicitud.fecha_solicitud if solicitud else False
#             record.solicitud_precio_aplicado = solicitud.precio_aplicado if solicitud else 0.0
