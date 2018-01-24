
from odoo import api, models, tools, fields

import logging

class cursos_res_partner(models.Model):
    _inherit = 'res.partner'

    historial_curso_ids = fields.One2many('cursos.historial','alumno_id','Historial')
    asistencia_curso_ids = fields.One2many('cursos.asistencia','alumno_id','Asistencia')
