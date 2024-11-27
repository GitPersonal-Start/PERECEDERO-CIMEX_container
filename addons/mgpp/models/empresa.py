# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Empresa(models.Model):
    _name = 'mgpp.empresa'
    _description = 'mgpp.empresa'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    image = fields.Image(max_width=120, max_height=120)
    telefono = fields.Char(string='Teléfono')
    correo = fields.Char(string='Correo Electrónico')
    
    # Dirección
    calle = fields.Char(string='Calle', required=True)
    calle2 = fields.Char(string='Calle 2')
    num = fields.Char(string='No:')
    municipio = fields.Char(string='Municipio', required=True)
    provincia = fields.Char(string='Provincia', required=True)
    cp = fields.Char(string='Código Postal')
    areas_ids = fields.One2many('mgpp.area', 'empresa_id', string="Áreas")
    create_date = fields.Datetime(string='Fecha de Creación', readonly=True)
    write_date = fields.Datetime(string='Fecha de Modificación', readonly=True)
    empresa_padre_id = fields.Many2one('mgpp.empresa', string='Empresa Superior', ondelete='set null')
    empresas_hijas_ids = fields.One2many('mgpp.empresa', 'empresa_padre_id', string='Empresas Relacionadas')
    tipo_empresa = fields.Selection([
        ('complejo', 'Complejo'),
        ('sucursal', 'Sucursal'),
        ('establecimiento', 'Establecimiento')
    ], string='Tipo de Empresa', required=True)
    num_empleados = fields.Integer(string='Número de Empleados')
    descripcion = fields.Text(string='Descripción')
    estado = fields.Boolean(string='Estado')
    @api.onchange('tipo_empresa')
    def onchange_tipo_empresa(self):
        if self.tipo_empresa == 'sucursal':
            self.empresa_padre_id = False
            self.empresas_hijas_ids = [(5, 0, 0)]  # Limpiar las empresas hijas
        elif self.tipo_empresa == 'complejo':
            # Validar que solo se puedan seleccionar empresas hijas de tipo sucursal
            return {
                'domain': {'empresa_padre_id': [('tipo_empresa', '=', 'sucursal')]}
            }
        elif self.tipo_empresa == 'establecimiento':
            # Validar que solo se puedan seleccionar empresas hijas de tipo complejo
            return {
                'domain': {'empresa_padre_id': [('tipo_empresa', '=', 'complejo')]}
            }
    @api.model
    def default_get(self, fields):
        res = super(Empresa, self).default_get(fields)
        res['tipo_empresa'] = 'sucursal'  # Establece 'sucursal' como valor por defecto
        return res
class Area(models.Model):
    _name = 'mgpp.area'
    _description = 'mgpp.area'

    name = fields.Char(string='Nombre del Área', required=True)
    codigo = fields.Char(string='Código', required=True)
    create_date = fields.Datetime(string='Fecha de Creacion', readonly=True)
    write_date = fields.Datetime(string='Fecha de Modificacion', readonly=True)
    estado = fields.Boolean(string='Estado')
    empresa_id = fields.Many2one(
        'mgpp.empresa', 
        string="Establecimiento", 
        required=True
    )