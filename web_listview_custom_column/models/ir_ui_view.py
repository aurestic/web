
from lxml import etree

from odoo import _, api, models, tools


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    def reset_customized_view(self, type_desc):
        customized_view = self.env.ref(
            self._custom_column_xmlid(type_desc), raise_if_not_found=False
        ) or self.browse([])
        customized_view.unlink()

    @api.model
    def __set_visibility(self, visible, xml_field):
        if not visible:
            xml_field.attrib['invisible'] = '1'
        else:
            xml_field.attrib['invisible'] = '0'

    def custom_column(self, type_desc, fields_datas):
        # print(etree.tostring(tree, pretty_print=True))
        self.ensure_one()
        tree = etree.fromstring(self.read_combined()['arch'])
        customized_view = self.env.ref(
            self._custom_column_xmlid(type_desc), raise_if_not_found=False
        ) or self.browse([])

        fields_names = list(
            map(
                lambda fd: fd.get('field_name'),
                fields_datas
            )
        )
        tree_fields = list(
            map(
                lambda xf: xf.attrib.get("name"),
                tree.iter('field'),
            )
        )
        # new fields
        for field_name in fields_names:
            if field_name not in tree_fields:
                etree.SubElement(tree, 'field', {'name': field_name})

        deleted_tree_fields = list(
            filter(
                lambda xf: xf.attrib.get("name") not in fields_names,
                tree.iter('field')
            )
        )
        # deleteds fields
        for deleted_tree_field in deleted_tree_fields:
            tree.remove(deleted_tree_field)

        # position fields
        for index in range(len(tree.findall('field'))):
            xml_field = tree.findall('field')[index]
            try:
                sequence = fields_names.index(xml_field.attrib.get("name"))
                if index != sequence:
                    other_xml_field = list(tree.iter('field'))[sequence]
                    tree.remove(other_xml_field)
                    tree.insert(index, other_xml_field)
                    self.__set_visibility(
                        fields_datas[index].get('visible'), other_xml_field
                    )
                    tree.remove(xml_field)
                    tree.insert(sequence, xml_field)
                    self.__set_visibility(
                        fields_datas[sequence].get('visible'), xml_field
                    )
                    continue
                self.__set_visibility(
                    fields_datas[index].get('visible'), xml_field
                )
            except ValueError:
                tree.remove(xml_field)

        replacement = etree.Element('tree', {'position': 'replace'})
        replacement.append(tree)
        arch = etree.tostring(replacement, pretty_print=True)
        if customized_view:
            customized_view.write({'arch': arch})
        else:
            customized_view = self._custom_column_create_view(type_desc, arch)

    def custom_column_desc(self):
        """Return metadata necessary for UI"""
        self.ensure_one()
        return {
            'fields': self.env[self.model].fields_get(),
            'type': bool(self.env.ref(
                self._custom_column_xmlid('user'),
                raise_if_not_found=False
            )) and 'user' or bool(self.env.ref(
                self._custom_column_xmlid('all'),
                raise_if_not_found=False
            )) and 'all' or 'user',
        }

    def _custom_column_xmlid(self, customization_type, qualify=True):
        """Return an xmlid for the view of a type of customization"""
        self.ensure_one()
        return '%scustom_view_%d_%s%s' % (
            qualify and 'web_listview_custom_column.' or '',
            self.id,
            customization_type,
            '_%d' % self.env.uid if customization_type == 'user' else '',
        )

    def _custom_column_create_view(self, type_desc, arch):
        """Actually create a view for customization"""
        self.ensure_one()
        values = self.copy_data(default={
            'name': _('%s customized') % self.name,
            'arch': arch,
            'inherit_id': self.id,
            'mode': 'extension',
            'priority': 10000 + (type_desc == 'user' and 1 or 0),
            'user_ids': [(4, self.env.uid)] if type_desc == 'user' else [],
        })[0]
        result = self.create(values)
        self.env['ir.model.data'].create({
            'name': self._custom_column_xmlid(type_desc, qualify=False),
            'module': 'web_listview_custom_column',
            'model': self._name,
            'res_id': result.id,
            'noupdate': True,
        })
        return result

    @api.constrains('arch')
    def _constrain_xml(self):
        """Don't validate our custom views, this will break in init mode"""
        if self.env.registry._init:
            self = self.filtered(
                lambda x: not x.xml_id or not x.xml_id.startswith(
                    'web_listview_custom_column.custom_view_'
                )
            )
        return super(IrUiView, self)._check_xml()

    @api.model
    def get_inheriting_views_arch(self, view_id, model):
        """Don't apply our view inheritance in init mode for the same reason"""
        return [
            (arch, view_id_)
            for arch, view_id_ in
            super(IrUiView, self).get_inheriting_views_arch(view_id, model)
            if (not self.env.registry._init or tools.config['test_enable']) or
            not self.sudo().browse(view_id_).xml_id or
            not self.sudo().browse(view_id_).xml_id.startswith(
                'web_listview_custom_column.custom_view_'
            )
        ]

    @api.multi
    def get_field_sequence_in_view(self, field_name):
        self.ensure_one()
        tree = etree.fromstring(self.read_combined()['arch'])
        visible = True
        for sequence, field in enumerate(tree.findall("field")):
            if field_name == field.attrib.get("name"):
                visible = field.attrib.get("invisible", '0') == '0'
                break
        else:
            sequence = -1
        return sequence, visible
