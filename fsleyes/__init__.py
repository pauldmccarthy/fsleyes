#!/usr/bin/env python
#
# __init__.py - FSLeyes - a python based OpenGL image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""*FSLeyes* - a 3D image viewer.

This package contains the application logic for *FSLeyes*.


.. image:: images/fsleyes.png
   :scale: 50%
   :align: center


--------
Overview
--------


*FSLeyes* is an OpenGL application for displaying 3D :mod:`overlays
<.overlay>`. All overlays are stored in a single list, the
:class:`.OverlayList`. Only one ``OverlayList`` ever exists - this list is
shared throughout the application.  The primary overlay type is the NIFTI
image format, but other overlay types are supported (VTK models), and more
will be supported in the future (e.g. surfaces).


Amongst other things, *FSLeyes* provides the following features:

  - Orthographic view  (:mod:`.orthopanel`)
  - Lightbox view (:mod:`.lightboxpanel`)
  - Time series plotting (:mod:`.timeseriespanel`)
  - Histogram plotting (:mod:`.histogrampanel`)
  - Power spectrum plotting (:mod:`.powerspectrumpanel`)
  - FSL atlas explorer (:mod:`.atlaspanel`)
  - FEAT cluster results explorer (:mod:`.clusterpanel`)
  - Melodic component classification (:mod:`.melodicclassificationpanel`)
  - NIFTI image editing (:mod:`.editor`)
  - A comprehensive command line interface (:mod:`.fsleyes_parseargs`)


*FSLeyes* makes heavy use of the :mod:`props` project, which is an
event-based framework.


------------
Entry points
------------


*FSLeyes* may be started with the :func:`fsleyes.main.main` function. *FSLeyes*
also includes an off-screen screenshot generator called `render`, which may
be started via the :func:`fsleyes.render.main` function.


---------------------------
Frames, views, and controls
---------------------------


The :class:`.FSLeyesFrame` is the top level GUI object. It is a container for
one or more *views*. All views are defined in the :mod:`.views` sub-package,
and are sub-classes of the :class:`.ViewPanel` class. Currently there are two
primary view categories - :class:`.CanvasPanel` views, which use :mod:`OpenGL`
to display overlays, and :class:`.PlotPanel` views, which use
:mod:`matplotlib` to plot data related to the overlays.


View panels may contain one or more *control* panels which provide an
interface allowing the user to control some aspect of the view (e.g. the
:class:`.OverlayDisplayToolBar`), or to display some other data associated
with the overlays (e.g. the :class:`.ClusterPanel`).  All controls are defined
in the :mod:`.controls` sub-package.


The view/control panel class hierarchy is shown below:

.. graphviz::

   digraph hierarchy {

     graph [size=""];

     node [style="filled",
           fillcolor="#ffffdd",
           fontname="sans"];

     rankdir="BT";
     1  [label="panel.FSLeyesPanel"];
     3  [label="views.viewpanel.ViewPanel"];
     4  [label="views.plotpanel.PlotPanel"];
     5  [label="views.canvaspanel.CanvasPanel"];
     6  [label="views.orthopanel.OrthoPanel"];
     7  [label="<other canvas panels>"];
     8  [label="views.histogrampanel.HistogramPanel"];
     9  [label="<other plot panels>"];
     10 [label="controls.overlaylistpanel.OverlayListPanel"];
     11 [label="<other control panels>"];

     3  -> 1;
     4  -> 3;
     5  -> 3;
     6  -> 5;
     7  -> 5;
     8  -> 4;
     9  -> 4;
     10 -> 1;
     11 -> 1;
   }

All toolbars inherit from the :class:`.FSLeyesToolBar` base class:

.. graphviz::

   digraph toolbar_hierarchy {

     graph [size=""];

     node [style="filled",
           fillcolor="#ffffdd",
           fontname="sans"];

     rankdir="BT";
     2  [label="toolbar.FSLeyesToolBar"];
     12 [label="controls.overlaydisplaytoolbar.OverlayDisplayToolBar"];
     13 [label="controls.lightboxtoolbar.LightBoxToolBar"];
     14 [label="<other toolbars>"];

     12 -> 2;
     13 -> 2;
     14 -> 2;
   }


