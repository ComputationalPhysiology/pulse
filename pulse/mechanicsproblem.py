#!/usr/bin/env python
from collections import namedtuple
from functools import partial

import dolfin
try:
    from dolfin_adjoint import (Function, Constant,
                                NonlinearVariationalSolver,
                                NonlinearVariationalProblem,
                                FunctionAssigner)
    has_dolfin_adjoint = True
except ImportError:
    from dolfin import (Function, Constant,
                        NonlinearVariationalSolver,
                        NonlinearVariationalProblem,
                        FunctionAssigner)
    has_dolfin_adjoint = False

from . import kinematics
from . import parameters
from .utils import set_default_none, make_logger, get_lv_marker
from .geometry import HeartGeometry

logger = make_logger(__name__, parameters['log_level'])

BoundaryConditions = namedtuple('BoundaryConditions',
                                ['dirichlet', 'neumann',
                                 'robin', 'body_force'])
set_default_none(BoundaryConditions, ())

NeumannBC = namedtuple('NeumannBC', ['traction', 'marker', 'name'])
# Name is optional
NeumannBC.__new__.__defaults__ = ('',)
RobinBC = namedtuple('RobinBC', ['value', 'marker'])


def dirichlet_fix_base(W, ffun, marker):
    '''Fix the basal plane.
    '''
    V = W if W.sub(0).num_sub_spaces() == 0 else W.sub(0)
    bc = dolfin.DirichletBC(V, dolfin.Constant((0, 0, 0)),
                            ffun, marker)
    return bc


def dirichlet_fix_base_directional(W, ffun, marker, direction=0):
    V = W if W.sub(0).num_sub_spaces() == 0 else W.sub(0)
    bc = dolfin.DirichletBC(V.sub(direction),
                            dolfin.Constant(0.0),
                            ffun, marker)
    return bc


def cardiac_boundary_conditions(geometry, pericardium_spring=0.0,
                                base_spring=0.0, base_bc='fix_x'):

    msg = ('Cardiac boundary conditions can only be applied to a '
           'HeartGeometry got {}'.format(type(geometry)))
    assert isinstance(geometry, HeartGeometry), msg

    # Neumann BC
    lv_marker = get_lv_marker(geometry)
    lv_pressure = NeumannBC(traction=Constant(0.0, name="lv_pressure"),
                            marker=lv_marker, name='lv')
    neumann_bc = [lv_pressure]

    if 'ENDO_RV' in geometry.markers:

        rv_pressure = NeumannBC(traction=Constant(0.0, name='lv_pressure'),
                                marker=geometry.markers['ENDO_RV'][0],
                                name='rv')

        neumann_bc += [rv_pressure]

    # Robin BC
    if pericardium_spring > 0.0:

        robin_bc = [RobinBC(value=dolfin.Constant(pericardium_spring),
                            marker=geometry.markers["EPI"][0])]

    else:
        robin_bc = []

    # Apply a linear sprint robin type BC to limit motion
    if base_spring > 0.0:
        robin_bc += [RobinBC(value=dolfin.Constant(base_spring),
                             marker=geometry.markers["BASE"][0])]

    # Dirichlet BC
    if base_bc == "fixed":

        dirichlet_bc = [partial(dirichlet_fix_base,
                                ffun=geometry.ffun,
                                marker=geometry.markers["BASE"][0])]

    elif base_bc == 'fix_x':

        dirichlet_bc = [partial(dirichlet_fix_base_directional,
                                ffun=geometry.ffun,
                                marker=geometry.markers["BASE"][0])]
    else:
        raise ValueError("Unknown base bc {}".format(base_bc))

    boundary_conditions = BoundaryConditions(dirichlet=dirichlet_bc,
                                             neumann=neumann_bc,
                                             robin=robin_bc)

    return boundary_conditions


class SolverDidNotConverge(Exception):
    pass


