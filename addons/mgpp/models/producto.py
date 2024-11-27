# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Producto(models.Model):
    _name = 'mgpp.producto'
    _description = 'mgpp.producto'

    name = fields.Char(string='Nombre del Producto', required=True)
    categoria = fields.Many2one('mgpp.categoria', string="Categoría", required=True)
    descripcion = fields.Text(string="Descripción")
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
    descripcion = fields.Text(string='Descripción')
    estado = fields.Boolean(string='Estado', required=True)
    parent_id = fields.Many2one('mgpp.categoria', string="Categoría Padre", ondelete='cascade')
    child_ids = fields.One2many('mgpp.categoria', 'parent_id', string="Subcategorías")
    
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
    descripcion = fields.Text(string='Descripción')
    estado = fields.Boolean(string='Estado')
    #lote_id = fields.Many2one('mgpp.lote', string="Lote", required=True)
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
    ubicacion_fisica_id = fields.Many2one('mgpp.ubicacion_fisica', string="Ubicación Física", required=True)
    cantidad = fields.Integer(string="Cantidad", required=True)
    
class UbicacionFisica(models.Model):
    _name = 'mgpp.ubicacion_fisica'
    _description = 'Ubicación Física'

    name = fields.Char(string="Nombre", compute="_compute_name", store=True)
    empresa_id = fields.Many2one('mgpp.empresa', string="Empresa", required=True)
    area_id = fields.Many2one('mgpp.area', string="Área", required=True)

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
    codigo_lote = fields.Char(string="Código de Lote", required=True)
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento", required=True)
    ubicaciones_ids = fields.One2many('mgpp.ubicacion', 'lote_id', string="Ubicaciones del Lote")
    etiqueta_ids = fields.One2many('mgpp.etiqueta', 'lote_ids', string="Etiquetas")
    unidad_medida = fields.Many2one('mgpp.um', string="Unidad de Medida", required=True)
    categoria = fields.Many2one('mgpp.categoria', string="Categoria", required=True)
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
    def create_new_ubicacion_fisica(self):
        """Abre un formulario para crear una nueva ubicación física."""
        return {
            'name': 'Nueva Ubicación Física',
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

        # Crear la rebaja automáticamente asociada al lote
        self.env['mgpp.rebaja'].create({
            'lote_id': lote.id,
            'precio_inicial': lote.precio,
            'fecha_vencimiento': lote.fecha_vencimiento,
        })

        return lote
#     def verificar_descuentos(self):
#         today = fields.Date.today()  # Fecha actual
#         for lote in self:
#             # Contar las solicitudes existentes
#             solicitudes_existentes = len(lote.solicitudes_rebaja_ids)
#             if solicitudes_existentes >= 4:
#                 continue  # No crear más solicitudes si ya hay 4

#             # Calcular los días restantes hasta la fecha de vencimiento
#             if lote.fecha_vencimiento:
#                 dias_restantes = (lote.fecha_vencimiento - today).days
#             else:
#                 dias_restantes = 0

#             # Crear solicitudes según las condiciones de los días restantes
#             if dias_restantes <= 30 and not lote.solicitudes_rebaja_ids.filtered(lambda r: r.tipo_descuento == '30%'):
#                 lote._crear_solicitud_rebaja(30)
#             if dias_restantes <= 15 and not lote.solicitudes_rebaja_ids.filtered(lambda r: r.tipo_descuento == '50%'):
#                 lote._crear_solicitud_rebaja(50)
#             if dias_restantes <= 7 and not lote.solicitudes_rebaja_ids.filtered(lambda r: r.tipo_descuento == '70%'):
#                 lote._crear_solicitud_rebaja(70)
#             if dias_restantes <= 0 and not lote.solicitudes_rebaja_ids.filtered(lambda r: r.tipo_descuento == '80%'):
#                 lote._crear_solicitud_rebaja(80)

#     def _crear_solicitud_rebaja(self, porcentaje):
#         self.env['mgpp_app.solicitud_rebaja'].create({
#             'lote_id': self.id,
#             'tipo_descuento': f'{porcentaje}%',
#             'estado': 'pendiente',
#             'fecha_solicitud': fields.Date.today(),
#             'precio_descuento': self.precio * (1 - (porcentaje / 100)),
#         })
        
#     @api.depends('ubicaciones_ids.cantidad')
#     def _compute_cantidad_total(self):
#         for lote in self:
#             lote.cantidad = sum(lote.ubicaciones_ids.mapped('cantidad'))

# class SolicitudRebaja(models.Model):
#     _name = 'mgpp_app.solicitud_rebaja'
#     _description = 'Solicitud de Rebaja de Producto'

#     lote_id = fields.Many2one('mgpp_app.lote', string="Lote", required=True)
#     tipo_descuento = fields.Selection(
#         [('30%', '30%'), ('50%', '50%'), ('70%', '70%'), ('80%', '80%')],
#         string="Descuento", required=True
#     )
#     estado = fields.Selection(
#         [('pendiente', 'Pendiente'), ('revisado', 'Revisado'), ('aprobado', 'Aprobado')],
#         string="Estado", default='pendiente'
#     )
#     fecha_solicitud = fields.Date(string="Fecha de Solicitud", default=fields.Date.today, readonly=True)
#     precio_descuento = fields.Float(string="Precio con Descuento", digits=(10, 2))
#     observaciones = fields.Text(string="Observaciones")

#     def aprobar_solicitud(self):
#         """Marca la solicitud como aprobada"""
#         self.write({'estado': 'aprobado'})

#     def revisar_solicitud(self):
#         """Marca la solicitud como revisada"""
#         self.write({'estado': 'revisado'})

# class IrCron(models.Model):
#     _inherit = 'ir.cron'

#     @staticmethod
#     def crear_cron_generar_descuentos(env):
#         """Crear un cron job para verificar descuentos automáticamente."""
#         env.ref('mgpp_app.verificar_descuentos_cron', raise_if_not_found=False) or env['ir.cron'].create({
#             'name': 'Verificar Descuentos Automáticos',
#             'model_id': env['ir.model'].search([('model', '=', 'mgpp_app.lote')]).id,
#             'state': 'code',
#             'code': "model.verificar_descuentos()",
#             'interval_number': 1,
#             'interval_type': 'days',
#             'numbercall': -1,  # Infinito
#         })

# class UbicacionLote(models.Model):
#     _name = 'mgpp_app.ubicacion_lote'
#     _description = 'Ubicación de Lote en Establecimiento y Área'

#     lote_id = fields.Many2one('mgpp_app.lote', string="Lote", required=True)
    
#     # Selección de complejo, establecimiento y área
#     complejo_id = fields.Many2one('mgpp_app.complejo', string="Complejo", required=True)
#     establecimiento_id = fields.Many2one(
#         'mgpp_app.establecimiento', 
#         string="Establecimiento", 
#         required=True,
#         domain="[('complejo_id', '=', complejo_id)]"
#     )
#     area_id = fields.Many2one(
#         'mgpp_app.area', 
#         string="Área en Establecimiento", 
#         required=True,
#         domain="[('establecimiento_id', '=', establecimiento_id)]"
#     )
#     cantidad = fields.Integer(string="Cantidad", required=True)
