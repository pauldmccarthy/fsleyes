#!/usr/bin/env python
#
# __init__.py - Manage interactions between the FSLeyes FileTreePanel and
#               the filetree library.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``fsleyes.filetree`` package manages interactions between the FSLeyes
:class:`.FileTreePanel` and the ``file-tree`` library.

Two versions of ``file-tree`` exist:

  - The ``fsl.utils.filetree`` package, part of the ``fslpy`` library. This
    package is deprecated, and will be removed in future versions of ``fslpy``.
  - The `file-tree <https://git.fmrib.ox.ac.uk/ndcn0236/file-tree/>`_ library.

FSLeyes should work with either version. If the ``file-tree`` library is
installed, it will be used.
"""


from fsleyes.filetree.manager import FileTreeManager
from fsleyes.filetree.query   import FileTreeQuery


def list_all_trees():
    """Returns a list containing the names of all known ``.tree`` files. """

    # new file-tree
    try:
        import file_tree.parse_tree as parse_tree
        return parse_tree.search_tree('*')

    # deprecated fsl.utils.filetre
    except ImportError:
        import fsl.utils.filetree as filetree
        return filetree.list_all_trees()


def read(treefile, directory):
    """Load a ``.tree`` file, and return a ``FileTree``. """
    # new file-tree
    try:
        import file_tree
        return file_tree.FileTree.read(treefile, top_level=directory)

    # deprecated fsl.utils.filetree
    except ImportError:
        import fsl.utils.filetree as file_tree
        return file_tree.FileTree.read(treefile, directory=directory)
