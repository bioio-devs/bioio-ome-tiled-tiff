#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import dask.array as da
import xarray as xr
from bfio import BioReader
from bioio_base import constants, dimensions, exceptions, io, reader, transforms, types
from fsspec.implementations.local import LocalFileSystem
from fsspec.spec import AbstractFileSystem
from ome_types import OME
from tifffile.tifffile import TiffFileError, TiffTags

from . import utils

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class Reader(reader.Reader):
    """
    BioIO reader plugin for ome tiled tiffs.

    Parameters
    ----------
    image: types.PathLike
        Path to image file.
    chunk_dims: List[str]
        Which dimensions to create chunks for.
        Default: DEFAULT_CHUNK_DIMS
        Note: Dimensions.SpatialY, and Dimensions.SpatialX will always be added to the
        list if not present during dask array construction.
    out_order: List[str]
        The output dimension ordering.
        Default: DEFAULT_DIMENSION_ORDER
    fs_kwargs: Dict[str, Any]
        Any specific keyword arguments to pass down to the fsspec created filesystem.
        Default: {}

    Notes
    -----
    If the OME metadata in your file isn't OME schema compliant or does not validate
    this will fail to read your file and raise an exception.

    If the OME metadata in your file doesn't use the latest OME schema (2016-06),
    this reader will make a request to the referenced remote OME schema to validate.
    """

    _xarray_dask_data: Optional["xr.DataArray"] = None
    _xarray_data: Optional["xr.DataArray"] = None
    _mosaic_xarray_dask_data: Optional["xr.DataArray"] = None
    _mosaic_xarray_data: Optional["xr.DataArray"] = None
    _dims: Optional[dimensions.Dimensions] = None
    _metadata: Optional[Any] = None
    _scenes: Optional[Tuple[str, ...]] = None
    _current_scene_index: int = 0
    # Do not provide default value because
    # they may not need to be used by your reader (i.e. input param is an array)
    _fs: "AbstractFileSystem"
    _path: str

    @staticmethod
    def _is_supported_image(fs: AbstractFileSystem, path: str, **kwargs: Any) -> bool:
        try:
            if not isinstance(fs, LocalFileSystem):
                raise exceptions.UnsupportedFileFormatError(
                    path, "This file is not located on a local file system."
                )

            with BioReader(path, backend="python") as br:
                # Fail fast if multi-image file
                if len(br.metadata.images) > 1:
                    raise exceptions.UnsupportedFileFormatError(
                        path,
                        "This file contains more than one scene and only the first "
                        + "scene can be read by the OmeTiledTiffReader. "
                        + "To read additional scenes, use the TiffReader, "
                        + "OmeTiffReader, or BioformatsReader.",
                    )

                return True

        # tifffile exceptions
        except (TypeError, ValueError) as e:
            raise exceptions.UnsupportedFileFormatError(path, "Error: " + str(e))

    def __init__(
        self,
        image: types.PathLike,
        chunk_dims: Optional[Union[str, List[str]]] = None,
        out_order: str = dimensions.DEFAULT_DIMENSION_ORDER,
        fs_kwargs: Dict[str, Any] = {},
        **kwargs: Any,
    ):
        # Expand details of provided image
        self._fs, self._path = io.pathlike_to_fs(
            image,
            enforce_exists=True,
            fs_kwargs=fs_kwargs,
        )

        if not isinstance(self._fs, LocalFileSystem):
            raise ValueError(
                "Cannot read .ome.tif from non-local file system. "
                f"Received URI: {self._path}, which points to {type(self._fs)}."
            )

        try:
            self._rdr = BioReader(self._path, backend="python")
        except (TypeError, ValueError, TiffFileError):
            raise exceptions.UnsupportedFileFormatError(
                self.__class__.__name__, self._path
            )

        # Add ndim attribute so _rdr can be passed directly to dask
        self._rdr.ndim = len(self._rdr.shape)

        # Setup dimension ordering
        dims = "YXZCT"
        self.native_dim_order = dims[: len(self._rdr.shape)]
        assert all(d in out_order for d in dims)
        self.out_dim_order = [d for d in out_order if d in dims]

        # Currently do not support custom chunking, throw a warning.
        if chunk_dims is not None:
            log.warning(
                "OmeTiledTiffReader does not currently support custom chunking."
            )

    @property
    def scenes(self) -> Tuple[str, ...]:
        return tuple(image_meta.id for image_meta in self._rdr.metadata.images)

    @property
    def ome_metadata(self) -> OME:
        return self._rdr.metadata

    @property
    def channel_names(self) -> Optional[List[str]]:
        return self._rdr.channel_names

    @property
    def physical_pixel_sizes(self) -> types.PhysicalPixelSizes:
        return types.PhysicalPixelSizes(
            self._rdr.ps_z[0],
            self._rdr.ps_y[0],
            self._rdr.ps_x[0],
        )

    def _read_delayed(self) -> xr.DataArray:
        return self._general_data_array_constructor(
            da.from_array(self._rdr, chunks=(1024, 1024) + (1,) * (self._rdr.ndim - 2)),
            self._tiff_tags(),
        )

    def _tiff_tags(self) -> Optional[Dict[str, str]]:
        return {
            code: tag.value
            for code, tag in self._rdr._backend._rdr.pages[0].tags.items()
        }

    def _read_immediate(self) -> xr.DataArray:
        return self._general_data_array_constructor(
            self._rdr[:],
            self._tiff_tags(),
        )

    def _general_data_array_constructor(
        self,
        image_data: types.ArrayLike,
        tiff_tags: Optional[TiffTags] = None,
    ) -> xr.DataArray:
        # Unpack dims and coords from OME
        coords = utils.get_coords_from_ome(
            ome=self._rdr.metadata,
            scene_index=0,
        )

        coords = {d: coords[d] for d in self.out_dim_order if d in coords}
        image_data = transforms.reshape_data(
            image_data, self.native_dim_order, "".join(self.out_dim_order)
        )

        attrs = {constants.METADATA_PROCESSED: self._rdr.metadata}

        if tiff_tags is not None:
            attrs[constants.METADATA_UNPROCESSED] = tiff_tags

        return xr.DataArray(
            image_data,
            dims=self.out_dim_order,
            coords=coords,
            attrs=attrs,
        )
