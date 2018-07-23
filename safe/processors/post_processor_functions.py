# coding=utf-8

"""Python functions that we use in postprocessors."""

import random
import math
from math import floor

# noinspection PyUnresolvedReferences
from qgis.core import QgsPointXY, NULL

from safe.definitions.exposure import exposure_population
from safe.definitions.hazard_classifications import (
    hazard_classes_all, not_exposed_class)
from safe.definitions.utilities import get_displacement_rate, is_affected, get_classifications
from safe.definitions.constants import big_number
from safe.utilities.utilities import LOGGER
from safe.utilities.i18n import tr

__copyright__ = "Copyright 2017, The InaSAFE Project"
__license__ = "GPL version 3"
__email__ = "info@inasafe.org"
__revision__ = '$Format:%H$'

# # #
# Functions
#
# Note that the function names and docstrings will be shown in the
# definitions report, so keep them neat and tidy!
# # #


def multiply(**kwargs):
    """Simple postprocessor where we multiply the input values.

    :param kwargs: Dictionary of values to multiply
    :type kwargs: dict

    :return: The result.
    :rtype: float
    """
    result = 1
    for i in list(kwargs.values()):
        if not i:
            # If one value is null, we return null.
            return i
        result *= i
    return result


def size(size_calculator, geometry):
    """Simple postprocessor where we compute the size of a feature.

    :param geometry: The geometry.
    :type geometry: QgsGeometry

    :param size_calculator: The size calculator.
    :type size_calculator: safe.gis.vector.tools.SizeCalculator

    :return: The size.
    """
    feature_size = size_calculator.measure(geometry)
    return feature_size


def calculate_distance(
        distance_calculator,
        place_geometry,
        latitude,
        longitude,
        earthquake_hazard=None,
        place_exposure=None):
    """Simple postprocessor where we compute the distance between two points.

    :param distance_calculator: The size calculator.
    :type distance_calculator: safe.gis.vector.tools.SizeCalculator

    :param latitude: The latitude to use.
    :type latitude: float

    :param longitude: The longitude to use.
    :type longitude: float

    :param place_geometry: Geometry of place.
    :type place_geometry: QgsGeometry

    :param earthquake_hazard: The hazard to use.
    :type earthquake_hazard: str

    :param place_exposure: The exposure to use.
    :type place_exposure: str

    :return: distance
    :rtype: float
    """
    _ = earthquake_hazard, place_exposure  # NOQA

    epicenter = QgsPointXY(longitude, latitude)
    place_point = place_geometry.asPoint()
    distance = distance_calculator.measure_distance(epicenter, place_point)
    return distance


def calculate_bearing(
        place_geometry,
        latitude,
        longitude,
        earthquake_hazard=None,
        place_exposure=None
):
    """Simple postprocessor where we compute the bearing angle between two
    points.

    :param place_geometry: Geometry of place.
    :type place_geometry: QgsGeometry

    :param latitude: The latitude to use.
    :type latitude: float

    :param longitude: The longitude to use.
    :type longitude: float

    :param earthquake_hazard: The hazard to use.
    :type earthquake_hazard: str

    :param place_exposure: The exposure to use.
    :type place_exposure: str

    :return: Bearing angle
    :rtype: float
    """
    _ = earthquake_hazard, place_exposure  # NOQA

    epicenter = QgsPointXY(longitude, latitude)
    place_point = place_geometry.asPoint()
    bearing = place_point.azimuth(epicenter)
    return bearing


def calculate_cardinality(
        angle,
        earthquake_hazard=None,
        place_exposure=None
):
    """Simple postprocessor where we compute the cardinality of an angle.

    :param angle: Bearing angle.
    :type angle: float

    :param earthquake_hazard: The hazard to use.
    :type earthquake_hazard: str

    :param place_exposure: The exposure to use.
    :type place_exposure: str

    :return: Cardinality text.
    :rtype: str
    """
    # this method could still be improved later, since the acquisition interval
    # is a bit strange, i.e the input angle of 22.499° will return `N` even
    # though 22.5° is the direction for `NNE`
    _ = earthquake_hazard, place_exposure  # NOQA

    direction_list = tr(
        'N,NNE,NE,ENE,E,ESE,SE,SSE,S,SSW,SW,WSW,W,WNW,NW,NNW'
    ).split(',')

    bearing = float(angle)
    direction_count = len(direction_list)
    direction_interval = 360. / direction_count
    index = int(floor(bearing / direction_interval))
    index %= direction_count
    return direction_list[index]


