#!/usr/bin/env python
#
# query.py - The FileTreeQuery class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Michiel Cottaar <michiel.cottaar@.ndcn.ox.ac.uk>
#
"""This module contains the :class:`FileTreeQuery` class, which can be used to
search for files in a directory described by a `FileTree
<https://git.fmrib.ox.ac.uk/ndcn0236/file-tree/>`_. A ``FileTreeQuery`` object
returns :class:`Match` objects which each represent a file that is described
by the ``FileTree``, and which is present in the directory.

The following utility functions, used by the ``FileTreeQuery`` class, are also
defined in this module:

.. autosummary::
   :nosignatures:

   scan
   allVariables
"""


import              logging
import              collections
import functools as ft

import os.path as op
from typing import Dict, List, Tuple

import numpy as np

from . import FileTree


log = logging.getLogger(__name__)


class FileTreeQuery(object):
    """The ``FileTreeQuery`` class uses a :class:`.FileTree` to search
    a directory for files which match a specific query.

    A ``FileTreeQuery`` scans the contents of a directory which is described
    by a :class:`.FileTree`, and identifies all file types (a.k.a. *templates*
    or *short names*) that are present, and the values of variables within each
    short name that are present. The :meth:`query` method can be used to
    retrieve files which match a specific template, and variable values.

    The :meth:`query` method returns a collection of :class:`Match` objects,
    each of which represents one file which matches the query.

    Example usage::

        >>> from fsl.utils.filetree import FileTree, FileTreeQuery

        >>> tree  = FileTree.read('bids_raw', './my_bids_data')
        >>> query = FileTreeQuery(tree)

        >>> query.axes('anat_image')
        ['acq', 'ext', 'modality', 'participant', 'rec', 'run_index',
         'session']

        >>> query.variables('anat_image')
        {'acq': [None],
         'ext': ['.nii.gz'],
         'modality': ['T1w', 'T2w'],
         'participant': ['01', '02', '03'],
         'rec': [None],
         'run_index': [None, '01', '02', '03'],
         'session': [None]}

        >>> query.query('anat_image', participant='01')
        [Match(./my_bids_data/sub-01/anat/sub-01_T1w.nii.gz),
         Match(./my_bids_data/sub-01/anat/sub-01_T2w.nii.gz)]


    Matches for templates contained within sub-trees are referred to by
    constructing a hierarchical path from the sub-tree template name(s),
    and the template name - see the :meth:`Match.full_name` method.
    """


    def __init__(self, tree):
        """Create a ``FileTreeQuery``. The contents of the tree directory are
        scanned via the :func:`scan` function, which may take some time for
        large data sets.

        :arg tree: The :class:`.FileTree` object
        """
        # Hard-code into the templates any pre-defined variables
        tree = tree.partial_fill()

        # Find all files present in the directory
        # (as Match objects), and find all variables,
        # plus their values, and all templates,
        # that are present in the directory.
        matches               = scan(tree)
        allvars, templatevars = allVariables(tree, matches)

        # Now we are going to build a series of ND
        # arrays to store Match objects. We create
        # one array for each template. Each axis
        # in an array corresponds to a variable
        # present in files of that template type,
        # and each position along an axis corresponds
        # to one value of that variable.
        #
        # These arrays will be used to store and
        # retrieve Match objects - given a template
        # and a set of variable values, we can
        # quickly find the corresponding Match
        # object (or objects).

        # matcharrays contains {template : ndarray}
        # mappings, and varidxs contains
        # {template : {varvalue : index}} mappings
        matcharrays = {}
        varidxs     = {}

        for template, tvars in templatevars.items():

            tvarlens = [len(allvars[v]) for v in tvars]

            # "Scalar" match objects - templates
            # which have no variables, and for
            # which zero or one file is present
            if len(tvarlens) == 0:
                tvarlens = 1

            # An ND array for this short
            # name. Each element is a
            # Match object, or nan.
            matcharray    = np.zeros(tvarlens, dtype=np.object)
            matcharray[:] = np.nan

            # indices into the match array
            # for each variable value
            tvaridxs = {}
            for v in tvars:
                tvaridxs[v] = {n : i for i, n in enumerate(allvars[v])}

            matcharrays[template] = matcharray
            varidxs[    template] = tvaridxs

        # Populate the match arrays
        for match in matches:
            tvars    = templatevars[match.full_name]
            tvaridxs = varidxs[     match.full_name]
            tarr     = matcharrays[ match.full_name]
            idx      = []

            if len(match.variables) == 0:
                idx = [0]
            else:
                for var in tvars:
                    val = match.variables[var]
                    idx.append(tvaridxs[var][val])

            tarr[tuple(idx)] = match

        self.__tree          = tree
        self.__allvars       = allvars
        self.__templatevars  = templatevars
        self.__matches       = matches
        self.__matcharrays   = matcharrays
        self.__varidxs       = varidxs


    def axes(self, template) -> List[str]:
        """Returns a list containing the names of variables present in files
        of the given ``template`` type, in the same order of the axes of
        :class:`Match` arrays that are returned by the :meth:`query` method.
        """
        return self.__templatevars[template]


    def variables(self, template=None) -> Dict[str, List]:
        """Return a dict of ``{variable : [values]}`` mappings.
        This dict describes all variables and their possible values in
        the tree.

        If a ``template`` is specified, only variables which are present in
        files of that ``template`` type are returned.
        """
        if template is None:
            return {var : list(vals) for var, vals in self.__allvars.items()}
        else:
            varnames = self.__templatevars[template]
            return {var : list(self.__allvars[var]) for var in varnames}


    @property
    def tree(self):
        """Returns the :class:`.FileTree` associated with this
        ``FileTreeQuery``.
        """
        return self.__tree


    @property
    def templates(self) -> List[str]:
        """Returns a list containing all templates of the ``FileTree`` that
        are present in the directory.
        """
        return list(self.__templatevars.keys())


    def query(self, template, asarray=False, **variables):
        """Search for files of the given ``template``, which match
        the specified ``variables``. All hits are returned for variables
        that are unspecified.

        :arg template: Template of files to search for.

        :arg asarray:  If ``True``, the relevant :class:`Match` objects are
                       returned in a in a ND ``numpy.array`` where each
                       dimension corresponds to a variable for the
                       ``templates`` in question (as returned by
                       :meth:`axes`). Otherwise (the default), they are
                       returned in a list.

        All other arguments are assumed to be ``variable=value`` pairs,
        used to restrict which matches are returned. All values are returned
        for variables that are not specified, or variables which are given a
        value of ``'*'``.

        :returns: A list  of ``Match`` objects, (or a ``numpy.array`` if
                  ``asarray=True``).
        """

        varnames    = list(variables.keys())
        allvarnames = self.__templatevars[template]
        varidxs     = self.__varidxs[     template]
        matcharray  = self.__matcharrays[ template]
        slc         = []

        for var in allvarnames:

            if var in varnames: val = variables[var]
            else:               val = '*'

            # We're using np.newaxis to retain
            # the full dimensionality of the
            # array, so that the axis labels
            # returned by the axes() method
            # are valid.
            if val == '*': slc.append(slice(None))
            else:          slc.extend([np.newaxis, varidxs[var][val]])

        result = matcharray[tuple(slc)]

        if asarray: return result
        else:       return [m for m in result.flat if isinstance(m, Match)]


