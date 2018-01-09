from odoo import api, models, tools, fields

import logging

class sede(models.Model):

    _name = 'cursos.sede'
    
    name = fields.Char('Nombre')

class curso(models.Model):

    _name = 'cursos.curso'

    name = fields.Char('Nombre')
    sede_id = fields.Many2one('cursos.sede','Sede', required=True)

class horario(models.Model):

    _name = 'cursos.horario'

    curso_id = fields.Many2one('cursos.curso','Curso', required=True)
    cupo = fields.Integer('Cupo')
    dia = fields.Selection([
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miercoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes')], 'Dia')
    profesores = fields.Many2many('res.partner','horario_partner_rel1', 'horario_id','partner_id', 'Profesores')
    alumnos = fields.Many2many('res.partner','horario_partner_rel2', 'horario_id','partner_id', 'Alumnos')
    hora_inicio = fields.Float('Hora Inicio')
    hora_fin = fields.Float('Hora Fin')
