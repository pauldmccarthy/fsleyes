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
"""


import              logging
import              collections
import functools as ft

import numpy     as np


log = logging.getLogger(__name__)


class FileTreeQuery:
    """The ``FileTreeQuery`` class uses a ``FileTree`` to search
    a directory for files which match a specific query.

    A ``FileTreeQuery`` scans the contents of a directory which is described
    by a ``FileTree``, and identifies all file types (a.k.a. *templates*
    or *short names*) that are present, and the values of variables within each
    short name that are present. The :meth:`query` method can be used to
    retrieve files which match a specific template, and variable values.

    The :meth:`query` method returns a collection of :class:`Match` objects,
    each of which represents one file which matches the query.

    Example usage::

        >>> from file_tree import FileTree
        >>> from fsleyes.filetree import FileTreeQuery

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

        :arg tree: The ``FileTree`` object
        """
        self.__tree        = tree
        self.__matcharrays = scan(tree)


    def axes(self, template):
        """Returns a list containing the names of variables present in files
        of the given ``template`` type.
        """
        return list(self.__matcharrays[template].coords.keys())


    def variables(self, template=None):
        """Return a dict of ``{variable : [values]}`` mappings.
        This dict describes all variables and their possible values in
        the tree.

        If a ``template`` is specified, only variables which are present in
        files of that ``template`` type are returned.
        """
        if template is not None:
            templates = [template]
        else:
            templates = self.__matcharrays.keys()

        variables = collections.defaultdict(set)

        for template in templates:
            coords = self.__matcharrays[template].coords

            for axis in coords.keys():
                varvalues       = variables[axis]
                variables[axis] = varvalues.union(set(coords[axis].data))

        # Variable values will usually be strings,
        # but can sometimes be None, so we convert
        # to str to handle this.
        variables = {name : sorted(vals, key=str)
                     for name, vals in variables.items()}

        return variables


    @property
    def tree(self):
        """Returns the ``FileTree`` associated with this ``FileTreeQuery``.
        """
        return self.__tree


    @property
    def templates(self):
        """Returns a list containing all templates of the ``FileTree`` that
        are present in the directory.
        """
        return list(self.__matcharrays.keys())


    def matcharray(self, template):
        """Returns a reference to the ``xarray.DataArray`` which contains the
        file paths for the given ``template``.
        """
        return self.__matcharrays[template]


    def query(self, template, **variables):
        """Search for files of the given ``template``, which match
        the specified ``variables``. All hits are returned for variables
        that are unspecified.

        :arg template: Template of files to search for.

        All other arguments are assumed to be ``variable=value`` pairs,
        used to restrict which matches are returned. All values are returned
        for variables that are not specified, or variables which are given a
        value of ``'*'``.

        :returns: A list  of ``Match`` objects
        """

        # Build a slice containing a value for
        # every axis of the template array
        varnames    = list(variables.keys())
        allvarnames = self.variables(template).keys()
        matcharray  = self.__matcharrays[ template]
        slc         = []

        for var in allvarnames:

            if var in varnames: val = variables[var]
            else:               val = '*'

            if val == '*': slc.append(slice(None))
            else:          slc.append(val)

        # Retrieve the results
        results = matcharray.loc[tuple(slc)]

        # Convert xarray.DataArray into a list of
        # Match objects. I can't find an elegant
        # way to do this - something like apply_ufunc
        # would be nice, but we lose the labelling
        # information.
        matches = []
        riter   = np.nditer(results, flags=['multi_index'])

        for fname in riter:

            fname = fname.item()

            if fname == '':
                continue

            # Look up the variable values associated
            # with this file name, and create a
            # corresponding Match object
            index  = riter.multi_index
            coords = results[index].coords
            rvars  = {ax : coords[ax].data[()] for ax in coords}

            matches.append(Match(fname, template, rvars))

        return matches


@ft.total_ordering
class Match:
    """A ``Match`` object represents a file with a name matching a template in
    a ``FileTree``.  The :meth:`FileTree.query` method returns ``Match``
    objects.
    """


    def __init__(self, filename, template, variables):
        """Create a ``Match`` object. All arguments are added as attributes.

        :arg template:   template identifier
        :arg value:

        """
        self.__filename  = filename
        self.__template  = template
        self.__variables = variables


    @property
    def filename(self):
        return self.__filename


    @property
    def template(self):
        return self.__template


    @property
    def variables(self):
        return dict(self.__variables)


    def __eq__(self, other):
        return (isinstance(other, Match)            and
                self.filename   == other.filename   and
                self.template   == other.template   and
                self.variables  == other.variables)


    def __lt__(self, other):
        return isinstance(other, Match) and self.filename < other.filename


    def __repr__(self):
        """Returns a string representation of this ``Match``. """
        return 'Match({}: {})'.format(self.template, self.filename)


    def __str__(self):
        """Returns a string representation of this ``Match``. """
        return repr(self)


def scan(tree, filterEmpty=True):
    """Scans the directory of the given ``FileTree`` to find all files which
    match a tree template.

    A dictionary of ``{template : xarray.DataArray}`` mappings is returned,
    where each ``DataArray`` has dimensions corresponding to variables used in
    the template, and contains names (as strings) of matching files present on
    disk as strings. Entries in an arrays for variable values which do not
    exist on disk are set to the empty string.

    See the ``file_tree.FileTree.get_mult_glob`` method for more details.

    :arg tree:        ``FileTree`` to scan

    :arg filterEmpty: If ``True`` (the default), file tree templates which
                      do not match any files on disk are not returned.

    :returns:         A dict of ``{template : xarray.DataArray}`` objects,
                      one for each template.
    """

    templates = tree.template_keys(only_leaves=True)
    xarrays   = tree.get_mult_glob(templates)
    results   = {}

    for template in templates:

        xa = xarrays[template]

        # Skip templates which do not have
        # any files present on disk
        if filterEmpty:
            if (xa == '').sum() == np.prod(xa.shape):
                continue

        results[template] = xa

    return results