----------------------
The ``DisplayContext``
----------------------


In order to manage how overlays are displayed, *FSLeyes* uses a
:class:`.DisplayContext`. Because *FSLeyes* allows multiple views to be opened
simultaneously, it needs to use multiple ``DisplayContext`` instances.
Therefore, one master ``DisplayContext`` instance is owned by the
:class:`FSLeyesFrame`, and a child ``DisplayContext`` is created for every
:class:`.ViewPanel`. The display settings managed by each child
``DisplayContext`` instance can be linked to those of the master instance;
this allows display properties to be synchronised across displays.


Each ``DisplayContext`` manages a collection of :class:`.Display` objects, one
for each overlay in the ``OverlayList``. Each of these ``Display`` objects
manages a single :class:`.DisplayOpts` instance, which contains overlay
type-specific display properties. Just as child ``DisplayContext`` instances
can be synchronised with the master ``DisplayContext``, child ``Display`` and
``DisplayOpts`` instances can be synchronised to the master instances.


The above description is summarised in the following diagram:


.. image:: images/fsleyes_architecture.png
   :scale: 40%
   :align: center


In this example, two view panels are open - an :class:`.OrthoPanel`, and a
:class:`.LightBoxPanel`. The ``DisplayContext`` for each of these views, along
with their ``Display`` and ``DisplayOpts`` instances (one of each for every
overlay in the ``OverlayList``) are linked to the master ``DisplayContext``
(and its ``Display`` and ``DisplayOpts`` instances), which is managed by the
``FSLeyesFrame``.  All of this synchronisation functionality is provided by
the ``props`` package.


See the :mod:`~fsleyes.displaycontext` package documentation for more
details.


-----------------------
Events and notification
-----------------------

TODO


.. note:: The current version of FSLeyes (|version|) lives in the
          :mod:`fsleyes.version` module.
