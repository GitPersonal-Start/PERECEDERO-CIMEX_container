# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DireccionMixin(models.AbstractModel):
    _name = 'mgpp.direccion_mixin'
    _description = 'Mixin para datos de dirección'

    calle = fields.Char(string='Calle', required=True)
    calle2 = fields.Char(string='Calle 2')
    numero = fields.Char(string='Número')
    municipio = fields.Char(string='Municipio', required=True)
    provincia = fields.Char(string='Provincia', required=True)
    codigo_postal = fields.Char(string='Código Postal')
class ContactoMixin(models.AbstractModel):
    _name = 'mgpp.contacto_mixin'
    _description = 'Mixin para datos de contacto'

    telefono = fields.Char(string='Teléfono')
    correo = fields.Char(string='Correo Electrónico')
    descripcion = fields.Text(string='Descripción')
    estado = fields.Boolean(string='Estado', default=True)
class Sucursal(models.Model):
    _name = 'mgpp.sucursal'
    _description = 'Sucursal'
    _inherit = ['mgpp.direccion_mixin', 'mgpp.contacto_mixin']

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    complejos_ids = fields.One2many('mgpp.complejo', 'sucursal_id', string='Complejos')
    empleados_count = fields.Integer(string='Número de Complejos' , compute='_compute_empleados_count', store=True)
    usuario_ids = fields.Many2many('res.users', string='Usuarios')

    @api.depends('complejos_ids')
    def _compute_empleados_count(self):
        for record in self:
            record.empleados_count = len(record.complejos_ids)

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'El código de la sucursal debe ser único.')
    ]

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if len(record.name) < 3:
                raise ValidationError('El nombre de la sucursal debe tener al menos 3 caracteres.')
class Complejo(models.Model):
    _name = 'mgpp.complejo'
    _description = 'Complejo'
    _inherit = ['mgpp.direccion_mixin', 'mgpp.contacto_mixin']

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    sucursal_id = fields.Many2one('mgpp.sucursal', string='Sucursal', required=True, ondelete='cascade')
    establecimientos_ids = fields.One2many('mgpp.establecimiento', 'complejo_id', string='Establecimientos')
    empleados_count = fields.Integer(string='Número de Establecimientos', compute='_compute_empleados_count', store=True)
    usuario_ids = fields.Many2many('res.users', string='Usuarios')

    @api.depends('establecimientos_ids')
    def _compute_empleados_count(self):
        for record in self:
            record.empleados_count = len(record.establecimientos_ids)

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'El código del complejo debe ser único.')
    ]
    # @api.model
    # def create(self, vals):
    #     # Crear la instancia del complejo
    #     complejo = super(Complejo, self).create(vals)

    #     # Crear automáticamente una instancia de miempresa
    #     self.env['mgpp.miempresa'].create({
    #         'name': complejo.name,  # Usar el nombre del complejo
    #         'complejo_id': complejo.id,  # Relacionar con el complejo
    #         'estado': 'no_aplicado'
    #     })

    #     return complejo
    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if len(record.name) < 3:
                raise ValidationError('El nombre del complejo debe tener al menos 3 caracteres.')
class Establecimiento(models.Model):
    _name = 'mgpp.establecimiento'
    _description = 'Establecimiento'
    _inherit = ['mgpp.direccion_mixin', 'mgpp.contacto_mixin']

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    complejo_id = fields.Many2one('mgpp.complejo', string='Complejo', required=True, ondelete='cascade')
    areas_ids = fields.One2many('mgpp.area', 'establecimiento_id', string='Áreas')
    empleados_count = fields.Integer(string='Número de Áreas', compute='_compute_empleados_count', store=True)
    usuario_ids = fields.Many2many('res.users', string='Usuarios')

    @api.depends('areas_ids')
    def _compute_empleados_count(self):
        for record in self:
            record.empleados_count = len(record.areas_ids)

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'El código del establecimiento debe ser único.')
    ]

    @api.onchange('complejo_id')
    def _onchange_complejo(self):
        if self.complejo_id:
            self.provincia = self.complejo_id.provincia
class Area(models.Model):
    _name = 'mgpp.area'
    _description = 'Área'

    name = fields.Char(string='Nombre del Área', required=True)
    codigo = fields.Char(string='Código', required=True, unique=True)
    establecimiento_id = fields.Many2one('mgpp.establecimiento', string='Establecimiento', required=True, ondelete='cascade')
    estado = fields.Boolean(string='Estado', default=True)
    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'El código del área debe ser único.')
    ]

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if len(record.name) < 3:
                raise ValidationError('El nombre del área debe tener al menos 3 caracteres.')

    @api.onchange('establecimiento_id')
    def _onchange_establecimiento(self):
        if self.establecimiento_id:
            self.estado = self.establecimiento_id.estado
            
# class MiEmpresa(models.Model):
#     _name = 'mgpp.miempresa'
#     _description = 'Mi Empresa'

#     name = fields.Char(string='Nombre', required=True)
#     complejo_id = fields.Many2one('mgpp.complejo', string='Complejo', required=True, ondelete='cascade')
#     circular_precios_ids = fields.One2many('mgpp.circular_precios', 'miempresa_id', string='Circulares de Precios')
#     estado = fields.Selection([
#         ('no_aplicado', 'No Aplicado'),
#         ('aplicado', 'Aplicado')
#     ], string="Estado", default='no_aplicado', required=True)
