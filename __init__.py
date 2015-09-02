#!/usr/bin/env python
#
# __init__.py - FSLeyes - a python based OpenGL image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains the application logic for *FSLeyes*.


--------
Overview
--------


*FSLeyes* is an OpenGL application for displaying 3D :mod:`overlays
<.overlay>`. All overlays are stored in a single list, the
:class:`.OverlayList`. Only one ``OverlayList`` ever exists - this list is
shared throughout the application.  The primary overlay type is the NIFTI1
image format, but other overlay types are supported (VTK models), and more
will be supported in the future (e.g. surfaces).


Amongst other things, *FSLeyes* provides the following features:

  - Orthographic view  (:mod:`.orthopanel`)
  - Lightbox view (:mod:`.lightboxpanel`)
  - Time series plotting (:mod:`.timeseriespanel`)
  - Histogram plotting (:mod:`.histogrampanel`)
  - FSL atlas explorer (:mod:`.atlaspanel`)
  - FEAT cluster results explorer (:mod:`.clusterpanel`)
  - NIFTI1 image editing (:mod:`.editor`)
  - A comprehensive command line interface (:mod:`.fsleyes_parseargs`)


---------------------------
Frames, views, and controls
---------------------------


The :class:`.FSLEyesFrame` is the top level GUI object. It is a container for
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
     1  [label="panel.FSLEyesPanel"];
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

All toolbars inherit from the :class:`.FSLEyesToolBar` base class:

.. graphviz::

   digraph toolbar_hierarchy {

     graph [size=""];

     node [style="filled",
           fillcolor="#ffffdd",
           fontname="sans"];
     
     rankdir="BT";
     2  [label="toolbar.FSLEyesToolBar"];
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
:class:`FSLEyesFrame`, and a child ``DisplayContext`` is created for every
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
``FSLEyesFrame``.  All of this synchronisation functionality is provided by
the ``props`` package.


--------------------
Package organisation
--------------------


The rest of *FSLeyes* is organised into the following sub-packages:

.. autosummary::
   ~fsl.fsleyes.views
   ~fsl.fsleyes.controls
   ~fsl.fsleyes.displaycontext
   ~fsl.fsleyes.gl
   ~fsl.fsleyes.profiles
   ~fsl.fsleyes.editor
   ~fsl.fsleyes.actions
   ~fsl.fsleyes.widgets
"""
