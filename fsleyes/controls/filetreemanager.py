#!/usr/bin/env python
#
# filetreemanager.py - Functions and classes used by the FileTreePanel.
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
:mod:`.filetree` specification. The ``FileTreePanel`` allows the user to
select which file types to display, and to restrict or re-order the files
with file tree variables.


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
import fsleyes.actions.loadoverlay     as loadoverlay
import fsleyes.displaycontext.meshopts as meshopts


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

        # Generate a key which uniquely identifies
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


    def __hash__(self):
        """Returns a unique hash for this ``FileGroup``. """
        return (hash(self.varyings) ^
                hash(self.fixed)    ^
                hash(self.ftypes)   ^
                hash(self.files))


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

    :arg fixed:    Dict of ``{ ftype : { var : [value] } }`` mappings
                   which, for each file type, contains a dictionary of
                   all fixed variables and their possible values.

    :returns:      A list of ``FileGroup`` objects.
    """

    # Build a list of file groups - each
    # file group represents a group of
    # files to be displayed together,
    # corresponding to a combination of
    # varying values
    filegroups = []

    # loop through all possible
    # combinations of varying values
    for rowi, vals in enumerate(it.product(*varyings.values())):

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

        # Drop rows which have no files
        if not all([f is None for f in groupFiles]):
            grp = FileGroup(groupVars, groupFixed, groupFtypes, groupFiles)
            filegroups.append(grp)

    return filegroups


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

        query              = self.query
        varyings           = prepareVaryings(query, ftypes, varyings)
        fixed              = prepareFixed(   query, ftypes, fixed)
        varcols, fixedcols = genColumns(     ftypes, varyings, fixed)
        filegroups         = genFileGroups(  query, varyings, fixedcols)

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


    def show(self, filegroup):
        """Show the overlays associated with a :class:`FileGroup`. The
        ``filegroup`` is passed to the :meth:`OverlayManager.show` method.
        """
        self.__ovlmgr.show(filegroup)


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
        self.__cache       = cache.Cache(maxsize=50, lru=True)
        self.__filegroups  = None
        self.__order       = None


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


    def update(self, filegroups):
        """Must be called when the list of ``FileGroup`` objects has changed,
        either due to them being re-ordered or completely changed.
        """
        self.__filegroups = filegroups
        self.__order      = []


    def show(self, filegroup):
        """Show the overlays associated with the given :class:`FileGroup`.

        Any overlays which were previously displayed are removed, and replaced
        with the overlays associated with the new group.
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
        # overlays with the same
        # file ID - we will replace
        # the existing ones with the
        # new ones.
        old = collections.OrderedDict()
        for ovl in displayCtx.getOrderedOverlays():
            if ovl.name in new:
                old[ovl.name] = ovl

        # Save the ordering of the old
        # overlays so we can preserve
        # it in the new overlays. The
        # length check is to take into
        # account missingd files -
        # file groups with more present
        # files should take precedence
        # over file groups with more
        # missing files.
        if len(old) >= len(self.__order):
            self.__order = list(old.keys())

        # Set the ordering of the new
        # overlays based on the old ones
        order = self.__order
        keys  = [k for k in order if k     in new] + \
                [k for k in new   if k not in order]
        new   = collections.OrderedDict([(k, new[k]) for k in keys])

        if len(new) > 0:
            self.__load(new, old)


    def __load(self, new, old):
        """Called by :meth:`show`. Loads the files specified in ``new``, then
        passes them (along with the ``old``) to the :meth:`__show` method.

        :arg new: Dict of ``{fileid : file}`` mappings, containing the
                  files to load.

        :arg old: Dict of ``{fileid : overlay}`` mappings, containing the
                  existing overlays which will be replaced with the new ones.
        """

        # Remove any files that are
        # in the cache, and don't
        # need to be re-loaded
        cache     = self.__cache
        toload    = [(k, f) for k, f in new.items() if f not in cache]
        loadkeys  = [kf[0] for kf in toload]
        loadfiles = [kf[1] for kf in toload]

        def onLoad(ovlidxs, ovls):

            # Gather the overlays to be shown,
            # either from the ones that were
            # just loaded, or from the cache.
            toshow = collections.OrderedDict()

            for key, fname in new.items():

                # Is this overlay in the cache?
                if fname in cache:
                    toshow[key] = cache[fname]

                # Or has it just been loaded?
                else:
                    idx         = loadkeys.index(key)
                    toshow[key] = ovls[idx]
                    cache.put(fname, ovls[idx])

            self.__show(toshow, old)

        loadoverlay.loadOverlays(loadfiles, onLoad=onLoad)


    def __show(self, new, old):
        """Adds the given ``new`` overlays to the :class:`.OverlayList`. The
        display properties of any ``old`` overlays with the same ID are copied
        over to the new ones.

        All existing overlays which were previously added are removed.
        """

        overlayList = self.__overlayList
        displayCtx  = self.__displayCtx

        # Get refs to all existing filetree
        # overlays, because we're going to
        # remove them all after adding the
        # new ones
        oldovls = [o for o in overlayList
                   if o.name.startswith(FILETREE_PREFIX) and
                   o not in new.values()]

        # Drop new overlays that
        # are already in the list
        new = collections.OrderedDict(
            [(key, ovl) for key, ovl in new.items()
             if ovl not in overlayList])

        for key, ovl in new.items(): log.debug('Adding %s: %s', key, ovl)
        for      ovl in oldovls:     log.debug('Removing %s',   ovl)

        # We set the name of each new overlay
        # to its ID key. If the user changes
        # the overlay name, it will no longer
        # be tracked
        for key, ovl in new.items():
            ovl.name = key

        # Get a list of overlay types from
        # the old overlays, if present
        propVals = collections.defaultdict(dict)
        for key, ovl in new.items():
            if key in old:

                oldovl  = old[key]
                display = displayCtx.getDisplay(oldovl)
                opts    = displayCtx.getOpts(   oldovl)

                for propName in display.getAllProperties()[0]:
                    propVals[propName][ovl] = getattr(display, propName)
                for propName in opts.getAllProperties()[0]:

                    val = getattr(opts, propName)

                    # these get calculated automatically
                    if propName in ('bounds', 'transform'):
                        continue

                    # mesh data/vertices are complicated,
                    # so I'm not doing them for the time
                    # being.
                    if isinstance(opts, meshopts.MeshOpts):

                        if propName in ('vertexData', 'vertexSet'):
                            continue

                        # Find a new reference image
                        if propName == 'refImage':
                            ref = opts.refImage
                            if ref is not None and ref.name in new:
                                val = new[ref.name]

                    propVals[propName][ovl] = val

        # Insert the new overlays
        # into the list. We'll sort
        # out overlay order later on.
        overlayList.extend(new.values(), **propVals)

        # Remove all of the
        # old filetree overlays
        idxs           = range(len(overlayList))
        idxs           = [i for i in idxs if overlayList[i] not in oldovls]
        overlayList[:] = [overlayList[i] for i in idxs]
