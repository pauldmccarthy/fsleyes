define([ 'base/js/namespace'], function(Jupyter) {

    var intro = "{{ fsleyes_md_intro  }}";
    var init  = "{{ fsleyes_code_init }}";

    function load_ipython_extension() {
        if (Jupyter.notebook.get_cells().length === 1) {
            Jupyter.notebook.insert_cell_above('code',     0).set_text(init);
            Jupyter.notebook.insert_cell_above('markdown', 0).set_text(intro);
        }
    }
    return {
        load_ipython_extension: load_ipython_extension
    };
});