def post_processor_pcrafi_damage_ratio_function(
        exposure=None, hazard=None, classification=None, hazard_class=None,
        pcrafi_construction_class=None,
        pcrafi_minimum_floor_height_class=None):
    """
    Postprocessor where we compute the fragility of a structure in flood.
    :param exposure:
    :param hazard:
    :param classification:
    :param hazard_class:
    :param pcrafi_construction_class:
    :param pcrafi_minimum_floor_height_class:
    :return: The damage ratio value on the curve for a certain
    pcrafi_construction class or None if any issue happens
    """

    # LOGGER.info(
    # 'PCRAFI Post-processor: %s' % pcrafi_construction_class)
    # LOGGER.info(
    # 'PCRAFI Post-processor: %s' % type(pcrafi_construction_class))

    if pcrafi_construction_class == NULL:
        LOGGER.info(
            'PCRAFI Post-processor: pcrafi_construction_class is NULL')
        return None

    # LOGGER.info(
    # 'PCRAFI Post-processor: %s' % pcrafi_minimum_floor_height_class)
    # LOGGER.info(
    # 'PCRAFI Post-processor: %s' % type(pcrafi_minimum_floor_height_class)
    if pcrafi_minimum_floor_height_class == NULL:
        LOGGER.info(
            'PCRAFI Post-processor: pcrafi_minimum_floor_height_class is NULL')
        return None

    if hazard != 'flood':
        LOGGER.info('PCRAFI Post-processor: %s hazard is not flood' % hazard)
        return None

    classes = {
        111: {
            'mean': 0.7,
            'stdev': 0.2
            },

        121: {
            'mean': 0.7,
            'stdev': 0.2
            },
        122: {
            'mean': 0.7,
            'stdev': 0.2
            },
        211: {
            'mean': 1.5,
            'stdev': 0.5
            },
        221: {
            'mean': 1.5,
            'stdev': 0.5
            },
        311: {
            'mean': 1.5,
            'stdev': 0.5
            },
        321: {
            'mean': 1.5,
            'stdev': 0.5
            },
        411: {
            'mean': 1.5,
            'stdev': 0.5
            },
        421: {
            'mean': 1.5,
            'stdev': 0.5
            },
        511: {
            'mean': 1.5,
            'stdev': 0.5
            },
        512: {
            'mean': 1.5,
            'stdev': 0.5
            },
        611: {
            'mean': 1.5,
            'stdev': 0.5
            },
        711: {
            'mean': 1.5,
            'stdev': 0.5
            },
        911: {
            'mean': 1.5,
            'stdev': 0.5
            },
        921: {
            'mean': 1.5,
            'stdev': 0.5
            },

        }

    # As defined by PCRAFI metadata
    pcrafi_floor_height_range = {
        1: [0.0,0.1],
        2: [0.2,0.3],
        3: [0.4,1.0],
        4: [1.1,3.0],
        5: [3.0,5.0], # note : class 5 is >3.0 but doesnt specify a max, there's probably not many houses with a floor height over 5m
    }

    # Getting the flood height as a numeric value (retromapping from the hazard classification)
    if hazard_class == not_exposed_class['key']:
        flood_numeric_value = 0
    else:
        classification_definition = None
        for c in get_classifications('flood'):
            if c['key'] == classification:
                classification_definition = c
                break

        class_definition = None
        for c in classification_definition['classes']:
            if c['key'] == hazard_class:
                class_definition = c
                break
        flood_numeric_value = class_definition['numeric_default_max']

    # Getting the floor height as a numeric value (retromapping from the floor height class)
    floor_height_range = pcrafi_floor_height_range[pcrafi_minimum_floor_height_class]
    floor_height_numeric_value = random.uniform(floor_height_range[0], floor_height_range[1])

    # Calculating the effective flood height (depth from the floor height)
    effective_flood_height = flood_numeric_value - floor_height_numeric_value

    # LOGGER.debug('PCRAFI Post-processor: flood {} / floor {} / effective {} '.format(flood_numeric_value,floor_height_numeric_value,effective_flood_height))

    try:
        settings = classes[pcrafi_construction_class]
        mean = settings['mean']
        stddev = settings['stdev']
    except KeyError:
        LOGGER.info('PCRAFI Post-processor: no settings or incomplete for construction class %s ' % pcrafi_construction_class)
        return None

    def cumulative_norm_distribution(x, mean, stddev):
        # Taken from https://stats.stackexchange.com/questions/187828/how-are-the-error-function-and-standard-normal-distribution-function-related/187909#comment644574_187909
        return (1.0 + math.erf((x - mean) / (stddev * math.sqrt(2.0)))) / 2.0

    # Calculate the actual damage ratio
    damage_ratio = cumulative_norm_distribution(effective_flood_height, mean, stddev)
    return damage_ratio

