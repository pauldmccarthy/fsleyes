#!/usr/bin/env python
#
# manager.py - Functions and classes used by the FileTreePanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains the :class:`FileTreeManager`, which is used by the
:class:`.FileTreePanel`. It also contains the :class:`OverlayManager`, which
is used by the ``FileTreeManager``.


Overview
--------


The :class:`.FileTreePanel` allows the user to navigate structured
directories, where the files and sub-directories are named according to a
`FileTree <https://git.fmrib.ox.ac.uk/ndcn0236/file-tree/>`_
specification. The ``FileTreePanel`` allows the user to select which file
types to display, and to restrict or re-order the files with file tree
variables.


By default, the :class:`.FileTreePanel` will display a list containing one row
for every combination of variable values; each row will contain all files for
(the selected file types) which correspond to that combination of variables.
The user may also choose to display ``<all>`` values of a specific variable on
a single row.


This module handles the mechanics of generating lists of variables and files
according to the user's settings.


In this module, and in the :mod:`.filetreepanel` module, variables which take
on a different value for each row are referred to as *varying*, and variables
for which all possible values are displaed on one row are referred to as
*fixed*.


Example
-------


For example, imagine that we have a data set with data for multiple subjects
(``sub``) and sessions (``ses``), described by this file tree::

    subj-{participant}
      [ses-{session}]
        T1w.nii.gz (T1w)
        {hemi}.gii (surface)

So for one subject and one session, we might have the following files::

    T1.nii.gz
    L.gii
    R.gii

So we have two files types (``T1`` and ``surface``), and three variables
(``sub``, ``ses``, and ``hemi``).  By default, all variables are *varying*, so
the ``FileTreePanel`` will display this data set like so (the ``x`` indicates
whether or not each file is present):


======= ======= ========= ======  ===========
``sub`` ``ses`` ``hemi``  ``T1``  ``surface``
------- ------- --------- ------  -----------
``1``   ``1``   ``L``     ``x``   ``x``
``1``   ``1``   ``R``     ``x``   ``x``
``1``   ``2``   ``L``     ``x``   ``x``
``1``   ``2``   ``R``     ``x``   ``x``
``2``   ``1``   ``L``     ``x``   ``x``
``2``   ``1``   ``R``     ``x``   ``x``
``2``   ``2``   ``L``     ``x``   ``x``
``2``   ``2``   ``R``     ``x``   ``x``
======= ======= ========= ======  ===========


However, it may make more sense to display all of the surface files together.
The user can do this by setting the ``hemi`` variable to ``<all>``, thus
changing it to a *fixed* variable. This will cause the :class:`.FileTreePanel`
to re-arrange the grid like so:


