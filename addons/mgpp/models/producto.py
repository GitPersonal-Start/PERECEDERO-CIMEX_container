# -*- coding: utf-8 -*-
from asyncio import exceptions
from xml.dom import ValidationErr
from odoo.exceptions import ValidationError
from odoo import models, fields, api

class Producto(models.Model):
    _name = 'mgpp.producto'
    _description = 'mgpp.producto'

    name = fields.Char(string='Nombre del Producto', required=True, help="Nombre descriptivo del producto.")
    categoria_id = fields.Many2one('mgpp.categoria', string="Categoría", required=True, help="Categoría del producto.", domain="[('estado', '=', True)]")
    descripcion = fields.Text(string="Descripción", help="Descripción detallada del producto.")
    lotes_ids = fields.One2many('mgpp.lote', 'producto_id', string="Lotes", help="Lotes asociados al producto.")
    estado = fields.Selection(
        [('activo', 'Activo'), ('inactivo', 'Inactivo')],
        string='Estado',
        default='activo',
        required=True,
        help="Estado actual del producto."
    )
    create_date = fields.Datetime(string='Fecha de Creación', readonly=True)
    write_date = fields.Datetime(string='Fecha de Modificación', readonly=True)
    existencia = fields.Integer(
        string='Existencia',
        compute="_compute_existencia",
        store=True,
        help="Cantidad total de productos disponibles en todos los lotes."
    )

    solicitudes_count = fields.Integer(
        string='Cantidad de Solicitudes',
        compute='_compute_solicitudes_count',
        store=True,
        help="Cantidad de solicitudes de rebaja asociadas a este producto."
    )
    
    @api.depends('lotes_ids.rebaja_id.solicitudes_ids')
    def _compute_solicitudes_count(self):
        for producto in self:
            solicitudes_count = 0
            for lote in producto.lotes_ids:
                solicitudes_count += len(lote.rebaja_id.solicitudes_ids)
            producto.solicitudes_count = solicitudes_count
    
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
    estado = fields.Boolean(string='Estado', required=True)
    
    lote_ids = fields.Many2many('mgpp.lote', string="Lotes")
    
class UM(models.Model):
    _name = 'mgpp.um'
    _description = 'mgpp.um'
    
    name = fields.Char(string='Unidad Medida', required=True)
    estado = fields.Boolean(string='Estado', required=True)
    
# class UbicacionLote(models.Model):
#     _name = 'mgpp.ubicacion'
#     _description = 'mgpp.ubicacion'

#     lote_id = fields.Many2one('mgpp.lote', string="Lote", required=True)
#     ubicacion_fisica_id = fields.Many2one('mgpp.ubicacion_fisica', string="Ubicacion Fisica", required=True)
#     cantidad = fields.Integer(string="Cantidad", required=True)
class UbicacionLote(models.Model):
    _name = 'mgpp.ubicacion_lote'
    _description = 'Ubicación de Lote'

    lote_id = fields.Many2one('mgpp.lote', string="Lote", required=True, ondelete='cascade')
    complejo_id = fields.Many2one('mgpp.complejo', string="Complejo", required=True)
    establecimiento_id = fields.Many2one('mgpp.establecimiento', string="Establecimiento", required=True)
    area_id = fields.Many2one('mgpp.area', string="Área", required=True)
    cantidad = fields.Integer(string="Cantidad", required=True)

    _sql_constraints = [
        ('unique_lote_area', 'unique(lote_id, area_id)', 'Un lote no puede estar en la misma área más de una vez.')
    ]

    @api.constrains('cantidad')
    def _check_cantidad(self):
        for record in self:
            if record.cantidad <= 0:
                raise ValidationError("La cantidad debe ser mayor que cero.")
    @api.onchange('ubicaciones_ids.complejo_id')
    def _onchange_complejo(self):
        for record in self:
            if record.ubicaciones_ids:
                record.ubicaciones_ids.establecimiento_id = False  # Reinicia establecimiento
                return {
                    'domain': {
                        'ubicaciones_ids.establecimiento_id': [('complejo_id', '=', record.ubicaciones_ids.complejo_id.id)]
                    }
                }
    @api.onchange('ubicaciones_ids.establecimiento_id')
    def _onchange_establecimiento(self):
        for record in self:
            if record.ubicaciones_ids:
                record.ubicaciones_ids.area_id = False  # Reinicia área
                return {
                    'domain': {
                        'ubicaciones_ids.area_id': [('establecimiento_id', '=', record.ubicaciones_ids.establecimiento_id.id)]
                    }
                }