class MechanicsProblem(object):
    """
    Base class for mechanics problem
    """
    def __init__(self, geometry, material, bcs=None, bcs_parameters=None):

        logger.debug('Initialize mechanics problem')
        self.geometry = geometry
        self.material = material

        if bcs is None:
            if isinstance(geometry, HeartGeometry):
                self.bcs_parameters = MechanicsProblem.default_bcs_parameters()
                self.bcs_parameters.update(**bcs_parameters)
                
            else:
                raise ValueError(('Please provive boundary conditions '
                                  'to MechanicsProblem'))

            self.bcs = cardiac_boundary_conditions(geometry,
                                                   **self.bcs_parameters)
            
        else:
            self.bcs = bcs

            # Just store this as well in case both is provided
            if bcs_parameters is not None:
                self.bcs_parameters = MechanicsProblem.default_bcs_parameters()
                self.bcs_parameters.update(**bcs_parameters)
            
            
        # Make sure that the material has microstructure information
        for attr in ("f0", "s0", "n0"):
            setattr(self.material, attr, getattr(self.geometry, attr))

        self._init_spaces()
        self._init_forms()

    @staticmethod
    def default_bcs_parameters():
        return dict(pericardium_spring=0.0,
                    base_spring=0.0,
                    base_bc='fixed')

    def _init_spaces(self):

        logger.debug('Initialize spaces for mechanics problem')
        mesh = self.geometry.mesh

        P2 = dolfin.VectorElement("Lagrange", mesh.ufl_cell(), 2)
        P1 = dolfin.FiniteElement("Lagrange", mesh.ufl_cell(), 1)

        # P2_space = FunctionSpace(mesh, P2)
        # P1_space = FunctionSpace(mesh, P1)
        self.state_space = dolfin.FunctionSpace(mesh, P2*P1)

        self.state = Function(self.state_space, name="state")
        self.state_test = dolfin.TestFunction(self.state_space)

    def _init_forms(self):

        logger.debug('Initialize forms mechanics problem')
        # Displacement and hydrostatic_pressure
        u, p = dolfin.split(self.state)
        v, q = dolfin.split(self.state_test)

        # Some mechanical quantities
        F = dolfin.variable(kinematics.DeformationGradient(u))
        J = kinematics.Jacobian(F)

        # Some geometrical quantities
        N = self.geometry.facet_normal
        ds = self.geometry.ds
        dx = self.geometry.dx

        internal_energy = self.material.strain_energy(F) \
            + self.material.compressibility(p, J)

        self._virtual_work \
            = dolfin.derivative(internal_energy * dx,
                                self.state, self.state_test)

        # DirichletBC
        for dirichlet_bc in self.bcs.dirichlet:

            msg = ('DirichletBC only implemented for as '
                   'callable. Please provide DirichletBC '
                   'as a callable with argument being the '
                   'state space only')

            if hasattr(dirichlet_bc, '__call__'):
                try:
                    self._dirichlet_bc \
                        = dirichlet_bc(self.state_space)
                except Exception as ex:
                    logger.error(msg)
                    raise ex
            else:

                raise NotImplementedError(msg)

        for neumann in self.bcs.neumann:

            n = neumann.traction * dolfin.cofac(F) * N
            self._virtual_work += dolfin.inner(v, n) * ds(neumann.marker)

        for robin in self.bcs.robin:

            self._virtual_work += dolfin.inner(robin.value * u, v) \
                                  * ds(robin.marker)

        for body_force in self.bcs.body_force:

            self._virtual_work \
                += -dolfin.derivative(dolfin.inner(body_force, u) * dx, u, v)

        self._jacobian \
            = dolfin.derivative(self._virtual_work, self.state,
                                dolfin.TrialFunction(self.state_space))

    def reinit(self, state, annotate=False):
        """Reinitialze state
        """
        
        if has_dolfin_adjoint:
            self.state.assign(state, annotate=annotate)
            
        else:
            self.state.assign(state)
            
        self._init_forms()

    def solve(self):
        r"""
        Solve the variational problem

        .. math::

           \delta W = 0

        """
        logger.debug('Solving variational problem')
        # Get old state in case of non-convergence
        old_state = self.state.copy(deepcopy=True)
        problem \
            = NonlinearVariationalProblem(self._virtual_work,
                                          self.state,
                                          self._dirichlet_bc,
                                          self._jacobian)

        solver = NonlinearVariationalSolver(problem)

        try:
            logger.debug('Try to solve')
            nliter, nlconv = solver.solve()
            if not nlconv:
                logger.debug('Failed')
                raise SolverDidNotConverge("Solver did not converge...")

        except RuntimeError as ex:
            logger.debug('Failed')
            logger.debug('Reintialize old state and raise exception')

            self.reinit(old_state)

            raise SolverDidNotConverge(ex)
        else:
            logger.debug('Sucess')

        return nliter, nlconv

    def get_displacement(self, annotate=True):

        D = self.state_space.sub(0)
        V = D.collapse()

        fa = FunctionAssigner(V, D)
        u = Function(V, name='displacement')
        if has_dolfin_adjoint:
            fa.assign(u, self.state.split()[0],
                      annotate=annotate)
        else:
            fa.assign(u, self.state.split()[0])
            
        return u

    @classmethod
    def from_geometry(self, geometry):

        if not hasattr(self, 'bcs_parameters'):
            msg = ('Cannot update geometry wihout bcs_parameters '
                   'Please provide bcs_parameters to the constructor')
            raise AttributeError(msg)

        self.material.update_geometry(geometry)
        
        MechanicsProblem.__init__(self, geometry=geometry,
                                  material=self.material,
                                  bcs_parameters=self.bcs_parameters)