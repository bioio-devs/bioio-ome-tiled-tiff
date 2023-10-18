#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Tuple

import numpy as np
import pytest
from bioio_base import dimensions, exceptions, test_utilities
from ome_types import OME

from bioio_ome_tiled_tiff import Reader

from .conftest import LOCAL_RESOURCES_DIR


@pytest.mark.parametrize(
    "filename, "
    "set_scene, "
    "expected_scenes, "
    "expected_shape, "
    "expected_dtype, "
    "expected_dims_order, "
    "expected_channel_names, "
    "expected_physical_pixel_sizes",
    [
        (
            "s_1_t_1_c_1_z_1_ome_tiff_tiles.ome.tif",
            "Image:0",
            ("Image:0",),
            (1, 1, 1, 325, 475),
            np.uint16,
            dimensions.DEFAULT_DIMENSION_ORDER,
            ["Bright"],
            (None, 1.0833333333333333, 1.0833333333333333),
        ),
        (
            "s_1_t_1_c_10_z_1_ome_tiff_tiles.ome.tif",
            "Image:0",
            ("Image:0",),
            (1, 10, 1, 1736, 1776),
            np.uint16,
            dimensions.DEFAULT_DIMENSION_ORDER,
            [f"C:{i}" for i in range(10)],  # This is the actual metadata
            (None, None, None),
        ),
        pytest.param(
            # This is the same file as the first file, but it is not tiled
            # This should throw and error since it is not tiled
            "s_1_t_1_c_1_z_1.ome.tiff",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            marks=pytest.mark.xfail(raises=exceptions.UnsupportedFileFormatError),
        ),
        pytest.param(
            "example.txt",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            marks=pytest.mark.xfail(raises=exceptions.UnsupportedFileFormatError),
        ),
        pytest.param(
            "s_1_t_1_c_2_z_1.lif",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            marks=pytest.mark.xfail(raises=exceptions.UnsupportedFileFormatError),
        ),
    ],
)
def test_ome_tiff_reader(
    filename: str,
    set_scene: str,
    expected_scenes: Tuple[str, ...],
    expected_shape: Tuple[int, ...],
    expected_dtype: np.dtype,
    expected_dims_order: str,
    expected_channel_names: List[str],
    expected_physical_pixel_sizes: Tuple[float, float, float],
) -> None:
    # Construct full filepath
    uri = LOCAL_RESOURCES_DIR / filename

    # Run checks
    test_utilities.run_image_file_checks(
        ImageContainer=Reader,
        image=uri,
        set_scene=set_scene,
        expected_scenes=expected_scenes,
        expected_current_scene=set_scene,
        expected_shape=expected_shape,
        expected_dtype=expected_dtype,
        expected_dims_order=expected_dims_order,
        expected_channel_names=expected_channel_names,
        expected_physical_pixel_sizes=expected_physical_pixel_sizes,
        expected_metadata_type=OME,
    )


@pytest.mark.parametrize(
    "filename, "
    "set_scene, "
    "expected_scenes, "
    "expected_shape, "
    "expected_dtype, "
    "expected_dims_order, "
    "expected_channel_names, "
    "expected_physical_pixel_sizes",
    [
        (
            "pre-variance-cfe_ome_tiff_tiles.ome.tif",
            "Image:0",
            ("Image:0",),
            (1, 9, 65, 600, 900),
            np.uint16,
            dimensions.DEFAULT_DIMENSION_ORDER,
            [
                "Bright_2",
                "EGFP",
                "CMDRP",
                "H3342",
                "SEG_STRUCT",
                "SEG_Memb",
                "SEG_DNA",
                "CON_Memb",
                "CON_DNA",
            ],
            (0.29, 0.10833333333333334, 0.10833333333333334),
        ),
        (
            "variance-cfe_ome_tiff_tiles.ome.tif",
            "Image:0",
            ("Image:0",),
            (1, 9, 65, 600, 900),
            np.uint16,
            dimensions.DEFAULT_DIMENSION_ORDER,
            [
                "CMDRP",
                "EGFP",
                "H3342",
                "Bright_2",
                "SEG_STRUCT",
                "SEG_Memb",
                "SEG_DNA",
                "CON_Memb",
                "CON_DNA",
            ],
            (0.29, 0.10833333333333332, 0.10833333333333332),
        ),
        (
            "actk_ome_tiff_tiles.ome.tif",
            "Image:0",
            ("Image:0",),
            (1, 6, 65, 233, 345),
            np.float64,
            dimensions.DEFAULT_DIMENSION_ORDER,
            [
                "nucleus_segmentation",
                "membrane_segmentation",
                "dna",
                "membrane",
                "structure",
                "brightfield",
            ],
            (0.29, 0.29, 0.29),
        ),
    ],
)
def test_ome_tiff_reader_large_files(
    filename: str,
    set_scene: str,
    expected_scenes: Tuple[str, ...],
    expected_shape: Tuple[int, ...],
    expected_dtype: np.dtype,
    expected_dims_order: str,
    expected_channel_names: List[str],
    expected_physical_pixel_sizes: Tuple[float, float, float],
) -> None:
    # Construct full filepath
    uri = LOCAL_RESOURCES_DIR / filename

    # Run checks
    test_utilities.run_image_file_checks(
        ImageContainer=Reader,
        image=uri,
        set_scene=set_scene,
        expected_scenes=expected_scenes,
        expected_current_scene=set_scene,
        expected_shape=expected_shape,
        expected_dtype=expected_dtype,
        expected_dims_order=expected_dims_order,
        expected_channel_names=expected_channel_names,
        expected_physical_pixel_sizes=expected_physical_pixel_sizes,
        expected_metadata_type=OME,
    )