"""


import            os
import os.path as op
import            logging
import            warnings

from   .                  import             version
from   fsl.utils.platform import platform as fslplatform
import fsl.utils.settings                 as fslsettings


# The logger is assigned in
# the configLogging function
log = None


# If set to True, logging will not be configured
disableLogging = fslplatform.frozen


__version__ = version.__version__
"""The current *FSLeyes* version (read from the :mod:`fsleyes.version`
module).
"""


assetDir = op.join(op.dirname(__file__), '..')
"""Base directory which contains all *FSLeyes* assets/resources (e.g. icon
files). This is set in the :func:`initialise` function.
"""


def canWriteToAssetDir():
    """Returns ``True`` if the user can write to the FSLeyes asset directory,
    ``False`` otherwise.
    """
    return os.access(op.join(assetDir, 'assets'), os.W_OK | os.X_OK)


def initialise():
    """Called when `FSLeyes`` is started as a standalone application.  This
    function *must* be called before most other things in *FSLeyes* are used,
    but after a ``wx.App`` has been created.

    Does a few initialisation steps::

      - Initialises the :mod:`fsl.utils.settings` module, for persistent
        storage  of application settings.

      - Sets the :data:`assetDir` attribute.
    """

    global assetDir

    import wx
    import matplotlib as mpl

    # Initialise the fsl.utils.settings module
    fslsettings.initialise('fsleyes')

    # Tell matplotlib what backend to use.
    # n.b. this must be called before
    # matplotlib.pyplot is imported.
    mpl.use('WxAgg')

    fsleyesDir = op.dirname(__file__)

    # If we are running from a bundled application,
    # wx will know where the FSLeyes resources are
    if fslplatform.frozen:

        # If we have a display, assume
        # that a wx app has been created
        if fslplatform.canHaveGui:

            sp       = wx.StandardPaths.Get()
            assetDir = op.join(sp.GetResourcesDir())

        # Otherwise we have to guess at the location
        elif fslplatform.os == 'Darwin':
            assetDir = op.join(fsleyesDir, '..', 'Resources')
        elif fslplatform.os == 'Linux':
            assetDir = op.join(fsleyesDir, '..', 'share', 'FSLeyes')

    # Otherwise we are running from a code install,
    # or from a source distribution. The assets
    # directory is either inside, or alongside, the
    # FSLeyes package directory.
    else:

        options = [op.join(fsleyesDir, '..'), fsleyesDir]

        for opt in options:
            if op.exists(op.join(opt, 'assets')):
                assetDir = opt
                break

    assetDir = op.abspath(assetDir)

    if not op.exists(assetDir):
        raise RuntimeError('Could not find FSLeyes asset directory! '
                           'It should be at {}'.format(assetDir))


def configLogging(namespace):
    """Configures *FSLeyes* ``logging``.

    .. note:: All logging calls are usually stripped from frozen
              versions of *FSLeyes*, so this function does nothing
              when we are running a frozen version.
    """

    global log

    # make numpy/matplotlib quiet
    warnings.filterwarnings('ignore', module='matplotlib')
    warnings.filterwarnings('ignore', module='mpl_toolkits')
    warnings.filterwarnings('ignore', module='numpy')
    logging.getLogger('nibabel').setLevel(logging.CRITICAL)

    # Set up my own custom logging level
    # for tracing memory related events.
    logging.MEMORY = 15

    def _logmemory(self, message, *args, **kwargs):
        """Log function for my custom ``logging.MEMORY`` logging level. """
        if logging and self.isEnabledFor(logging.MEMORY):
            self._log(logging.MEMORY, message, args, **kwargs)

    logging.Logger.memory = _logmemory
    logging.addLevelName(logging.MEMORY, 'MEMORY')

    # Set up the root logger
    logFormatter = logging.Formatter('%(levelname)8.8s '
                                     '%(filename)20.20s '
                                     '%(lineno)4d: '
                                     '%(funcName)-15.15s - '
                                     '%(message)s')
    logHandler  = logging.StreamHandler()
    logHandler.setFormatter(logFormatter)

    log = logging.getLogger()
    log.addHandler(logHandler)

    # Everything below this point sets up verbosity
    # as requested by the user. But verbosity-related
    # command line arguments are not exposed to the
    # user in frozen versions of FSLeyes, so if we're
    # running as a frozen app, there's nothing else
    # to do.
    if disableLogging:
        return

    # Now we can set up logging
    # as requested by the user.
    if namespace.noisy is None:
        namespace.noisy = []

    if namespace.verbose is None:
        if namespace.memory:
            class MemFilter(object):
                def filter(self, record):
                    if   record.name in namespace.noisy:   return 1
                    elif record.levelno == logging.MEMORY: return 1
                    else:                                  return 0

            log.setLevel(logging.MEMORY)
            log.handlers[0].addFilter(MemFilter())
            log.memory('Added filter for MEMORY messages')
            logging.getLogger('fsleyes_props')  .setLevel(logging.WARNING)
            logging.getLogger('fsleyes_widgets').setLevel(logging.WARNING)

    if namespace.verbose == 1:
        log.setLevel(logging.DEBUG)

        # make some noisy things quiet
        logging.getLogger('fsleyes.gl')     .setLevel(logging.MEMORY)
        logging.getLogger('fsleyes.views')  .setLevel(logging.MEMORY)
        logging.getLogger('fsleyes_props')  .setLevel(logging.WARNING)
        logging.getLogger('fsleyes_widgets').setLevel(logging.WARNING)
    elif namespace.verbose == 2:
        log.setLevel(logging.DEBUG)
        logging.getLogger('fsleyes_props')  .setLevel(logging.WARNING)
        logging.getLogger('fsleyes_widgets').setLevel(logging.WARNING)
    elif namespace.verbose == 3:
        log.setLevel(logging.DEBUG)
        logging.getLogger('fsleyes_props')  .setLevel(logging.DEBUG)
        logging.getLogger('fsleyes_widgets').setLevel(logging.DEBUG)

    for mod in namespace.noisy:
        logging.getLogger(mod).setLevel(logging.DEBUG)

    # The trace module monkey-patches some
    # things if its logging level has been
    # set to DEBUG, so we import it now so
    # it can set itself up.
    traceLogger = logging.getLogger('fsleyes_props.trace')
    if traceLogger.getEffectiveLevel() <= logging.DEBUG:
        import fsleyes_props.trace
