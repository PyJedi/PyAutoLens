import math
import numpy as np
from matplotlib import pyplot


class EllipticalProfile(object):
    """Generic elliptical profile class to contain functions shared by light and mass profiles"""

    def __init__(self, axis_ratio, phi, center=(0, 0)):
        """
        Parameters
        ----------
        center: (float, float)
            The coordinates of the centre of the profile
        axis_ratio : float
            Ratio of profile ellipse's minor and major axes (b/a)
        phi : float
            Rotational angle of profile ellipse counter-clockwise from positive x-axis
        """

        self.center = center
        self.axis_ratio = axis_ratio
        self.phi = phi

    @property
    def x_cen(self):
        return self.center[0]

    @property
    def y_cen(self):
        return self.center[1]

    @property
    def cos_phi(self):
        return self.angles_from_x_axis()[0]

    @property
    def sin_phi(self):
        return self.angles_from_x_axis()[1]

    def angles_from_x_axis(self):
        """
        Determine the sin and cosine of the angle between the profile ellipse and positive x-axis, \
        defined counter-clockwise from x.

        Returns
        -------
        The sin and cosine of the angle
        """
        phi_radians = math.radians(self.phi)
        return math.cos(phi_radians), math.sin(phi_radians)

    def coordinates_to_centre(self, shifted_coordinates):
        """
        Converts image coordinates to profile's centre

        Parameters
        ----------
        shifted_coordinates : (float, float)
            The x and y coordinates of the image

        Returns
        ----------
        The coordinates at the mass profile centre
        """
        return shifted_coordinates[0] - self.x_cen, shifted_coordinates[1] - self.y_cen

    def coordinates_to_radius(self, coordinates):
        """
        Convert the coordinates to a radius

        Parameters
        ----------
        coordinates : (float, float)
            The image coordinates (x, y)

        Returns
        -------
        The radius at those coordinates
        """
        return math.sqrt(coordinates[0] ** 2 + coordinates[1] ** 2)

    def coordinates_to_eccentric_radius(self, coordinates):
        """
        Convert the coordinates to a radius in elliptical space.

        Parameters
        ----------
        coordinates : (float, float)
            The image coordinates (x, y)
        Returns
        -------
        The radius at those coordinates
        """

        shifted_coordinates = self.coordinates_rotate_to_elliptical(coordinates)
        return math.sqrt(self.axis_ratio) * math.sqrt(
            shifted_coordinates[0] ** 2 + (shifted_coordinates[1] / self.axis_ratio) ** 2)

    # TODO: This isn't using any variable from the class. Should it be?
    @staticmethod
    def coordinates_angle_from_x(coordinates):
        """
        Compute the angle between the coordinates and positive x-axis, defined counter-clockwise. Elliptical profiles
        are symmetric after 180 degrees, so angles above 180 are converted to their equivalent value from 0.
        (e.g. 225 degrees counter-clockwise from the x-axis is equivalent to 45 degrees counter-clockwise)

        Parameters
        ----------
        coordinates : (float, float)
            The x and y coordinates of the image.

        Returns
        ----------
        The angle between the coordinates and the x-axis and profile centre
        """
        theta_from_x = math.degrees(np.arctan2(coordinates[1], coordinates[0]))

        return theta_from_x

    def coordinates_angle_to_profile(self, theta):
        """
        Compute the sin and cosine of the angle between the shifted coordinates and elliptical profile

        Parameters
        ----------
        theta : Float

        Returns
        ----------
        The sin and cosine of the angle between the shifted coordinates and profile ellipse.
        """
        theta_coordinate_to_profile = math.radians(theta - self.phi)
        return math.cos(theta_coordinate_to_profile), math.sin(theta_coordinate_to_profile)

    def coordinates_back_to_cartesian(self, coordinates_elliptical):
        """
        Rotate elliptical coordinates back to the original Cartesian grid (for a cirular profile this
        returns the input coordinates)

        Parameters
        ----------
        coordinates_elliptical : (float, float)
            The x and y coordinates of the image translated to the elliptical coordinate system

        Returns
        ----------
        The coordinates (typically deflection angles) on a regular Cartesian grid
        """
        x_elliptical = coordinates_elliptical[0]
        x = (x_elliptical * self.cos_phi - coordinates_elliptical[1] * self.sin_phi)
        y = (+x_elliptical * self.sin_phi + coordinates_elliptical[1] * self.cos_phi)
        return x, y

    def coordinates_rotate_to_elliptical(self, coordinates):
        """
        Translate Cartesian image coordinates to the lens profile's reference frame (for a circular profile this
        returns the input coordinates)

        Parameters
        ----------
        coordinates : (float, float)
            The x and y coordinates of the image

        Returns
        ----------
        The coordinates after the elliptical translation
        """

        # TODO: Big error here, coordinates_to_centre is not performed (it is only performed in coordinates_to_radius)
        # TODO: Our coordinates below are therefore not translated to the lens profile coordinates
        # TODO: Need to unit test this explicitly - Ill fix tomorrow

        # Shift coordinates to lens profile center
        shifted_coordinates = self.coordinates_to_centre(coordinates)

        # Compute their distance to its centre
        radius = self.coordinates_to_radius(shifted_coordinates)

        # Compute the angle between the coordinates and x-axis
        theta_from_x = self.coordinates_angle_from_x(shifted_coordinates)

        # Compute the angle between the coordinates and profile ellipse
        cos_theta, sin_theta = self.coordinates_angle_to_profile(theta_from_x)

        # Multiply by radius to get their x / y distance from the profile centre in this elliptical unit system
        return radius * cos_theta, radius * sin_theta


