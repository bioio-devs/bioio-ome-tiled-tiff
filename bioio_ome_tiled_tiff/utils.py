from typing import Any, Dict, List, Union

import numpy as np
from bioio_base import dimensions, types
from ome_types import OME


def get_coords_from_ome(
    ome: OME, scene_index: int
) -> Dict[str, Union[List[Any], Union[types.ArrayLike, Any]]]:
    """
    Process the OME metadata to retrieve the coordinate planes.

    Parameters
    ----------
    ome: OME
        A constructed OME object to retrieve data from.
    scene_index: int
        The current operating scene index to pull metadata from.

    Returns
    -------
    coords: Dict[str, Union[List[Any], Union[types.ArrayLike, Any]]]
        The coordinate planes / data for each dimension.
    """

    # Select scene
    scene_meta = ome.images[scene_index]

    # Get coordinate planes
    coords: Dict[str, Union[List[str], np.ndarray]] = {}

    # Channels
    # Channel name isn't required by OME spec, so try to use it but
    # roll back to ID if not found
    coords[dimensions.DimensionNames.Channel] = [
        channel.name if channel.name is not None else channel.id
        for channel in scene_meta.pixels.channels
    ]

    # Time
    # If global linear timescale we can np.linspace with metadata
    if scene_meta.pixels.time_increment is not None:
        coords[dimensions.DimensionNames.Time] = generate_coord_array(
            0, scene_meta.pixels.size_t, scene_meta.pixels.time_increment
        )
    # If non global linear timescale, we need to create an array of every plane
    # time value
    elif scene_meta.pixels.size_t > 1:
        if len(scene_meta.pixels.planes) > 0:
            t_index_to_delta_map = {
                p.the_t: p.delta_t for p in scene_meta.pixels.planes
            }
            coords[dimensions.DimensionNames.Time] = list(t_index_to_delta_map.values())
        else:
            coords[dimensions.DimensionNames.Time] = np.linspace(
                0,
                scene_meta.pixels.size_t - 1,
                scene_meta.pixels.size_t,
            )

    # Handle Spatial Dimensions
    if scene_meta.pixels.physical_size_z is not None:
        coords[dimensions.DimensionNames.SpatialZ] = generate_coord_array(
            0, scene_meta.pixels.size_z, scene_meta.pixels.physical_size_z
        )
    if scene_meta.pixels.physical_size_y is not None:
        coords[dimensions.DimensionNames.SpatialY] = generate_coord_array(
            0, scene_meta.pixels.size_y, scene_meta.pixels.physical_size_y
        )
    if scene_meta.pixels.physical_size_x is not None:
        coords[dimensions.DimensionNames.SpatialX] = generate_coord_array(
            0, scene_meta.pixels.size_x, scene_meta.pixels.physical_size_x
        )

    return coords


def generate_coord_array(
    start: Union[int, float], stop: Union[int, float], step_size: Union[int, float]
) -> np.ndarray:
    """
    Generate an np.ndarray for coordinate values.

    Parameters
    ----------
    start: Union[int, float]
        The start value.
    stop: Union[int, float]
        The stop value.
    step_size: Union[int, float]
        How large each step should be.

    Returns
    -------
    coords: np.ndarray
        The coordinate array.

    Notes
    -----
    In general, we have learned that floating point math is hard....
    This block of code used to use `np.arange` with floats as parameters and
    it was causing errors. To solve, we generate the range with ints and then
    multiply by a float across the entire range to get the proper coords.
    See: https://github.com/AllenCellModeling/aicsimageio/issues/249
    """
    return np.arange(start, stop) * step_size