@ft.total_ordering
class Match(object):
    """A ``Match`` object represents a file with a name matching a template in
    a ``FileTree``.  The :func:`scan` function and :meth:`FileTree.query`
    method both return ``Match`` objects.
    """


    def __init__(self, filename, template, tree, variables):
        """Create a ``Match`` object. All arguments are added as attributes.

        :arg filename:   name of existing file
        :arg template:   template identifier
        :arg tree:       :class:`.FileTree` which contains this ``Match``
        :arg variables:  Dictionary of ``{variable : value}`` mappings
                         containing all variables present in the file name.
        """
        self.__filename   = filename
        self.__template   = template
        self.__tree       = tree
        self.__variables  = dict(variables)


    @property
    def filename(self):
        return self.__filename


    @property
    def template(self):
        return self.__template


    @property
    def full_name(self):
        """The ``full_name`` of a ``Match`` is a combination of the
        ``template`` (i.e. the matched template), and the name(s) of
        the relevant ``FileTree`` objects.

        It allows one to unamiguously identify the location of a ``Match``
        in a ``FileTree`` hierarchy, where the same ``short_name`` may be
        used in different sub-trees.
        """

        def parents(tree):
            if tree.parent is None:
                return []
            else:
                return [tree.parent] + parents(tree.parent)

        trees = [self.tree] + parents(self.tree)

        # Drop the root tree
        trees = list(reversed(trees))[1:]

        return '/'.join([t.name for t in trees] + [self.template])


    @property
    def tree(self):
        return self.__tree


    @property
    def variables(self):
        return dict(self.__variables)


    def __eq__(self, other):
        return (isinstance(other, Match)            and
                self.filename   == other.filename   and
                self.template   == other.template   and
                self.tree       is other.tree       and
                self.variables  == other.variables)


    def __lt__(self, other):
        return isinstance(other, Match) and self.filename < other.filename


    def __repr__(self):
        """Returns a string representation of this ``Match``. """
        return 'Match({}: {})'.format(self.full_name, self.filename)


    def __str__(self):
        """Returns a string representation of this ``Match``. """
        return repr(self)


def scan(tree : FileTree) -> List[Match]:
    """Scans the directory of the given ``FileTree`` to find all files which
    match a tree template.

    :arg tree: :class:`.FileTree` to scan
    :returns:  list of :class:`Match` objects
    """

    matches = []
    for template in tree.templates:

        for variables in tree.get_all_vars(template, glob_vars='all'):

            filename = tree.update(**variables).get(template)

            if not op.isfile(filename):
                continue

            matches.append(Match(filename, template, tree, variables))

    for tree_name, sub_tree in tree.sub_trees.items():
        matches.extend(scan(sub_tree))

    return matches


def allVariables(
        tree    : FileTree,
        matches : List[Match]) -> Tuple[Dict[str, List], Dict[str, List]]:
    """Identifies the ``FileTree`` variables which are actually represented
    in files in the directory.

    :arg filetree: The ``FileTree`` object
    :arg matches:  list of ``Match`` objects (e.g. as returned by :func:`scan`)

    :returns: a tuple containing two dicts:

               - A dict of ``{ variable : [values] }`` mappings containing all
                 variables and their possible values present in the given list
                 of ``Match`` objects.

               - A dict of ``{ full_name : [variables] }`` mappings,
                 containing the variables which are relevant to each template.
    """
    allvars      = collections.defaultdict(set)
    alltemplates = {}

    for m in matches:

        if m.full_name not in alltemplates:
            alltemplates[m.full_name] = set()

        for var, val in m.variables.items():
            allvars[     var]        .add(val)
            alltemplates[m.full_name].add(var)

    # allow us to compare None with strings
    def key(v):
        if v is None: return ''
        else:         return v

    allvars      = {var : list(sorted(vals, key=key))
                    for var, vals in allvars.items()}
    alltemplates = {tn  : list(sorted(vars))
                    for tn, vars in alltemplates.items()}

    return allvars, alltemplates
