#!/usr/bin/env python
#
# fsleyes_kernelspecmanager.py - Custom Jupyter notebook kernel spec manager.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            sys

from jupyter_client.kernelspec import KernelSpecManager

from fsl.utils.platform import platform as fslplatform


class FSLeyesKernelSpecManager(KernelSpecManager):
    """Custom jupyer ``KernelSpecManager`` which ensures that kernels can be
    instantiated from frozen versions of FSLeyes.
    """

    def get_kernel_spec(self, kernel_name):
        """If running frozen, patches the kernel launcher command line
        arguments to redirect to the frozen FSLeyes entry point (see
        :func:`fsleyes.actions.notebook.nbmain`).
        """

        spec = super(FSLeyesKernelSpecManager, self).get_kernel_spec(
            kernel_name)

        if not fslplatform.frozen:
            return spec

        exe = op.join(op.dirname(sys.executable), 'fsleyes')

        # replace [executable, '-m', 'ipykernel_launcher']
        spec.argv = [exe, 'notebook', 'kernel'] + spec.argv[3:]

        return spec
