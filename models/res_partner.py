# -*- coding: utf-8 -*-

from odoo import api, models, tools, fields

import logging

class cursos_res_partner(models.Model):
    _inherit = 'res.partner'

    fecha_inicio_congelamiento = fields.Date('Fecha Inicio congelamiento')
    fecha_congelamiento = fields.Date('Fecha Fin congelamiento')
    razon_congelamiento = fields.Char('Razón congelamiento')
    historial_curso_ids = fields.One2many('cursos.historial','alumno_id','Historial', readonly= True)
    asistencia_curso_ids = fields.One2many('cursos.asistencia','alumno_id','Asistencia')

    type = fields.Selection(default='other')
