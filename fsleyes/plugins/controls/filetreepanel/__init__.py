#!/usr/bin/env python
#
# __init__.py - Manage interactions between the FSLeyes FileTreePanel and
#               the filetree library.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``fsleyes.filetree`` package manages interactions between the FSLeyes
:class:`.FileTreePanel` and the `file-tree
<https://git.fmrib.ox.ac.uk/ndcn0236/file-tree/>`_ library.
"""


import os.path as op
import            glob

import file_tree

from .filetreepanel import FileTreePanel
from .manager       import FileTreeManager
from .query         import FileTreeQuery


def list_all_trees():
    """Returns a list containing the names of all known ``.tree`` files. """

    file_tree.parse_tree.scan_plugins()

    treefiles = []

    for directory in file_tree.tree_directories:
        treefiles.extend(glob.glob(op.join(directory, '*.tree')))

    for subtree in file_tree.parse_tree.available_subtrees.keys():
        treefiles.append(subtree)

    return treefiles


def read(treefile, directory):
    """Load a ``.tree`` file, and return a ``FileTree``. """
    return file_tree.FileTree.read(treefile, top_level=directory)
