# -*- coding: utf-8 -*-

from odoo import api, models, tools, fields

import logging

class cursos_res_partner(models.Model):
    _inherit = 'res.partner'

    historial_curso_ids = fields.One2many('cursos.historial','alumno_id','Historial')
    historial_congelado_ids = fields.One2many('cursos.congelamiento','alumno_id','Congelamientos')
    asistencia_curso_ids = fields.One2many('cursos.asistencia','alumno_id','Asistencia')
    curso_asignado = fields.Many2one('cursos.horario',compute='_get_curso_asignado',string="Curso asignado")

    type = fields.Selection(default='other')

    def _get_curso_asignado(self):
        horario_id = 0
        for cliente in self:
            for linea in cliente.historial_curso_ids:
                if linea.fecha_fin == False:
                    horario_id = linea.horario_id
                    cliente.curso_asignado = linea.horario_id

                    