======= ======= ====== =================== ===================
``sub`` ``ses`` ``T1`` ``surface[hemi=L]`` ``surface[hemi=R]``
------- ------- ------ ------------------- -------------------
``1``   ``1``   ``x``  ``x``               ``x``
``1``   ``2``   ``x``  ``x``               ``x``
``2``   ``1``   ``x``  ``x``               ``x``
``2``   ``2``   ``x``  ``x``               ``x``
======= ======= ====== =================== ===================
"""


import                    collections
import                    logging
import functools       as ft
import itertools       as it

import fsl.utils.cache                 as cache
import fsleyes_widgets.utils.typedict  as td
import fsleyes.actions.loadoverlay     as loadoverlay


log = logging.getLogger(__name__)


FILETREE_PREFIX = '[filetree] '
"""This is a prefix added to the name of every overlay which is added to the
:class:`.OverlayList` by this module.
"""


class FileGroup(object):
    """A ``FileGroup`` represents a single row in the file tree panel list.  It
    encapsulates a set of values for all varying variables, and a set of files
    and their associated fixed variable values. These are all accessible as
    attributes called ``varyings``, ``files``, and ``fixedvars``.

    Another attribute, ``fileIDs``, contains a unique ID for each file within
    one ``FileGroup``. This ID can be used to pair up files from different
    ``FileGroup`` objects.
    """


    def __init__(self, varyings, fixed, ftypes, files):
        """Create a ``FileGroup``.

        :arg varyings: Dict of ``{ var : val }`` mappings containing the
                       varying variable values.

        :arg fixed:    List containing ``{ var : val }`` mappings, each
                       containing the fixed variable values for each file.

        :arg ftypes:   List containing the file type for each file.

        :arg files:    List of file names, the same length as ``fixedvars``.
                       Missing files are represented as ``None``.
        """

        self.varyings = varyings
        self.fixed    = fixed
        self.ftypes   = ftypes
        self.files    = files
        self.fileIDs  = []

        # Generate an ID which uniquely identifies
        # each overlay by file type and fixed
        # variable values (i.e. a unique ID for each
        # row . This will be used as
        # the overlay name
        for fname, ftype, v in zip(files, ftypes, fixed):

            # The FileGroup may contain
            # non-existent files, and
            # we don't want to load files
            # that are already in the
            # overlay list
            if fname is None:
                self.fileIDs.append(None)
                continue

            if len(v) == 0:
                fid = ftype
            else:
                fid = ftype + '[' + ','.join(
                    ['{}={}'.format(var, val)
                     for var, val in sorted(v.items())]) + ']'

            self.fileIDs.append(fid)


    def __str__(self):
        """Return a string representation of this ``FileGroup``. """
        return 'FileGroup({}, {}, {}, {})'.format(self.varyings,
                                                  self.fixed,
                                                  self.ftypes,
                                                  self.files)


    def __repr__(self):
        """Return a string representation of this ``FileGroup``. """
        return str(self)


    def __eq__(self, other):
        """Return ``True`` if this ``FileGroup`` is equal to ``other``. """
        return (self.varyings == other.varyings and
                self.fixed    == other.fixed    and
                self.ftypes   == other.ftypes   and
                self.files    == other.files)


class FileTreeManager(object):
    """The ``FileTreeManager`` class handles the generation and arranging
    of varying and fixed variables, and file types, according to a
    specification of *varying* and *fixed* variables.

    The ``FileTreeManager`` creates and uses an :class:`OverlayManager` which
    handles overlay display.
    """


    def __init__(self, overlayList, displayCtx, query):
        """Create a ``FileTreeManager``.

        :arg overlayList: The :class:`.OverlayList`

        :arg displayCtx:  The :class:`.DisplayContext` which is to manage
                          the file tree overlay display.

        :arg query:      :class:`.FileTreeQuery` instance
        """

        self.__query       = query
        self.__ovlmgr      = OverlayManager(overlayList, displayCtx)
        self.__ftypes      = None
        self.__varyings    = None
        self.__fixed       = None
        self.__varcols     = None
        self.__fixedcols   = None
        self.__filegroups  = None


    def destroy(self):
        """Must be called when this ``FileTreeManager`` is no longer needed.
        Destroys the :class:`OverlayManager` and clears references.
        """

        self.__ovlmgr.destroy()
        self.__query      = None
        self.__ovlmgr     = None
        self.__ftypes     = None
        self.__varyings   = None
        self.__fixed      = None
        self.__varcols    = None
        self.__fixedcols  = None
        self.__filegroups = None


    def update(self, ftypes, varyings, fixed):
        """Update the internal file tree grid information according to the
        given file types and variables.

        :arg ftypes:   List of file types that are to be displayed

        :arg varyings: Dict of ``{var : value}`` mappings defining the
                       varying variables.

        :arg fixed:    List of variable names defining the fixed variables.
        """

        query                 = self.query
        varyings              = prepareVaryings( query,  ftypes,   varyings)
        fixed                 = prepareFixed(    query,  ftypes,   fixed)
        varcols,    fixedcols = genColumns(      ftypes, varyings, fixed)
        filegroups            = genFileGroups(   query,  varyings, fixedcols)
        filegroups, fixedcols = filterFileGroups(filegroups,       fixedcols)

        self.__ovlmgr.update(filegroups)

        self.__ftypes     = ftypes
        self.__varyings   = varyings
        self.__fixed      = fixed
        self.__varcols    = varcols
        self.__fixedcols  = fixedcols
        self.__filegroups = filegroups


    def reorder(self, varcols):
        """Re-order the file groups according to the new varying variable
        order. The first varying variable is the slowest changing.

        :arg varcols: List of varying variable names.
        """

        if sorted(varcols) != sorted(self.varcols):
            raise ValueError('Invalid varying columns: {}'.format(varcols))

        filegroups = self.filegroups

        def cmp(g1, g2):

            g1 = filegroups[g1]
            g2 = filegroups[g2]

            for col in varcols:
                v1 = g1.varyings[col]
                v2 = g2.varyings[col]
                if   v1 == v2:   continue
                elif v1 is None: return  1
                elif v2 is None: return -1
                elif v1 > v2:    return  1
                elif v1 < v2:    return -1
            return 0

        idxs = list(range(len(filegroups)))
        idxs = sorted(idxs, key=ft.cmp_to_key(cmp))

        # Update the internal manager state
        # so the new order is preserved
        filegroups = [filegroups[i] for i in idxs]
        varyings   = collections.OrderedDict()
        varcols    = list(varcols)

        for v in varcols:
            varyings[v] = self.varyings[v]

        self.__ovlmgr.update(filegroups)

        self.__filegroups = filegroups
        self.__varyings   = varyings
        self.__varcols    = varcols


    def show(self, filegroup, callback=None):
        """Show the overlays associated with a :class:`FileGroup`.

        All arguments are passed through to the :meth:`OverlayManager.show` method.
        """
        self.__ovlmgr.show(filegroup, callback)


    @property
    def query(self):
        """Returns the :class:`.FileTreeQuery` object used by this
        ``FileTreeManager``.
        """
        return self.__query


    @property
    def ftypes(self):
        """Returns a list of all file types to be displayed. """
        return self.__ftypes


    @property
    def varyings(self):
        """Returns a dict of ``{ var : [value] }`` mappings, containing every
        possible value for each varying variable.
        """
        return self.__varyings


    @property
    def fixed(self):
        """Returns a dict of ``{ ftype : { var : [value] } }`` mappings which,
        for each file type, contains a dictionary of all fixed variables and
        their possible values.
        """
        return self.__fixed


    @property
    def varcols(self):
        """Returns a list of varying variable names to be used as columns for
        the varying variables.
        """
        return self.__varcols


    @property
    def fixedcols(self):
        """Returns a list of tuples, with each tuple containing:
          - A file type
          - A dict of ``{var : value}`` mappings, containing
            fixed variable values

        Each tuple represents a column for a combination of file type and
        fixed variable values.
        """
        return self.__fixedcols


    @property
    def filegroups(self):
        """Returns a list containing all of the ``FileGroup`` objects. Each
        ``FileGroup`` represents one row in the file tree grid.
        """
        return self.__filegroups


def prepareVaryings(query, ftypes, varyings):
    """Called by :meth:`FileTreeManager.update`. Prepares a dictionary which
    contains all possible values for each varying variable.

    :arg query:    :class:`.FileTreeQuery` object

    :arg ftypes:   List of file types to be displayed.

    :arg varyings: Dict of ``{ var : value }`` mappings. A value of ``'*'``
                   indicates that all possible values for this variable
                   should be used.

    :returns:      A dict of ``{ var : [value] }`` mappings, containing
                   every possible value for each varying variable.
    """

    allvars = query.variables()

    # Force a constsient ordering
    # of the varying variables
    _varyings = collections.OrderedDict()
    for var in sorted(varyings.keys()):
        _varyings[var] = varyings[var]
    varyings = _varyings

    # Expand the varying dict so that
    # it contains { var : [value] }
    # mappings - '*' is replaced with
    # a list of all possible values,
    # and a scalar value is replaced
    # with a list containing just that
    # value.
    for var, val in list(varyings.items()):

        # This variable is not relevant for
        # any of the specified file types.
        if not any([var in query.variables(ft) for ft in ftypes]):
            varyings.pop(var)
            continue

        elif val == '*': varyings[var] = allvars[var]
        else:            varyings[var] = [val]

    return varyings


def prepareFixed(query, ftypes, fixed):
    """Called by :meth:`.FileTreeManager.update`. Prepares a dictionary
    which contains all possible values for each fixed variable, and for
    each file type.

    :arg query:  :class:`.FileTreeQuery` object

    :arg ftypes: List of file types to be displayed

    :arg fixed:  List of fixed variables

    :returns:    A dict of ``{ ftype : { var : [value] } }`` mappings
                 which, for each file type, contains a dictionary of
                 all fixed variables and their possible values.
    """

    allvars = query.variables()

    # Create a dict for each file type
    # containing { var : [value] }
    # mappings for all fixed variables
    # which are relevant to that file
    # type.
    _fixed = {}
    for ftype in ftypes:
        ftvars        = query.variables(ftype)
        _fixed[ftype] = {}
        for var in fixed:
            if var in ftvars:
                _fixed[ftype][var] = allvars[var]
    fixed = _fixed

    return fixed


def genColumns(ftypes, varyings, fixed):
    """Determines all columns which need to be present in a file tree grid
    for the given file types, varying and fixed variables.

    :arg ftypes:   List of file types to be displayed

    :arg varyings: Dict of ``{ var : [value} }`` mappings, containing all
                   varying variables and their possible values (see
                   :func:`prepareVaryings`).

    :arg fixed:    Dict of ``{ ftype : { var : [value] } }`` mappings
                   which, for each file type, contains a dictionary of
                   all fixed variables and their possible values.

    :returns:      Two lists which, combined, represent all columns to be
                   displayed in the file tree grid:

                    - A list of varying variable names
                    - A list of tuples, with each tuple containing:

                      - A file type
                      - A dict of ``{var : value}`` mappings, containing
                        fixed variable values
    """

    varcols   = [var for var, vals in varyings.items() if len(vals) > 1]
    fixedcols = []

    for ftype in ftypes:

        ftvars    = fixed[ftype]
        ftvarprod = list(it.product(*[vals for vals in ftvars.values()]))

        for ftvals in ftvarprod:
            ftvals = {var : val for var, val in zip(ftvars, ftvals)}
            fixedcols.append((ftype, ftvals))

    return varcols, fixedcols


def genFileGroups(query, varyings, fixed):
    """Generates a list of :class:`FileGroup` objects, each representing one
    row in a grid defined by the given set of varying and fixed variables.

    :arg query:    :class:`.FileTreeQuery` object

    :arg varyings: Dict of ``{ var : [value} }`` mappings, containing all
                   varying variables and their possible values (see
                   :func:`prepareVaryings`).

    :arg fixed:    List of tuples of ``(ftype, { var : value })`` mappings,
                   which each contain a file type and set of fixed variables
                   corresponding to one column in the grid.

    :returns:      A list of ``FileGroup`` objects.
    """

    if len(varyings) == 0:
        return []

    # Build a list of file groups - each
    # file group represents a group of
    # files to be displayed together,
    # corresponding to a combination of
    # varying values
    filegroups = []

    # loop through all possible
    # combinations of varying values
    for vals in it.product(*varyings.values()):

        groupVars   = {var : val for var, val in zip(varyings.keys(), vals)}
        groupFtypes = []
        groupFixed  = []
        groupFiles  = []

        for ftype, ftvars in fixed:

            fname = query.query(ftype, **groupVars, **ftvars)

            # There should only be one file for
            # each combination of varying+fixed
            # values
            if len(fname) == 1: fname = fname[0].filename
            else:               fname = None

            groupFtypes.append(ftype)
            groupFixed .append(ftvars)
            groupFiles .append(fname)

        grp = FileGroup(groupVars, groupFixed, groupFtypes, groupFiles)
        filegroups.append(grp)

    return filegroups


def filterFileGroups(filegroups, fixedcols):
    """Filters out empty, duplicate and redundant rows, and empty columns,
    from ``filegroups``

    :arg filegroups: List of :class:`FileGroup` objects.
    :arg fixedcols:  List of ``(ftype, { var : value })`` mappings
    :returns:        A tuple containing the filtered ``filegroups`` and
                     ``fixedcols``
    """

    # TODO optimise this whole thing

    dropcols = set()

    # Remove duplicate/redundant rows
    for i in range(len(filegroups)):

        if i in dropcols:
            continue

        grpi   = filegroups[i]
        ifiles = [f for f in grpi.files if f is not None]

        # drop empty rows
        if len(ifiles) == 0:
            dropcols.add(i)
            continue

        for j in range(i + 1, len(filegroups)):

            if j in dropcols:
                continue

            grpj   = filegroups[j]
            jfiles = [f for f in grpj.files if f is not None]

            # Group i contains all the files
            # of group j - we can drop group j
            # (this will also cause j to be
            # dropped if it is empty)
            if all([n in ifiles for n in jfiles]):
                dropcols.add(j)

            # Group j contains all the files
            # in group i - we can drop group i
            elif all([n in jfiles for n in ifiles]):
                dropcols.add(i)
                break

    filegroups = [g for i, g in enumerate(filegroups) if i not in dropcols]

    # Count the number of present files in
    # each column, and drop empty columns
    if len(filegroups) > 0: ncolumns = len(filegroups[0].files)
    else:                   ncolumns = 0

    colcounts = {i : 0 for i in range(ncolumns)}
    for grp in filegroups:
        for i, fname in enumerate(grp.files):
            if fname is not None:
                colcounts[i] += 1

    keepcols = [idx for idx, count in colcounts.items() if count > 0]

    if len(keepcols) > 0 and len(keepcols) < ncolumns:
        fixedcols = [fixedcols[i] for i in keepcols]
        for grp in filegroups:
            grp.fileIDs = [grp.fileIDs[i] for i in keepcols]
            grp.files   = [grp.files[  i] for i in keepcols]
            grp.ftypes  = [grp.ftypes[ i] for i in keepcols]
            grp.fixed   = [grp.fixed[  i] for i in keepcols]

    return filegroups, fixedcols


class OverlayManager(object):
    """The ``OverlayManager`` is used by the :class:`FileTreeManager`. It
    manages the mechanics of displaying overlays associated with the file tree.

    The :meth:`update` method is used to tell the ``OverlayManager`` about the
    currently displayed list of :class:`FileGroup` objects. The :meth:`show`
    method is used to show the overlays in a specific ``FileGroup``.

    Whenever the :meth:`show` method is called, the overlays from any
    previously displayed ``FileGroup`` are "swapped" out for the overlays in
    the new ``FileGroup``. The display properties for matching pairs of
    overlays are preserved as best as possible.
    """


    def __init__(self, overlayList, displayCtx):
        """Create an ``OverlayManager``

        :arg overlayList: The :class:`.OverlayList`

        :arg displayCtx:  The :class:`.DisplayContext` which is to manage
                          the file tree overlay display.
        """

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx

        # Loaded overlays are cached to
        # reduce swap time if they are
        # re-shown.
        self.__cache = cache.Cache(maxsize=50, lru=True)

        # The current list of file
        # groups - set in update
        self.__filegroups = None

        # When we swap one group out
        # for another, we preserve
        # the overlay ordering.
        self.__order = None

        # When we swap one group out
        # for another, we preserve
        # overlay display/opts
        # property values.
        self.__propVals = None


    def destroy(self):
        """Must be called when this ``OverlayManager`` is no longer needed.
        Clears references.
        """
        self.__cache.clear()

        self.__overlayList = None
        self.__displayCtx  = None
        self.__cache       = None
        self.__filegroups  = None
        self.__order       = None
        self.__propVals    = None


    def update(self, filegroups):
        """Must be called when the list of ``FileGroup`` objects has changed,
        either due to them being re-ordered or completely changed.
        """
        self.__filegroups = filegroups
        self.__order      = []
        self.__propVals   = {}


    def show(self, filegroup, callback=None):
        """Show the overlays associated with the given :class:`FileGroup`.

        Any overlays which were previously displayed are removed, and replaced
        with the overlays associated with the new group.

        :arg filegroup: ``FileGroup`` to show
        :arg callback:  Optional function which will be called when the
                        overlays have been shown. Will not be called if no new
                        overlays are to be shown.
        """

        # Force an error if a file
        # group which is not in our
        # known list is passed in.
        self.__filegroups.index(filegroup)

        displayCtx = self.__displayCtx

        # Gather all of the files
        # to be loaded, using their
        # unique file ID (unique
        # within one file group)
        new = {}
        for fname, fid in zip(filegroup.files, filegroup.fileIDs):

            # The FileGroup may contain
            # non-existent files
            if fname is None:
                continue

            new[FILETREE_PREFIX + fid] = fname

        # Get refs to the existing
        # filetree overlays - we will
        # replace the existing ones
        # with the new ones.
        old = collections.OrderedDict()
        for ovl in displayCtx.getOrderedOverlays():
            if ovl.name.startswith(FILETREE_PREFIX):
                old[ovl.name] = ovl

        # Save the display settings
        # of the old overlays - we'll
        # apply them to the new ones
        for fid, ovl in old.items():
            propVals = self.__propVals.get(fid, {})
            propVals.update(getProperties(ovl, displayCtx))
            self.__propVals[fid] = propVals

        # Save the ordering of the old
        # overlays so we can preserve
        # it in the new overlays. The
        # length check is to take into
        # account missing files -
        # file groups with more present
        # files should take precedence
        # over file groups with more
        # missing files.
        if len(old) >= len(self.__order):
            self.__order = list(old.keys())

        # Set the ordering of the new
        # overlays based on the old ones
        order = self.__order
        fids  = [f for f in order if f     in new] + \
                [f for f in new   if f not in order]
        new   = collections.OrderedDict([(f, new[f]) for f in fids])

        if len(new) > 0:
            self.__load(new, old, callback)


    def __load(self, new, old, callback=None):
        """Called by :meth:`show`. Loads the files specified in ``new``, then
        passes them (along with the ``old``) to the :meth:`__show` method.

        :arg new:      Dict of ``{fileid : file}`` mappings, containing the
                       files to load.

        :arg old:      Dict of ``{fileid : overlay}`` mappings, containing the
                       existing overlays which will be replaced with the new
                       ones.

        :arg callback: No-args function which will be called after the new
                       overlays have been loaded.

        """

        # Remove any files that are
        # in the cache, and don't
        # need to be re-loaded
        cache     = self.__cache
        toload    = [(fid, f) for fid, f in new.items() if fid not in cache]
        loadfids  = [f[0] for f in toload]
        loadfiles = [f[1] for f in toload]

        def onLoad(ovlidxs, ovls):

            # Gather the overlays to be shown,
            # either from the ones that were
            # just loaded, or from the cache.
            toshow = collections.OrderedDict()

            for fid, fname in new.items():

                # Is this overlay in the cache?
                if fname in cache:
                    toshow[fid] = cache[fname]

                # Or has it just been loaded?
                else:
                    idx         = loadfids.index(fid)
                    toshow[fid] = ovls[idx]
                    cache.put(fname, ovls[idx])

            self.__show(toshow, old)

            if callback is not None:
                callback()

        loadoverlay.loadOverlays(loadfiles, onLoad=onLoad)


    def __show(self, new, old):
        """Adds the given ``new`` overlays to the :class:`.OverlayList`. The
        display properties of any ``old`` overlays with the same ID are copied
        over to the new ones.

        All existing overlays which were previously added are removed.
        """

        overlayList = self.__overlayList
        displayCtx  = self.__displayCtx

        # Drop old overlays that
        # are being (re-)addd
        old = collections.OrderedDict(
            [(fid, ovl) for fid, ovl in old.items()
             if ovl not in new.values()])

        # Drop new overlays that
        # are already in the list,
        # but keep a ref to the
        # original, in case any
        # properties refer to them
        allnew = new
        new    = collections.OrderedDict(
            [(fid, ovl) for fid, ovl in new.items()
             if ovl not in overlayList])

        for fid, ovl in new.items(): log.debug('Adding %s: %s', fid, ovl)
        for      ovl in old:         log.debug('Removing %s',   ovl)

        # We set the name of each new overlay
        # to its file ID. If the user changes
        # the overlay name, it will no longer
        # be tracked
        for fid, ovl in new.items():
            ovl.name = fid

        # Copy the display settings across from
        # the old overlays to the new ones. The
        # old ones were saved in the show method,
        # but we need to rearrange them a little
        # before passing them to the overlayList.
        propVals = collections.defaultdict(dict)

        for fid, ovl in new.items():
            for name, val in self.__propVals.get(fid, {}).items():

                # If the value is a ToReplace
                # object, it has has been
                # REPLACEd by the getProperties
                # function - see REPLACE and
                # getProperties.
                if isinstance(val, ToReplace):
                    if val.value in allnew: val = allnew[val.value]
                    else:                   val = None

                propVals[name][ovl] = val

        # remove the old overlays from any
        # overlay groups, otherwise property
        # syncing might screw things up
        old = list(old.values())
        for ovl in old:
            for group in displayCtx.overlayGroups:
                group.removeOverlay(ovl)

        # Insert the new overlays into the list.
        overlayList.extend(new.values(), **propVals)

        # preserve the display space if
        # it was set to a filegroup image
        dspace = displayCtx.displaySpace
        if dspace in old and dspace.name in new:
            displayCtx.displaySpace = new[dspace.name]

        # Remove all of the
        # old filetree overlays
        idxs           = range(len(overlayList))
        idxs           = [i for i in idxs if overlayList[i] not in old]
        overlayList[:] = [overlayList[i] for i in idxs]



REPLACE = td.TypeDict({
    'MeshOpts'    : ['refImage'],
    'VolumeOpts'  : ['clipImage'],
    'VectorOpts'  : ['colourImage', 'modulateImage', 'clipImage']
})
"""This dict contains :class:`.DisplayOpts` properties which refer to other
images, and which need to be explicitly handled when the
:class:`OverlayManager` swaps a group of overlays in for another.
"""


SKIP = td.TypeDict({
    'DisplayOpts' : ['bounds'],
    'NiftiOpts'   : ['transform'],
    'MeshOpts'    : ['vertexSet', 'vertexData', 'vertexDataIndex'],
})
"""This dict contains :class:`.DisplayOpts` properties which are not copied
when the :class:`OverlayManager` swaps a group of overlays in for an existing
group.
"""


class ToReplace(object):
    """Placeholder type used by the :func:`getProperties` function when a
    property value is in the :attr:`REPLACE` dictionary, and needs to be
    explicitly handled by the :class:`OverlayManager`.
    """
    def __init__(self, value):
        self.value = value


def getProperties(ovl, displayCtx):
    """Retrieves the :class:`.Display` and :class:`DisplayOpts` properties
    for the given overlay, applying the rules defined by the :attr:`REPLACE`
    and :attr:`SKIP` dictionaries.

    :arg ovl:        An overlay
    :arg displayCtx: The :class:`.DisplayContext` managing the overlay display.
    :returns:        a dict of ``{ name : value}`` mappings.
    """

    propVals = {}
    display  = displayCtx.getDisplay(ovl)
    opts     = displayCtx.getOpts(   ovl)
    skip     = list(it.chain(*SKIP   .get(opts, [], allhits=True)))
    replace  = list(it.chain(*REPLACE.get(opts, [], allhits=True)))

    for propName in display.getAllProperties()[0]:
        propVals[propName] = getattr(display, propName)

    for propName in opts.getAllProperties()[0]:

        if propName in skip:
            continue

        value = getattr(opts, propName)

        if value is None:
            continue

        if (propName in replace) and (value is not None):
            value = ToReplace(value.name)

        propVals[propName] = value

    return propVals
