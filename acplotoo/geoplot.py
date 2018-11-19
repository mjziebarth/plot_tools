# -*- coding: utf-8 -*-
#
# Acplotoo Geoplot class file.
# Copyright (C) 2018 Malte Ziebarth
# 
# This software is distributed under the MIT license.
# See the LICENSE file in this repository.

from .geoplot_base.rect import Rect
from .geoplot_base.base import GeoplotBase

from warnings import warn

import numpy as np





# GEOPLOT:

class Geoplot(GeoplotBase):


	def __init__(self, ax, projection, limits_xy=None, gshhg_path=None,
	             which_ticks='significant', water_color='lightblue',
	             land_color='white', verbose=0, use_joblib=False,
	             resize_figure=False):
		"""
		Init method.

		Required arguments:
		   ax         :
		   projection :
		   limits_xy  : [xlim, ylim]

		Optional arguments:
		   which_ticks : Determines which ticks to display at which
		                 axis. One of:
		                 'both' - draw both lon and lat ticks on all
		                     axes.
		                 'significant' - draw either lon or lat
		                     what has more ticks.
		                 'lonlat' - draw lon ticks at x- and lat ticks
		                     at y-axis
		                 'latlon' - reverse 'lonlat'
		   use_joblib  : Whether to use joblib to cache some intermediat
		                 results (e.g. coastlines). Can be useful if a
		                 lot of plots are created for the same projection.
		"""

		super().__init__(ax, projection, gshhg_path, which_ticks,
		                 water_color, land_color, verbose, use_joblib,
		                 resize_figure)

		self._gshhg_path = gshhg_path


		self._canvas = None
		self._plot_canvas = self._canvas

		# Setup configuration:
		self._box_axes = False
		self._box_axes_width = 0.1

		# If limits are given, set them:
		if limits_xy is not None:
			self._user_xlim = limits_xy[0]
			self._user_ylim = limits_xy[1]
			self._xlim = self._user_xlim
			self._ylim = self._user_ylim
			self._schedule_callback()


	def set_xlim(self, xlim):
		# TODO Sanity checks.
		self._user_xlim = xlim
		self._schedule_callback()

	def set_ylim(self, ylim):
		self._user_ylim = ylim
		self._schedule_callback()

	def coastline(self, level, water_color=None, land_color=None,
	              zorder=0, **kwargs):
		"""
		Plot the coast line.
		"""
		if self._gshhg_path is None:
			raise RuntimeError("GSHHG not loaded!")

		if water_color is not None:
			self._water_color = water_color

		if land_color is not None:
			self._land_color = land_color


		# Schedule coastline:
		self._scheduled += [['coastline', False, (level,zorder,kwargs)]]
		self._schedule_callback()

	def grid(self, on=True, grid_constant=1.0, anchor_lon=0.0, anchor_lat=0.0, **kwargs):
		"""
		Set grid on or off.
		"""
		# Save configuration:
		self._grid_on = on
		self._grid_constant = grid_constant
		self._grid_kwargs = {**self._grid_kwargs_base, **kwargs}
		self._grid_anchor = (anchor_lon, anchor_lat)

		if not "linewidth" in kwargs:
			self._grid_kwargs["linewidth"] = 0.5

		# Schedule callback:
		self._update_grid = True
		self._schedule_callback()


	def scatter(self, lon, lat, **kwargs):
		"""
		Scatter plot.
		"""
		# Schedule marker plot:
		self._scheduled += [['scatter', False, (lon, lat, kwargs)]]
		self._schedule_callback()

	def quiver(self, lon, lat, u, v, c=None, **kwargs):
		"""
		Quiver (arrow) plot.

		Required arguments:
		   lon, lat : Geodetic coordinates of arrow origins.
		   u        : Vector components in longitude direction.
		   v        : Vector components in latitude direction.

		Optional arguments:
		   c        : Vector of colors.
		              (Default: None)
		   kwargs   : Passed to matplotlib quiver.
		"""
		# Schedule quiver:
		self._scheduled += [['quiver', False, (lon, lat, u, v, c, kwargs)]]
		self._schedule_callback()

	def streamplot_projected(self, x, y, u, v, **kwargs):
		"""
		Streamplot.

		Required arguments:
		   x, y : 1d-arrays defining the grid in projected coordinates
		   u    : 2d-grid of vector components in longitude direction.
		   v    : 2d-grid of vector components in latitude direction.
		
		Optional arguments:
		   kwargs : Passed to matplotlib streamplot
		"""
		# Schedule streamplot:
		self._scheduled += [['streamplot', False, (x, y, u, v, kwargs)]]
		self._schedule_callback()

	def streamplot(self, lon, lat, u, v, **kwargs):
		# TODO Interpolate data to grid and do streamplot on grid!
		# TODO : Also convert start point!
		raise NotImplementedError("Geoplot.streamplot() not implemented yet.")

	def tensorfield_symmetric_2d(self, lon=None, lat=None, t1=None, t2=None, angle=None,
	                             x=None, y=None, linewidth=1.0, **kwargs):
		"""
		Plot a two-dimensional field of a symmetric two-dimensional tensor
		using streamplot. The tensor's principal axis direction is visualized
		using the streamplot line direction. The difference between first
		and second principal component is visualized using the line widths.
		The first principal component's amplitude is visualized using a
		color map applied to the lines.
		"""
		# Exactly one of the pairs (lon,lat) and (x,y) has to be given:
		if (lon is None) == (x is None) or (lon is None) != (lat is None) \
		or (x is None) != (y is None):
			raise ValueError("Exactly one of the pairs (lon,lat) or (x,y) have "
			                 "to be given!")

		# Tensor has to be given:
		if t1 is None or t2 is None or angle is None:
			raise ValueError("Tensor has to be given!")

		# Calculate relevant properties from tensor:
		color = t1
		width = t1-t2
		u = np.sin(np.deg2rad(angle))
		v = np.cos(np.deg2rad(angle))

		# Save keys in addition to old ones:
		kwdict = dict(kwargs)
		if "color" in kwdict:
			warn("Keyword 'color' passed to streamplot is being overridden.")
		kwdict["linewidth"] = linewidth * (width - width.min())/(width.max() - width.min())
		kwdict["color"] = color

		# Call streamplot:
		if lon is not None:
			self.streamplot(lon, lat, u, v, **kwargs)
		else:
			self.streamplot_projected(x, y, u, v, **kwdict)


	def imshow_projected(self, z, xlim, ylim, **kwargs):
		"""
		Plot a field (in projected coordinates) using imshow.
		"""
		# Check data limits:
		if self._data_xlim is None:
			self._data_xlim = xlim
		else:
			if xlim[0] < self._data_xlim[0]:
				self._data_xlim[0] = xlim[0]
			if xlim[1] > self._data_xlim[1]:
				self._data_xlim[1] = xlim[1]
		if self._data_ylim is None:
			self._data_ylim = ylim
		else:
			if ylim[0] < self._data_ylim[0]:
				self._data_ylim[0] = ylim[0]
			if ylim[1] > self._data_ylim[1]:
				self._data_ylim[1] = ylim[1]

		# Schedule plot:
		self._scheduled += [['imshow', False, (z, xlim,ylim,kwargs)]]
		self._schedule_callback()