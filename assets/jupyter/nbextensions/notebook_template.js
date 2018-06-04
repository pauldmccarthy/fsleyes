define([ 'base/js/namespace'], function(Jupyter) {

    var intro = "{{ intro     }}".trim();
    var init  = "{{ init_code }}".trim();

    function load_ipython_extension() {
        if (Jupyter.notebook.get_cells().length === 1) {

            if (init.length > 0) {
                Jupyter.notebook.insert_cell_above('code',     0).set_text(init);
            }

            if (intro.length > 0) {
                var cell = Jupyter.notebook.insert_cell_above('markdown', 0);
                cell.set_text(intro)
                cell.render();
            }
        }
    }
    return {
        load_ipython_extension: load_ipython_extension
    };
});
