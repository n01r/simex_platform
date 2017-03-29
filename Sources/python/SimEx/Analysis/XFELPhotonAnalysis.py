##########################################################################
#                                                                        #
# Copyright (C) 2015-2017 Carsten Fortmann-Grote                         #
# Contact: Carsten Fortmann-Grote <carsten.grote@xfel.eu>                #
#                                                                        #
# This file is part of simex_platform.                                   #
# simex_platform is free software: you can redistribute it and/or modify #
# it under the terms of the GNU General Public License as published by   #
# the Free Software Foundation, either version 3 of the License, or      #
# (at your option) any later version.                                    #
#                                                                        #
# simex_platform is distributed in the hope that it will be useful,      #
# but WITHOUT ANY WARRANTY; without even the implied warranty of         #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
# GNU General Public License for more details.                           #
#                                                                        #
# You should have received a copy of the GNU General Public License      #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
##########################################################################
"""
    :module XFELPhotonAnalysis: Module that hosts the XFELPhotonAnalysis class."""
from SimEx.Analysis.AbstractAnalysis import AbstractAnalysis, plt, mpl

import numpy
import wpg

class XFELPhotonAnalysis(AbstractAnalysis):
    """
    :class XFELPhotonAnalysis: Class that implements common data analysis tasks for wavefront (radiation field) data.
    """

    def __init__(self, input_path=None,):
        """ Constructor for the XFELPhotonAnalysis class.

        :param input_path: Name of file or directory that contains data to analyse.
        :type input_path: str

        """

        # Initialize base class. This takes care of parameter checking.
        super(XFELPhotonAnalysis, self).__init__(input_path)

        # Get wavefront file name.
        self.__wavefront = wpg.Wavefront()
        self.__wavefront.load_hdf5(self.input_path)

    @property
    def wavefront(self):
        """ Query for the wavefront. """
        return self.__wavefront

    def plotIntensityMap(self, qspace=False, logscale=False):
        """ Plot the integrated intensity as function of x,y or qx, qy on a colormap.

        :param qspace: Whether to plot the reciprocal space intensity map (default False).
        :type qspace: bool

        :param logscale: Whether to plot the intensity on a logarithmic scale (z-axis) (default False).
        :type logscale: bool

        """
        # Setup new figure.
        plt.figure()

        # Get the wavefront and integrate over time.
        wf = self.wavefront

        # Switch to q-space if requested.
        if qspace:
            wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 'a')

        # Get intensity.
        wf_intensity = wf.get_intensity().sum(axis=-1)

        # Get average and time slicing.
        nslices = wf.params.Mesh.nSlices
        if (nslices>1):
            dt = (wf.params.Mesh.sliceMax-wf.params.Mesh.sliceMin)/(nslices-1)
            t0 = dt*nslices/2 + wf.params.Mesh.sliceMin
        else:
            t0 = (wf.params.Mesh.sliceMax+wf.params.Mesh.sliceMin)/2

        # Setup a figure.
        figure = plt.figure(figsize=(10, 10), dpi=100)
        plt.axis('tight')
        # Profile plot.
        profile = plt.subplot2grid((3, 3), (1, 0), colspan=2, rowspan=2)

        # Get limits.
        xmin, xmax, ymax, ymin = wf.get_limits()
        mn, mx = wf_intensity.min(), wf_intensity.max()

        # Plot profile as 2D colorcoded map.
        if logscale:
            profile.imshow(wf_intensity, norm=mpl.colors.LogNorm(vmin=mn, vmax=mx), extent=[xmin*1.e6, xmax*1.e6, ymax*1.e6, ymin*1.e6], cmap="viridis")
        else:
            profile.imshow(wf_intensity, norm=mpl.colors.Normalize(vmin=mn, vmax=mx), extent=[xmin*1.e6, xmax*1.e6, ymax*1.e6, ymin*1.e6], cmap="viridis")

        profile.set_aspect('equal', 'datalim')

        # Get x and y ranges.
        x = numpy.linspace(xmin*1.e6, xmax*1.e6, wf_intensity.shape[1])
        y = numpy.linspace(ymin*1.e6, ymax*1.e6, wf_intensity.shape[0])

        # Labels.
        if qspace:
            profile.set_xlabel(r'$q_{x}\ \mathrm{(\mu rad)}$')
            profile.set_ylabel(r'$q_{y}\ \mathrm{(\mu rad)}$')
        else:
            profile.set_xlabel(r'$x\ \mathrm{(\mu m)}$')
            profile.set_ylabel(r'$y\ \mathrm{(\mu m)}$')

        # x-projection plots above main plot.
        x_projection = plt.subplot2grid((3, 3), (0, 0), sharex=profile, colspan=2)
        print(x.shape, wf_intensity.sum(axis=0).shape)

        x_projection.plot(x, wf_intensity.sum(axis=0), label='x projection')

        # Set range according to input.
        profile.set_xlim([xmin*1.e6, xmax*1.e6])

        # y-projection plot right of main plot.
        y_projection = plt.subplot2grid((3, 3), (1, 2), rowspan=2, sharey=profile)
        y_projection.plot(wf_intensity.sum(axis=1), y, label='y projection')

        # Hide minor tick labels, they disturb here.
        plt.minorticks_off()

        # Set range according to input.
        profile.set_ylim([ymin*1.e6, ymax*1.e6])


    def plotTotalPower(self, spectrum=False):
        """ Method to plot the total power.

        :param spectrum: Whether to plot the power density in energy domain (True) or time domain (False, default).
        :type spectrum: bool

        """

        """ Adapted from github:Samoylv/WPG/wpg/wpg_uti_wf.integral_intensity() """
        # Setup new figure.
        plt.figure()

        # Get wavefront.
        wf = self.wavefront

        # Switch to frequency (energy) domain if requested.
        if spectrum:
            wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 'f')

        # Get dimensions.
        mesh = wf.params.Mesh
        dx = (mesh.xMax - mesh.xMin)/(mesh.nx - 1)
        dy = (mesh.yMax - mesh.yMin)/(mesh.ny - 1)

        # Get intensity by integrating over transverse dimensions.
        int0 = wf.get_intensity().sum(axis=0).sum(axis=0)
        # Scale to get unit W/mm^2
        int0 = int0*(dx*dy*1.e6) #  amplitude units sqrt(W/mm^2)
        int0max = int0.max()

        # Get center pixel numbers.
        center_nx = int(mesh.nx/2)
        center_ny = int(mesh.ny/2)

        # Get meaningful slices.
        aw = [a[0] for a in numpy.argwhere(int0 > int0max*0.01)]
        int0_mean = int0[min(aw):max(aw)]  # meaningful range of pulse
        dSlice = (mesh.sliceMax - mesh.sliceMin)/(mesh.nSlices - 1)
        xs = numpy.arange(mesh.nSlices)*dSlice+ mesh.sliceMin
        xs_mf = numpy.arange(min(aw), max(aw))*dSlice + mesh.sliceMin
        if(wf.params.wDomain=='time'):
            plt.plot(xs*1e15, int0) # time axis converted to fs.
            plt.plot(xs_mf*1e15, int0_mean, 'ro')
            plt.title('Power')
            plt.xlabel('time (fs)')
            plt.ylabel('Power (W)')
            dt = (mesh.sliceMax - mesh.sliceMin)/(mesh.nSlices - 1)
            print('Pulse energy {:1.2g} J'.format(int0_mean.sum()*dt))

        else: #frequency domain
            plt.plot(xs, int0)
            plt.plot(xs_mf, int0_mean, 'ro')
            plt.title('Spectral Energy')
            plt.xlabel('eV')
            plt.ylabel('J/eV')

            # Switch back to time domain.
            wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 't')

    def plotOnAxisPowerDensity(self, spectrum=False):
        """ Method to plot the on-axis power density.

        :param spectrum: Whether to plot the power density in energy domain (True) or time domain (False, default).
        :type spectrum: bool

        """
        """ Adapted from github:Samoylv/WPG/wpg/wpg_uti_wf.integral_intensity() """

        # Setup new figure.
        plt.figure()

        # Get wavefront.
        wf = self.wavefront

        # Switch to frequency (energy) domain if requested.
        if spectrum:
            wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 'f')

        # Get dimensions.
        mesh = wf.params.Mesh
        dx = (mesh.xMax - mesh.xMin)/(mesh.nx - 1)
        dy = (mesh.yMax - mesh.yMin)/(mesh.ny - 1)

        # Get center pixel numbers.
        center_nx = int(mesh.nx/2)
        center_ny = int(mesh.ny/2)

        # Get on-axis intensity.
        intensity = wf.get_intensity()
        int0_00 = intensity[center_ny, center_nx, :]
        int0 = intensity.sum(axis=(0,1))*(dx*dy*1.e6) #  amplitude units sqrt(W/mm^2)
        int0max = int0.max()

        # Get meaningful slices.
        aw = [a[0] for a in numpy.argwhere(int0 > int0max*0.01)]
        dSlice = (mesh.sliceMax - mesh.sliceMin)/(mesh.nSlices - 1)

        xs = numpy.arange(mesh.nSlices)*dSlice+ mesh.sliceMin
        xs_mf = numpy.arange(min(aw), max(aw))*dSlice + mesh.sliceMin

        # Plot.
        if(wf.params.wDomain=='time'):
            plt.plot(xs*1e15,int0_00)
            plt.plot(xs_mf*1e15, int0_00[min(aw):max(aw)], 'ro')
            plt.title('On-Axis Power Density')
            plt.xlabel('time (fs)')
            plt.ylabel(r'Power density (W/mm${}^{2}$)')
        else: #frequency domain
            plt.plot(xs,int0_00)
            plt.plot(xs_mf, int0_00[min(aw):max(aw)], 'ro')
            plt.title('On-Axis Spectral Fluence')
            plt.xlabel('photon energy (eV)')
            plt.ylabel(r'fluence (J/eV/mm${}^{2}$)')

            # Switch back to time domain.
            wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 't')