class SphericalProfile(EllipticalProfile):
    """Generic circular profile class to contain functions shared by light and mass profiles"""

    def __init__(self, center=(0, 0)):
        """
        Parameters
        ----------
        center: (float, float)
            The coordinates of the centre of the profile
        """
        super(SphericalProfile, self).__init__(1.0, 0.0, center)


class LightProfile(object):
    """Mixin class that implements functions common to all light profiles"""

    def as_array(self, x_min=0, y_min=0, x_max=10, y_max=10, pixel_scale=0.1):
        """

        Parameters
        ----------
        pixel_scale : float
            The arcsecond (") size of each pixel
        x_min : int
            The minimum x bound
        y_min : int
            The minimum y bound
        x_max : int
            The maximum x bound
        y_max : int
            The maximum y bound

        Returns
        -------
        array
            A numpy array illustrating this light profile between the given bounds
        """

        array = np.zeros((int((x_max - x_min)), int((y_max - y_min))))
        #TODO : Make own function of generic Profile class?
        x_center, y_center = ((x_max + x_min) / 2.0, (y_max + y_min) / 2.0)
        for x in range(x_min, x_max):
            for y in range(y_min, y_max):
                array[x, y] = self.flux_at_coordinates(((x - x_center) * pixel_scale, (y - y_center) * pixel_scale))
        return array

    def as_flat_array(self, x_min=0, y_min=0, x_max=10, y_max=10, pixel_scale=0.1):
        """

        Parameters
        ----------
        pixel_scale : float
            The arcsecond (") size of each pixel
        x_min : int
            The minimum x bound
        y_min : int
            The minimum y bound
        x_max : int
            The maximum x bound
        y_max : int
            The maximum y bound

        Returns
        -------
        array
            A flat numpy array illustrating this light profile between the given bounds
        """
        return self.as_array(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max, pixel_scale=pixel_scale).flatten()

    # noinspection PyMethodMayBeStatic
    def flux_at_coordinates(self, coordinates):
        """
        Abstract method for obtaining flux at given coordinates
        Parameters
        ----------
        coordinates : (int, int)
            The coordinates in image space
        Returns
        -------
        flux : float
            The value of flux at the given coordinates
        """
        raise AssertionError("Flux at coordinates should be overridden")

    def plot(self, x_min=0, y_min=0, x_max=10, y_max=10, pixel_scale=0.1):
        """
        Draws a plot of this light profile. Upper normalisation limit determined by taking mean plus one standard
        deviation

        Parameters
        ----------
        pixel_scale : float
            The arcsecond (") size of each pixel
        x_min : int
            The minimum x bound
        y_min : int
            The minimum y bound
        x_max : int
            The maximum x bound
        y_max : int
            The maximum y bound

        """
        array = self.as_array(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max, pixel_scale=pixel_scale)
        pyplot.imshow(array)
        pyplot.clim(vmax=np.mean(array) + np.std(array))
        pyplot.show()


class CombinedLightProfile(list, LightProfile):
    def __init__(self, *light_profiles):
        super(CombinedLightProfile, self).__init__(light_profiles)

    def flux_at_coordinates(self, coordinates):
        """
        Method for obtaining flux at given coordinates
        Parameters
        ----------
        coordinates : (int, int)
            The coordinates in image space
        Returns
        -------
        flux : float
            The value of flux at the given coordinates
        """
        return sum(map(lambda p: p.flux_at_coordinates(coordinates), self))