class Lote(models.Model):
    _name = 'mgpp.lote'
    _description = 'Lote de Producto Perecedero'

    producto_id = fields.Many2one('mgpp.producto', string="Producto Asociado", required=True)
    codigo_lote = fields.Char(string="Código de Lote", required=True)
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento", required=True)
    ubicaciones_ids = fields.One2many('mgpp.ubicacion_lote', 'lote_id', string="Ubicaciones del Lote", ondelete='cascade')
    etiqueta_ids = fields.One2many('mgpp.etiqueta', 'lote_ids', string="Etiquetas" , domain="[('estado', '=', True)]")
    unidad_medida = fields.Many2one('mgpp.um', string="Unidad de Medida", required=True, domain="[('estado', '=', True)]")
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
    precio = fields.Float(string='Precio CUP', required=True, digits=(10, 2))
    costo = fields.Float(string='Costo CUP', required=True, digits=(10, 2))
    rebaja_id = fields.One2many('mgpp.rebaja', 'lote_id', string="Rebaja Asociada", readonly=True, ondelete='cascade')
    descuento_promedio = fields.Float(
        string='Descuento Promedio',
        compute='_compute_descuento_promedio',
        store=True,
        help="Descuento promedio aplicado a este lote."
    )
    
    
    @api.depends('rebaja_id.descuento_rebaja')
    def _compute_descuento_promedio(self):
        for lote in self:
            descuentos = lote.rebaja_id.mapped('descuento_rebaja')
            lote.descuento_promedio = sum(descuentos) / len(descuentos) if descuentos else 0
            
    @api.constrains('codigo_lote')
    def _check_codigo_lote(self):
        for record in self:
            # Validar que solo contenga números
            if not record.codigo_lote.isdigit():
                raise ValidationError("El código de lote solo puede contener números.")

            # Validar la longitud del código de barras
            longitud_esperada = 13  # Cambia este valor según el estándar que uses (EAN-13, UPC-A, etc.)
            if len(record.codigo_lote) != longitud_esperada:
                raise ValidationError(f"El código de lote debe tener exactamente {longitud_esperada} dígitos.")        
    _sql_constraints = [
        ('unique_fecha_vencimiento_producto',
         'UNIQUE(producto_id, fecha_vencimiento)',
         'Un producto no puede tener más de un lote con la misma fecha de vencimiento.')
    ]
    @api.depends('producto_id')
    def _compute_categoria(self):
        for record in self:
            record.categoria = record.producto_id.categoria_id
    @api.depends('ubicaciones_ids.cantidad')
    def _compute_cantidad(self):
        for record in self:
            record.cantidad = sum(record.ubicaciones_ids.mapped('cantidad'))
    @api.constrains('precio', 'costo')
    def _check_precio_costo(self):
        for record in self:
            if record.precio <= 0:
                raise ValidationError("El precio debe ser mayor que cero.")
            if record.costo <= 0:
                raise ValidationError("El costo debe ser mayor que cero.")
            if record.costo > record.precio:
                raise ValidationError("El costo no puede exceder el precio.")   
    @api.constrains('fecha_vencimiento')
    def _check_fecha_vencimiento(self):
        for record in self:
            if record.fecha_vencimiento < fields.Date.today():
                raise ValidationError("La fecha de vencimiento no puede ser anterior a hoy.")  
            
    def unlink(self):
        rebajas_lote = self.env['mgpp.rebaja_lote'].search([('lote_id', 'in', self.ids)])
        if rebajas_lote:
            rebajas_lote.unlink()
        # Primero, eliminamos los registros de circular_precios asociados
        circular_precios = self.env['mgpp.circular_precios'].search([('lote_id', 'in', self.ids)])
        if circular_precios:
            circular_precios.unlink()  # Esto eliminará los registros de circular_precios
        return super(Lote, self).unlink()  # Luego, eliminamos el lote

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
    @api.constrains('ubicaciones_ids')
    def _check_ubicaciones(self):
        for record in self:
            if not record.ubicaciones_ids:
                raise ValidationError("Debes agregar al menos una ubicación antes de guardar el lote.")

