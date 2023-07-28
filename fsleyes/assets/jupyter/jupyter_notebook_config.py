c.ContentsManager.untitled_notebook   = 'FSLeyes_notebook'
c.Session.key                         = b''
c.ServerApp.port                      = {{ fsleyes_nbserver_port }}
c.ServerApp.port_retries              = 50
c.ServerApp.token                     = '{{ fsleyes_nbserver_token }}'
c.ServerApp.password                  = ''
c.ServerApp.root_dir                  = '{{ fsleyes_nbserver_dir }}'
c.ServerApp.extra_static_paths        = ['{{ fsleyes_nbserver_static_dir }}']
c.ServerApp.answer_yes                = True
c.NotebookApp.extra_nbextensions_path = ['{{ fsleyes_nbextension_dir }}']
c.NotebookApp.open_browser            = {{ fsleyes_nbserver_open_browser }}
c.ServerApp.kernel_manager_class      = 'fsleyes.actions.notebook.FSLeyesNotebookKernelManager'

# Allow additional configuration to be injected
# from environment - used for unit tests (see
# .ci/test_template.sh)
{{ os.environ.get('FSLEYES_EXTRA_JUPYTER_CONFIG', '') }}

# inject our kernel connection
# file into the kernel manager
from fsleyes.actions.notebook import FSLeyesNotebookKernelManager
FSLeyesNotebookKernelManager.connfile = '{{ fsleyes_kernel_connfile }}'