class SersicLightProfile(EllipticalProfile, LightProfile):
    """Used to fit the light of a galaxy. It can produce both highly concentrated light profiles (for high Sersic Index)
     or extended flatter profiles (for low Sersic Index)."""

    def __init__(self, axis_ratio, phi, flux, effective_radius, sersic_index, center=(0, 0)):
        """

        Parameters
        ----------
        center: (float, float)
            The coordinates of the centre of the profile
        axis_ratio : float
            Ratio of profile ellipse's minor and major axes (b/a)
        phi : float
            Rotational angle of profile ellipse counter-clockwise from positive x-axis
        flux : float
            Overall flux intensity normalisation in the light profile (electrons per second)
        effective_radius : float
            The radius containing half the light of this model
        sersic_index : Int
            The concentration of the light profile
        """
        super(SersicLightProfile, self).__init__(axis_ratio, phi, center)
        self.flux = flux
        self.effective_radius = effective_radius
        self.sersic_index = sersic_index

    @property
    def elliptical_effective_radius(self):
        # Extra physical parameters not used by the model, but have value scientifically
        return self.effective_radius / self.axis_ratio

    @property
    def sersic_constant(self):
        """

        Returns
        -------
        sersic_constant: float
            A parameter, derived from sersic_index, that ensures that effective_radius always contains 50% of the light.
        """
        return (2 * self.sersic_index) - (1. / 3.) + (4. / (405. * self.sersic_index)) + (
            46. / (25515. * self.sersic_index ** 2)) + (131. / (1148175. * self.sersic_index ** 3)) - (
                   2194697. / (30690717750. * self.sersic_index ** 4))

    def flux_at_radius(self, radius):
        """

        Parameters
        ----------
        radius : float
            The distance from the centre of the profile
        Returns
        -------
        flux: float
            The flux at that radius
        """
        return self.flux * math.exp(
            -self.sersic_constant * (((radius / self.effective_radius) ** (1. / self.sersic_index)) - 1))

    def flux_at_coordinates(self, coordinates):
        """
        Method for obtaining flux at given coordinates
        Parameters
        ----------
        coordinates : (int, int)
            The coordinates in image space
        Returns
        -------
        flux : float
            The value of flux at the given coordinates
        """
        radius = self.coordinates_to_eccentric_radius(coordinates)
        return self.flux_at_radius(radius)


class ExponentialLightProfile(SersicLightProfile):
    """Used to fit flatter regions of light in a galaxy, typically its disks or stellar halo. It is a subset of the
    Sersic profile, corresponding exactly to the solution sersic_index = 1"""

    def __init__(self, axis_ratio, phi, flux, effective_radius, center=(0, 0)):
        """

        Parameters
        ----------
        center: (float, float)
            The coordinates of the centre of the profile
        axis_ratio : float
            Ratio of profile ellipse's minor and major axes (b/a)
        phi : float
            Rotational angle of profile ellipse counter-clockwise from positive x-axis
        flux : float
            Overall flux intensity normalisation in the light profile (electrons per second)
        effective_radius : float
            The radius containing half the light of this model
        """
        super(ExponentialLightProfile, self).__init__(axis_ratio, phi, flux, effective_radius, 1, center)


class DevVaucouleursLightProfile(SersicLightProfile):
    """Used to fit the concentrated regions of light in a galaxy, typically its bulge. It may also fit the entire light
    profile of an elliptical / early-type galaxy. It is a subset of the Sersic profile, corresponding exactly to the
    solution sersic_index = 4."""

    def __init__(self, axis_ratio, phi, flux, effective_radius, center=(0, 0)):
        """

        Parameters
        ----------
        center: (float, float)
            The coordinates of the centre of the profile
        axis_ratio : float
            Ratio of profile ellipse's minor and major axes (b/a)
        phi : float
            Rotational angle of profile ellipse counter-clockwise from positive x-axis
        flux : float
            Overall flux intensity normalisation in the light profile (electrons per second)
        effective_radius : float
            The radius containing half the light of this model
        """
        super(DevVaucouleursLightProfile, self).__init__(axis_ratio, phi, flux, effective_radius, 4, center)


