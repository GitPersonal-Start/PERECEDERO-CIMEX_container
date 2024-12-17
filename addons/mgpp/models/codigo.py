# -*- coding: utf-8 -*-

# from odoo import models, fields, api
# # class FechaFinalizacion(models.Model):
# #     _name = 'mgpp.fecha_finalizacion'
# #     _description = 'Código 23 para Solicitudes de Rebaja'

# #     fecha = fields.Datetime(string="Fecha de Validación", required=True)
# #     solicitud_ids = fields.One2many(
# #         'mgpp.solicitud_rebaja', 'fecha_finalizacion_id', string="Solicitudes"
# #     )
        
# class FechaValidacion(models.Model):
#     _name = 'mgpp.fecha_validacion'
#     _description = 'Fecha de Validación de Solicitudes'

#     fechas_validacion = fields.Date(string="Fecha de Validación", required=True, unique=True)
#     name = fields.Char(string="Descripción", compute='_compute_name', store=True)
#     solicitudes_ids = fields.One2many('mgpp.solicitud_rebaja', 'fecha_validacion_id', string="Solicitudes Asociadas")
#     cantidad_solicitudes = fields.Integer(string="Cantidad de Solicitudes", compute='_compute_cantidad_solicitudes', store=True)

#     @api.depends('solicitudes_ids')
#     def _compute_cantidad_solicitudes(self):
#         for record in self:
#             record.cantidad_solicitudes = len(record.solicitudes_ids)
#     @api.depends('fechas_validacion')
#     def _compute_name(self):
#         for record in self:
#             record.name = f"Fecha:{record.fechas_validacion}"
# class Codigo23(models.Model):
#     _name = 'mgpp.codigo23'
#     _description = 'Código Único 23 para Solicitudes'

#     name = fields.Char(string="Código 23", required=True)
#     fecha_validacion_id = fields.Many2one('mgpp.fecha_validacion', string="Fecha de Validación", required=True, domain="[('id', 'in', valid_fecha_ids)]")
#     solicitudes_ids = fields.Many2many(
#         'mgpp.solicitud_rebaja',
#         string="Solicitudes Asociadas",
#         domain="[('estado', '=', 'pendiente_aprobacion'), ('codigo_23_aplicado', '=', False), ('fechas_validacion', '=', fecha_validacion_id)]",
#         help="Selecciona solo solicitudes con estado 'Aprobado'."
#     )
#     cantidad_solicitudes = fields.Integer(
#         string="Cantidad de Solicitudes", compute='_compute_cantidad_solicitudes', store=True)
#     estado = fields.Selection(
#         [('sin_aplicar', 'Sin Aplicar'), ('aplicado', 'Aplicado')],
#         string="Estado",
#         default='sin_aplicar',
#         required=True
#     )
#     valid_fecha_ids = fields.Many2many(
#         'mgpp.fecha_validacion', 
#         compute='_compute_valid_fecha_ids', 
#         string="Fechas válidas"
#     )
    
#     @api.depends('solicitudes_ids')
#     def _compute_cantidad_solicitudes(self):
#         for record in self:
#             record.cantidad_solicitudes = len(record.solicitudes_ids)
#     @api.depends('fecha_validacion_id.solicitudes_ids')
#     def _compute_valid_fecha_ids(self):
#         for record in self:
#             # Verificar que la fecha de validación tenga al menos una solicitud con estado 'pendiente_aprobacion'
#             valid_ids = self.env['mgpp.fecha_validacion'].search([
#                 ('solicitudes_ids.estado', '=', 'pendiente_aprobacion')
#             ]).ids
#             record.valid_fecha_ids = valid_ids
            
            
from odoo import models, fields, api

class FechaValidacion(models.Model):
    _name = 'mgpp.fecha_validacion'
    _description = 'Fecha de Validación de Solicitudes'

    fechas_validacion = fields.Date(string="Fecha de Validación", required=True, unique=True)
    name = fields.Char(string="Descripción", compute='_compute_name', store=True)
    solicitudes_ids = fields.One2many('mgpp.solicitud_rebaja', 'fecha_validacion_id', string="Solicitudes Asociadas")
    cantidad_solicitudes = fields.Integer(string="Cantidad de Solicitudes", compute='_compute_cantidad_solicitudes', store=True)

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
        domain="[('id', 'in', valid_fecha_ids)]",
        help="Selecciona una Fecha de Validación que contenga al menos una solicitud pendiente de aprobación."
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
