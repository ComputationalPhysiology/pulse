import logging as _logging
import os

# Check if dolfin-adjoint is installed, and if
# the 'DOLFIN_ADJOINT' flag is set to 0, then
# we remove it from sys.modules
try:
    import dolfin_adjoint  # noqa: F401
except ImportError:
    pass
else:
    if not bool(int(os.getenv("DOLFIN_ADJOINT", "1"))):
        import sys

        sys.modules["dolfin_adjoint"] = None  # type: ignore
        _logging.warning("Dolfin-adjoint found but will be turned off")


import daiquiri as _daiquiri


from . import dolfin_utils
from . import geometry
from . import geometry_utils
from . import io_utils
from . import iterate
from . import kinematics
from . import material
from . import mechanicsproblem
from . import numpy_mpi
from . import solver
from . import unloader
from . import utils
from .__version__ import __version__
from .dolfin_utils import MixedParameter
from .dolfin_utils import QuadratureSpace
from .dolfin_utils import RegionalParameter
from .example_meshes import mesh_paths
from .geometry import CRLBasis
from .geometry import Geometry
from .geometry import HeartGeometry
from .geometry import MarkerFunctions
from .geometry import Microstructure
from .kinematics import DeformationGradient
from .kinematics import EulerAlmansiStrain
from .kinematics import GreenLagrangeStrain
from .kinematics import Invariants
from .kinematics import InversePiolaTransform
from .kinematics import Jacobian
from .kinematics import LeftCauchyGreen
from .kinematics import PiolaTransform
from .kinematics import RightCauchyGreen
from .kinematics import SecondOrderIdentity
from .material import ActiveModel
from .material import ActiveStrain
from .material import ActiveStress
from .material import Guccione
from .material import HolzapfelOgden
from .material import LinearElastic
from .material import Material
from .material import NeoHookean
from .material import StVenantKirchhoff
from .mechanicsproblem import BoundaryConditions
from .mechanicsproblem import MechanicsProblem
from .mechanicsproblem import NeumannBC
from .mechanicsproblem import RobinBC
from .solver import NonlinearProblem
from .solver import NonlinearSolver
from .unloader import FixedPointUnloader
from .unloader import MeshUnloader
from .unloader import RaghavanUnloader
from .utils import annotation


def set_log_level(level):
    from daiquiri import set_default_log_levels

    loggers = [
        "pulse.utils.logger",
        "pulse.dolfin_utils.logger",
        "pulse.io_utils.logger",
        "pulse.solver.logger",
        "pulse.mechanicsproblem.logger",
        "pulse.iterate.logger",
        "pulse.unloader.logger",
        "pulse.geometry.logger",
        "pulse.geometry_utils.logger",
    ]
    set_default_log_levels((logger, level) for logger in loggers)


_daiquiri.setup(level=_logging.INFO)


ffc_logger = _logging.getLogger("FFC")
ffc_logger.setLevel(_logging.WARNING)
ffc_logger.addFilter(utils.mpi_filt)

ufl_logger = _logging.getLogger("UFL")
ufl_logger.setLevel(_logging.WARNING)
ufl_logger.addFilter(utils.mpi_filt)

__author__ = "Henrik Finsberg"
__credits__ = ["Henrik Finsberg"]
__license__ = "LGPL-3.0-or-later"
__maintainer__ = "Henrik Finsberg"
__email__ = "henriknf@simula.no"

__all__ = [
    "annotation",
    "utils",
    "dolfin_utils",
    "io_utils",
    "numpy_mpi",
    "kinematics",
    "mechanicsproblem",
    "iterate",
    "unloader",
    "Geometry",
    "CRLBasis",
    "HeartGeometry",
    "Microstructure",
    "MarkerFunctions",
    "QuadratureSpace",
    "MixedParameter",
    "RegionalParameter",
    "material",
    "MeshUnloader",
    "RaghavanUnloader",
    "FixedPointUnloader",
    "BoundaryConditions",
    "MechanicsProblem",
    "NeumannBC",
    "RobinBC",
    "ActiveStrain",
    "ActiveStress",
    "ActiveModel",
    "Material",
    "HolzapfelOgden",
    "Guccione",
    "LinearElastic",
    "NeoHookean",
    "StVenantKirchhoff",
    "SecondOrderIdentity",
    "DeformationGradient",
    "Jacobian",
    "GreenLagrangeStrain",
    "LeftCauchyGreen",
    "RightCauchyGreen",
    "EulerAlmansiStrain",
    "Invariants",
    "PiolaTransform",
    "InversePiolaTransform",
    "set_log_level",
    "__version__",
    "solver",
    "mesh_paths",
    "NonlinearProblem",
    "NonlinearSolver",
    "geometry",
    "geometry_utils",
]

__author__ = "Henrik Finsberg"
__credits__ = ["Henrik Finsberg"]
__license__ = "LGPL-3"
__maintainer__ = "Henrik Finsberg"
__email__ = "henriknf@simula.no"