def post_processor_pcrafi_damage_state_function(pcrafi_damage_ratio=None):

    # This maps from damage ratio to damage states, currently mapping is abritrary (ranges are [min;max[ )
    # TODO : this should probably be defined somewhere in definitions
    pcrafi_damage_state_ranges = {
        # we must make sure lowerbound of first DS is higher than cumulative_norm_distribution(0,mean,stddev),
        # if not we get incoherent results as unaffected areas aren't aggregated in the hazard value
        'DS0' : [-big_number,0.0015],
        'DS1' : [0.0015,0.25],
        'DS2' : [0.25,0.5],
        'DS3' : [0.5,0.75],
        'DS4' : [0.75,1.0],
        'DS5' : [1.0,big_number],
    }

    # Map the damage ratio to the damage state
    for ds, range_ in pcrafi_damage_state_ranges.items():
        if pcrafi_damage_ratio >= range_[0] and pcrafi_damage_ratio < range_[1]:
            return ds

    LOGGER.info('PCRAFI Post-processor: could not map damage ratio %s to damage state' % damage)
    return None


def post_processor_pcrafi_damage_state_function_factory(ds):
    """Returns a function that checks if the given damage ratio is within the damage state"""

    def func(pcrafi_damage_ratio=None):
        if post_processor_pcrafi_damage_state_function(pcrafi_damage_ratio) == ds:
            return 1
        else:
            return 0
    return func


# This postprocessor function is also used in the aggregation_summary
def post_processor_affected_function(
        exposure=None, hazard=None, classification=None, hazard_class=None):
    """Private function used in the affected postprocessor.

    It returns a boolean if it's affected or not, or not exposed.

    :param exposure: The exposure to use.
    :type exposure: str

    :param hazard: The hazard to use.
    :type hazard: str

    :param classification: The hazard classification to use.
    :type classification: str

    :param hazard_class: The hazard class of the feature.
    :type hazard_class: str

    :return: If this hazard class is affected or not. It can be `not exposed`.
        The not exposed value returned is the key defined in
        `hazard_classification.py` at the top of the file.
    :rtype: bool,'not exposed'
    """
    if exposure == exposure_population['key']:
        affected = is_affected(
            hazard, classification, hazard_class)
    else:
        classes = None
        for hazard in hazard_classes_all:
            if hazard['key'] == classification:
                classes = hazard['classes']
                break

        for the_class in classes:
            if the_class['key'] == hazard_class:
                affected = the_class['affected']
                break
        else:
            affected = not_exposed_class['key']

    return affected


def post_processor_population_displacement_function(
        hazard=None, classification=None, hazard_class=None, population=None):
    """Private function used in the displacement postprocessor.

    :param hazard: The hazard to use.
    :type hazard: str

    :param classification: The hazard classification to use.
    :type classification: str

    :param hazard_class: The hazard class of the feature.
    :type hazard_class: str

    :param population: We don't use this value here. It's only used for
        condition for the postprocessor to run.
    :type population: float, int

    :return: The displacement ratio for a given hazard class.
    :rtype: float
    """
    _ = population  # NOQA

    return get_displacement_rate(hazard, classification, hazard_class)


def post_processor_population_fatality_function(
        classification=None, hazard_class=None, population=None):
    """Private function used in the fatality postprocessor.

    :param classification: The hazard classification to use.
    :type classification: str

    :param hazard_class: The hazard class of the feature.
    :type hazard_class: str

    :param population: We don't use this value here. It's only used for
        condition for the postprocessor to run.
    :type population: float, int

    :return: The displacement ratio for a given hazard class.
    :rtype: float
    """
    _ = population  # NOQA
    for hazard in hazard_classes_all:
        if hazard['key'] == classification:
            classification = hazard['classes']
            break

    for hazard_class_def in classification:
        if hazard_class_def['key'] == hazard_class:
            displaced_ratio = hazard_class_def.get('fatality_rate', 0.0)
            if displaced_ratio is None:
                displaced_ratio = 0.0
            # We need to cast it to float to make it works.
            return float(displaced_ratio)

    return 0.0
