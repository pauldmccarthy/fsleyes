c.ContentsManager.untitled_notebook     = 'FSLeyes_notebook'
c.Session.key                           = b''
c.NotebookApp.port                      = {{ fsleyes_nbserver_port }}
c.NotebookApp.port_retries              = 50
c.NotebookApp.token                     = '{{ fsleyes_nbserver_token }}'
c.NotebookApp.password                  = ''
c.NotebookApp.notebook_dir              = '{{ fsleyes_nbserver_dir }}'
c.NotebookApp.extra_static_paths        = ['{{ fsleyes_nbserver_static_dir }}']
c.NotebookApp.answer_yes                = True
c.NotebookApp.extra_nbextensions_path   = ['{{ fsleyes_nbextension_dir }}']
c.NotebookApp.open_browser              = {{ fsleyes_nbserver_open_browser }}
c.NotebookApp.kernel_manager_class      = 'fsleyes.actions.notebook.FSLeyesNotebookKernelManager'

# inject our kernel connection
# file into the kernel manager
from fsleyes.actions.notebook import FSLeyesNotebookKernelManager
FSLeyesNotebookKernelManager.connfile = '{{ fsleyes_kernel_connfile }}'
