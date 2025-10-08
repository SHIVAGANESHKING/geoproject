from setuptools import setup, find_packages

setup(
    name="terrain-annotator",
    version="1.0.0",
    author="Jules",
    description="A desktop GIS application for terrain annotation.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        # See requirements.txt for the full list of dependencies.
        # Core dependencies that can be installed via pip are listed here.
        'psycopg2-binary',
        'numpy',
        'scipy',
        'pyqtgraph',
        'pyvista',
        'matplotlib',
        'shapely'
    ],
    entry_points={
        'gui_scripts': [
            'terrain-annotator = main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires='>=3.9',
)