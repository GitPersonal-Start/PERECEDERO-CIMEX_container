# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Producto(models.Model):
    _name = 'mgpp.producto'
    _description = 'mgpp.producto'

    name = fields.Char(string='Nombre del Producto', required=True)
    categoria = fields.Many2one('mgpp.categoria', string="Categoria", required=True)
    descripcion = fields.Text(string="Descripcion")
    lotes_ids = fields.One2many('mgpp.lote', 'producto_id', string="Lotes")
    estado = fields.Boolean(string='Estado' )
    create_date = fields.Datetime(string='Fecha de Creacion', readonly=True)
    write_date = fields.Datetime(string='Fecha de Modificacion', readonly=True)
    existencia = fields.Integer(string='Existencia', compute="_compute_existencia", store=True)
    
    @api.depends('lotes_ids.cantidad')
    def _compute_existencia(self):
        for record in self:
            record.existencia = sum(record.lotes_ids.mapped('cantidad'))
            
class Categoria(models.Model):
    _name = 'mgpp.categoria'
    _description = 'mgpp.categoria'
    
    name = fields.Char(string='Categorias', required=True)
    descripcion = fields.Text(string='Descripcion')
    estado = fields.Boolean(string='Estado', required=True)
    parent_id = fields.Many2one('mgpp.categoria', string="Categoria Padre", ondelete='cascade')
    child_ids = fields.One2many('mgpp.categoria', 'parent_id', string="Subcategorias")
    
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.parent_id:
                name = f"{record.parent_id.name}/{name}"
            result.append((record.id, name))
        return result
    
class Etiquetas(models.Model):
    _name = 'mgpp.etiqueta'
    _description = 'mgpp.etiqueta'
    
    name = fields.Char(string='Etiqueta', required=True)
    descripcion = fields.Text(string='Descripcion')
    estado = fields.Boolean(string='Estado')
    
    lote_ids = fields.Many2many('mgpp.lote', string="Lotes")
    
class UM(models.Model):
    _name = 'mgpp.um'
    _description = 'mgpp.um'
    
    name = fields.Char(string='Unidad Medida', required=True)
    estado = fields.Boolean(string='Estado')
    
class UbicacionLote(models.Model):
    _name = 'mgpp.ubicacion'
    _description = 'mgpp.ubicacion'

    lote_id = fields.Many2one('mgpp.lote', string="Lote", required=True)
    ubicacion_fisica_id = fields.Many2one('mgpp.ubicacion_fisica', string="Ubicacion Fisica", required=True)
    cantidad = fields.Integer(string="Cantidad", required=True)
    
class UbicacionFisica(models.Model):
    _name = 'mgpp.ubicacion_fisica'
    _description = 'Ubicacion Fisica'

    name = fields.Char(string="Nombre", compute="_compute_name", store=True)
    empresa_id = fields.Many2one('mgpp.empresa', string="Empresa", required=True)
    area_id = fields.Many2one('mgpp.area', string="Area", required=True)

    @api.depends('empresa_id', 'area_id')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.empresa_id.name} - {record.area_id.name}"

    @api.onchange('empresa_id')
    def _onchange_empresa(self):
        if self.empresa_id:
            return {
                'domain': {'area_id': [('empresa_id', '=', self.empresa_id.id)]}
            }
        else:
            return {'domain': {'area_id': []}}

class Lote(models.Model):
    _name = 'mgpp.lote'
    _description = 'Lote de Producto Perecedero'

    producto_id = fields.Many2one('mgpp.producto', string="Producto Asociado", required=True)
    codigo_lote = fields.Char(string="Codigo de Lote", required=True)
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento", required=True)
    ubicaciones_ids = fields.One2many('mgpp.ubicacion', 'lote_id', string="Ubicaciones del Lote")
    etiqueta_ids = fields.One2many('mgpp.etiqueta', 'lote_ids', string="Etiquetas")
    unidad_medida = fields.Many2one('mgpp.um', string="Unidad de Medida", required=True)
    categoria = fields.Many2one(
        'mgpp.categoria', 
        string="Categoría", 
        compute="_compute_categoria", 
        store=True, 
        readonly=True
    )
    cantidad = fields.Integer(string='Cantidad',compute="_compute_cantidad", store=True)
    estado = fields.Selection(
        [('nuevo', 'Nuevo'), ('solicitado', 'Solicitado'), ('revisado', 'Revisado'), ('pendiente_aprobacion', 'Pendiente Aprobacion'), ('aprobado', 'Aprobado')],
        default='nuevo', string="Estado", readonly=True
    )
    create_date = fields.Datetime(string='Fecha de Creacion', readonly=True)
    write_date = fields.Datetime(string='Fecha de Modificacion', readonly=True)
    precio = fields.Float(string='Precio', required=True, digits=(10, 2))
    costo = fields.Float(string='Costo', required=True, digits=(10, 2))
    rebaja_id = fields.One2many('mgpp.rebaja', 'lote_id', string="Rebaja Asociada", readonly=True)
    
    _sql_constraints = [
        (
            'unique_producto_fecha_vencimiento',
            'unique(producto_id, fecha_vencimiento)',
            'No se pueden crear lotes con la misma fecha de vencimiento para el mismo producto.'
        ),
    ]
    @api.depends('producto_id')
    def _compute_categoria(self):
        for record in self:
            record.categoria = record.producto_id.categoria
    def create_new_ubicacion_fisica(self):
        """Abre un formulario para crear una nueva ubicacion fisica."""
        return {
            'name': 'Nueva Ubicacion Fisica',
            'type': 'ir.actions.act_window',
            'res_model': 'mgpp.ubicacion_fisica',
            'view_mode': 'form',
            'target': 'new',  # Abre el formulario en un modal
        }
    @api.depends('ubicaciones_ids.cantidad')
    def _compute_cantidad(self):
        for record in self:
            record.cantidad = sum(record.ubicaciones_ids.mapped('cantidad'))
          
    @api.model
    def create(self, vals):
        # Crear el lote
        lote = super(Lote, self).create(vals)
        # Obtener el nombre del producto asociado al lote
        producto_nombre = lote.producto_id.name if lote.producto_id else 'Producto Desconocido'
        # Crear la rebaja automáticamente asociada al lote
        self.env['mgpp.rebaja'].create({
            'name': f"{producto_nombre} - {lote.codigo_lote}",
            'lote_id': lote.id,
            'precio_inicial': lote.precio,
            'precio_actual': lote.precio,
            'fecha_finalizacion': lote.fecha_vencimiento,
            'descuento_rebaja': '0',
            'estado': 'sin_rebaja', 
        })

        return lote
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.codigo_lote))
        return result