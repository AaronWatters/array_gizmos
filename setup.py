from setuptools import setup

url = "https://github.com/AaronWatters/array_gizmos"
version = "0.1.0"
readme = open('README.md').read()

setup(
    name="array_gizmos",
    packages=[
        "array_gizmos",
        ],
    version=version,
    description="A collection of array operations and visualizations",
    long_description=readme,
    long_description_content_type="text/markdown",
    #include_package_data=True,
    author="Aaron Watters",
    author_email="awatters@flatironinstitute.org",
    url=url,
    install_requires=[
        "numpy",
        "H5Gizmos",
        ],
    scripts = [
        "bin/compare_npz_labels",
    ],
    python_requires=">=3.6",
)
