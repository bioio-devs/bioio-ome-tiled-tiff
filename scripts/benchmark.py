"""
    Runs bioio_base's benchmark function against the test resources in this repository
"""
import pathlib

import bioio_base.benchmark

import bioio_ome_tiled_tiff


# This file is under /scripts while the test resourcess are under /bioio_ome_tiled_tiff/tests/resources
test_resources_dir = pathlib.Path(__file__).parent.parent / "bioio_ome_tiled_tiff" / "tests" / "resources"
assert test_resources_dir.exists(), f"Test resources directory {test_resources_dir} does not exist"
test_files = [
    test_file
    for test_file in test_resources_dir.iterdir()
    if (test_file.name.endswith(".tif") or test_file.name.endswith(".tiff")) and test_file.name not in {"s_1_t_1_c_1_z_1.ome.tiff"}
]
print(f"Test files: {[file.name for file in test_files]}")
bioio_base.benchmark.benchmark(bioio_ome_tiled_tiff.reader.Reader, test_files)
