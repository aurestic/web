
from odoo import api, fields, models


class ListCustomColumnHelperWiz(models.TransientModel):
    _name = 'list.custom.column.helper.wiz'

    line_ids = fields.One2many(
        comodel_name="list.custom.column.helper.wiz.line",
        inverse_name="wiz_id",
    )
    view_id = fields.Many2one(
        comodel_name="ir.ui.view",
        string="View",
        readonly=True,
        required=True,
    )
    type_desc = fields.Selection(
        selection=[
            ('user', 'User'),
            ('all', 'All'),
        ],
        string="Type",
        required=True,
        readonly=True,
    )

    @api.model
    def default_get(self, fields):
        defaults = super(ListCustomColumnHelperWiz, self).default_get(fields)
        view_id = self._context.get('view_id')
        view = self.env["ir.ui.view"].browse(view_id)
        column_desc = view.custom_column_desc()
        fields_desc = column_desc.get("fields")
        fields_names = sorted(
            filter(lambda name: '__' != name[:2], fields_desc.keys())
        )
        line_datas = []
        for field_name in fields_names:
            sequence, visible = view.get_field_sequence_in_view(field_name)
            added = sequence > -1
            if not added:
                sequence = 1000
            line_datas += [(0, 0, {
                'field_name': field_name,
                'field_string': fields_desc.get(field_name).get("string"),
                'added': added,
                'visible': visible,
                'sequence': sequence,
            })]

        defaults.update({
            'view_id': view.id,
            'type_desc': column_desc.get('type'),
            'line_ids': line_datas,
        })
        return defaults

    def reload(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def save(self):
        self.ensure_one()
        fields_datas = self.line_ids.filtered(
            lambda l: l.added
        ).mapped(lambda l: {
            'field_name': l.field_name,
            'visible': l.visible,
        })
        customized_view = self.view_id.custom_column(
            self.type_desc, fields_datas
        )
        return self.reload()

    def action_save_user(self):
        self.ensure_one()
        self.type_desc = 'user'
        return self.save()

    def action_save_all(self):
        self.ensure_one()
        self.type_desc = 'all'
        return self.save()

    def action_reset(self):
        self.ensure_one()
        self.view_id.reset_customized_view(self.type_desc)
        return self.reload()


class ListCustomColumnHelperWizLine(models.TransientModel):
    _name = 'list.custom.column.helper.wiz.line'
    _order = 'sequence asc'

    wiz_id = fields.Many2one(
        comodel_name="list.custom.column.helper.wiz",
        string="Wizard",
        required=True,
        readonly=True,
    )
    field_name = fields.Char(
        string="Field name",
        readonly=True,
        required=True,
    )
    field_string = fields.Char(
        string="Field",
        readonly=True,
        required=True,
    )
    sequence = fields.Integer(
        string="Sequence",
    )
    added = fields.Boolean(
        string="On view?",
        default=False,
        readonly=True,
    )
    visible = fields.Boolean(
        string="Is visible?",
        default=False,
        readonly=True,
    )

    def action_toggle_visible(self):
        self.ensure_one()
        self.visible = not self.visible
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self.wiz_id._name,
            'type': 'ir.actions.act_window',
            'res_id': self.wiz_id.id,
            'context': self._context.copy(),
            'target': 'new',
        }

    def action_toggle_added(self):
        self.ensure_one()
        self.added = not self.added
        if self.added:
            self.sequence = (
                self.wiz_id.line_ids.filtered(
                    lambda l: l.added
                )[-2].sequence + 1
            )
        else:
            self.sequence = 1000
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self.wiz_id._name,
            'type': 'ir.actions.act_window',
            'res_id': self.wiz_id.id,
            'context': self._context.copy(),
            'target': 'new',
        }