class CoreSersicLightProfile(SersicLightProfile):
    """The Core-Sersic profile is used to fit the light of a galaxy. It is an extension of the Sersic profile and
    flattens the light profiles central values (compared to the extrapolation of a pure Sersic profile), by forcing
    these central regions to behave instead as a power-law."""

    def __init__(self, axis_ratio, phi, flux, effective_radius, sersic_index, radius_break, flux_break,
                 gamma, alpha, center=(0, 0)):
        """

        Parameters
        ----------
        center: (float, float)
            The coordinates of the centre of the profile
        axis_ratio : float
            Ratio of profile ellipse's minor and major axes (b/a)
        phi : float
            Rotational angle of profile ellipse counter-clockwise from positive x-axis
        flux : float
            Overall flux intensity normalisation in the light profile (electrons per second)
        effective_radius : float
            The radius containing half the light of this model
        sersic_index : Int
            The concentration of the light profile
        radius_break : Float
            The break radius separating the inner power-law (with logarithmic slope gamma) and outer Sersic function.
        flux_break : Float
            The intensity at the break radius.
        gamma : Float
            The logarithmic power-law slope of the inner core profile
        alpha :
            Controls the sharpness of the transition between the inner core / outer Sersic profiles.
        """
        super(CoreSersicLightProfile, self).__init__(axis_ratio, phi, flux, effective_radius,
                                                     sersic_index, center)
        self.radius_break = radius_break
        self.flux_break = flux_break
        self.alpha = alpha
        self.gamma = gamma

    @property
    def flux_prime(self):
        """Overall flux intensity normalisation in the rescaled Core-Sersic light profile (electrons per second)"""
        return self.flux_break * (2.0 ** (-self.gamma / self.alpha)) * math.exp(
            self.sersic_constant * (((2.0 ** (1.0 / self.alpha)) * self.radius_break) / self.effective_radius) ** (
                1.0 / self.sersic_index))

    def flux_at_radius(self, radius):
        """

        Parameters
        ----------
        radius : float
            The distance from the centre of the profile
        Returns
        -------
        flux: float
            The flux at that radius
        """
        return self.flux_prime * (
            (1 + ((self.radius_break / radius) ** self.alpha)) ** (self.gamma / self.alpha)) * math.exp(
            -self.sersic_constant * (
                (((radius ** self.alpha) + (self.radius_break ** self.alpha)) / (
                    self.effective_radius ** self.alpha)) ** (
                    1.0 / (self.alpha * self.sersic_index))))


class EllipticalPowerLawMassProfile(EllipticalProfile):
    """Represents an elliptical power-law density distribution"""

    def __init__(self, axis_ratio, phi, einstein_radius, slope, center=(0, 0)):
        """

        Parameters
        ----------
        center: (float, float)
            The coordinates of the centre of the profile
        axis_ratio : float
            Ratio of mass profile ellipse's minor and major axes (b/a)
        phi : float
            Rotational angle of mass profile ellipse counter-clockwise from positive x-axis
        einstein_radius : float
            Einstein radius of power-law mass profile
        slope : float
            power-law density slope of mass profile
        """

        super(EllipticalPowerLawMassProfile, self).__init__(axis_ratio, phi, center)

        self.einstein_radius = einstein_radius
        self.slope = slope

    def compute_deflection_angle(self, coordinates):
        """
        Calculate the deflection angle at a given set of image plane coordinates

        Parameters
        ----------
        coordinates : (float, float)
            The x and y coordinates of the image

        Returns
        ----------
        The deflection angle at those coordinates
        """

        # TODO : Unit tests missing - need to sort out scipy.integrate

        coordinates_elliptical = self.coordinates_rotate_to_elliptical(coordinates)

        # TODO: implement a numerical integrator for this profile using scipy and / or c++

        # defl_elliptical = scipy.integrate(coordinates_elliptical, kappa_power_law)
        # defl_angles = self.coordinates_back_to_cartesian(coordinates_elliptical=defl_elliptical)
        # defl_angles = self.normalization*defl_angles
        # return defl_angles

        pass

    @property
    def einstein_radius_rescaled(self):
        return ((3 - self.slope) / (1 + self.axis_ratio)) * self.einstein_radius


class EllipticalIsothermalMassProfile(EllipticalPowerLawMassProfile):
    """Represents an elliptical isothermal density distribution, which is equivalent to the elliptical power-law
    density distribution for the value slope=2.0"""

    def __init__(self, axis_ratio, phi, einstein_radius, center=(0, 0)):
        """

        Parameters
        ----------
        center: (float, float)
            The coordinates of the centre of the profile
        axis_ratio : float
            Ratio of mass profile ellipse's minor and major axes (b/a)
        phi : float
            Rotational angle of mass profile ellipse counter-clockwise from positive x-axis
        einstein_radius : float
            Einstein radius of power-law mass profile
        """

        super(EllipticalIsothermalMassProfile, self).__init__(axis_ratio, phi, einstein_radius, 2.0, center)

    @property
    def normalization(self):
        return self.einstein_radius_rescaled * self.axis_ratio / (math.sqrt(1 - self.axis_ratio ** 2))

    def compute_deflection_angle(self, coordinates):
        """
        Parameters
        ----------
        coordinates : (float, float)
            The x and y coordinates of the image

        Returns
        ----------
        The deflection angles at these coordinates
        """
        coordinates = self.coordinates_rotate_to_elliptical(coordinates)
        psi = math.sqrt((self.axis_ratio ** 2) * (coordinates[0] ** 2) + coordinates[1] ** 2)

        defl_x = self.normalization * math.atan((math.sqrt(1 - self.axis_ratio ** 2) * coordinates[0]) / (psi))
        defl_y = self.normalization * math.atanh((math.sqrt(1 - self.axis_ratio ** 2) * coordinates[1]) / (psi))
        return defl_x, defl_y