#!/usr/bin/env python
#
# fsleyes_kernelmanager.py - Custom Jupyter notebook kernel manager.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from tornado import gen

from notebook.services.kernels.kernelmanager import MappingKernelManager


class FSLeyesNotebookKernelManager(MappingKernelManager):
    """Custom jupter ``MappingKernelManager`` which forces every notebook
    to connect to the embedded FSLeyes IPython kernel.

    See https://github.com/ebanner/extipy
    """


    connfile = ''
    """Path to the IPython kernel connection file that all notebooks should
    connect to.
    """

    def __init__(self, *args, **kwargs):
        super(FSLeyesNotebookKernelManager, self).__init__(*args, **kwargs)


    def __patch_connection(self, kernel):
        """Connects the given kernel to the IPython kernel specified by
        ``connfile``.
        """
        kernel.hb_port      = 0
        kernel.shell_port   = 0
        kernel.stdin_port   = 0
        kernel.iopub_port   = 0
        kernel.control_port = 0
        kernel.load_connection_file(self.connfile)


    @gen.coroutine
    def start_kernel(self, **kwargs):
        """Overrides ``MappingKernelManager.start_kernel``. Connects
        all new kernels to the IPython kernel specified by ``connfile``.
        """
        kid = super(FSLeyesNotebookKernelManager, self)\
                  .start_kernel(**kwargs).result()
        kernel = self._kernels[kid]
        self.__patch_connection(kernel)
        raise gen.Return(kid)


    def restart_kernel(self, *args, **kwargs):
        """Overrides ``MappingKernelManager.restart_kernel``. Does nothing. """
        pass