class RebajaLote(models.Model):
    _name = 'mgpp.rebaja_lote'
    _description = 'Rebaja de Cantidades de Lote'

    producto_id = fields.Many2one('mgpp.producto', string="Producto", required=True)
    lote_id = fields.Many2one('mgpp.lote', string="Lote", required=True, domain="[('producto_id', '=', producto_id)]")
    establecimiento_id = fields.Many2one('mgpp.establecimiento', string="Establecimiento", required=True)
    area_id = fields.Many2one('mgpp.area', string="Área", required=True)
    cantidad_rebajada = fields.Integer(string="Cantidad Rebajada", required=True)
    fecha_rebaja = fields.Date(string="Fecha de Rebaja", default=fields.Date.context_today, readonly=True)
    motivo_descuento = fields.Selection(
        [('merma', 'Merma'), ('venta', 'Venta'), ('rotura', 'Rotura'), ('otro', 'Otro')],
        default='merma', string="Motivo del Descuento", required=True)
    descripcion = fields.Text(string='Descripción')
    
    @api.onchange('producto_id')
    def _onchange_producto(self):
        """
        Filtra los lotes disponibles para el producto seleccionado.
        """
        self.lote_id = False  # Reset lote selection
        return {
            'domain': {
                'lote_id': [('producto_id', '=', self.producto_id.id)]
            }
        }
    
    @api.onchange('lote_id')
    def _onchange_lote(self):
        """
        Filtra las ubicaciones disponibles para el lote seleccionado.
        """
        self.establecimiento_id = False
        self.area_id = False
        return {
            'domain': {
                'establecimiento_id': [('id', 'in', self.lote_id.ubicaciones_ids.mapped('establecimiento_id.id'))],
                'area_id': [('id', 'in', self.lote_id.ubicaciones_ids.mapped('area_id.id'))],
            }
        }
    
    @api.constrains('cantidad_rebajada', 'motivo_descuento', 'descripcion')
    def _check_cantidad_rebajada_y_descripcion(self):
        """
        Valida la cantidad rebajada y la descripción cuando el motivo es 'otro'.
        """
        for record in self:
            # Verificar que el motivo "otro" tenga descripción
            if record.motivo_descuento == 'otro' and not record.descripcion:
                raise exceptions.ValidationError("Debe proporcionar una descripción para el motivo 'Otro'.")

            # Buscar la ubicación seleccionada
            ubicacion = self.env['mgpp.ubicacion_lote'].search([
                ('lote_id', '=', record.lote_id.id),
                ('establecimiento_id', '=', record.establecimiento_id.id),
                ('area_id', '=', record.area_id.id)
            ], limit=1)

            if not ubicacion:
                raise exceptions.ValidationError("No se encontró la ubicación seleccionada para este lote.")

            # Verificar que la cantidad a rebajar no exceda la cantidad disponible
            if record.cantidad_rebajada > ubicacion.cantidad:
                raise exceptions.ValidationError(
                    f"La cantidad a rebajar ({record.cantidad_rebajada}) excede la cantidad disponible en la ubicación ({ubicacion.cantidad})."
                )

            # Actualizar la cantidad en la ubicación y en el lote
            ubicacion.cantidad -= record.cantidad_rebajada
            record.lote_id.cantidad -= record.cantidad_rebajada
