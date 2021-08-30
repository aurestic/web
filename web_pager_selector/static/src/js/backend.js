odoo.define('web_pager_selector.backend', function (require) {

    const Pager = require('web.Pager');

    const PAGER_LEVEL = ['1-10', '1-30', '1-50', '1-80', '1-200', '1-2000'];

    Pager.include({
        _edit: function () {
            var self = this;
            const $input = $('<select>', { class: 'o_input' });
            _.each(PAGER_LEVEL, function (level) {
                level.split('-')[1]
                if (parseInt(level.split('-')[1]) < parseInt(self.$limit.text())) {
                    const $option = $('<option>', { value: level }).html(level);
                    $input.append($option);
                }
            });
            // Add All
            var all_objects = '1-' + self.$limit.text()
            const $option = $('<option>', { value: all_objects }).html(all_objects);
            $input.append($option)
            $input.val(this.$value.html());

            this.$value.html($input);
            $input.focus();

            // Event handlers
            $input.click(function (ev) {
                ev.stopPropagation(); // ignore clicks on the input
            });
            $input.blur(function (ev) {
                self._render(); // save the state when leaving the input
            });
            $input.change(function (ev) {
                self._save($(ev.target)); // save the state when leaving the input
            });
            $input.on('keydown', function (ev) {
                ev.stopPropagation();
                if (ev.which === $.ui.keyCode.ENTER) {
                    self._save($(ev.target)); // save on enter
                } else if (ev.which === $.ui.keyCode.ESCAPE) {
                    self._render(); // leave on escape
                }
            });
        },
    });

});
