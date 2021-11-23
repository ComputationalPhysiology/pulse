# # Custom material
#
# In this demo we show how you can use the pulse-framework
# together with your custom material model.
#
# To illustrate this we will implement a model for a
# Mooney-Rivelin material.
#

import dolfin

# Make sure to use dolfin-adjoint version of object if using dolfin_adjoint
try:
    from dolfin_adjoint import (
        Constant,
        DirichletBC,
        Expression,
        UnitCubeMesh,
        interpolate,
        Mesh,
    )
except ImportError:
    from dolfin import (
        UnitCubeMesh,
        Expression,
        Constant,
        DirichletBC,
        interpolate,
        Mesh,
    )

import pulse
from fenics_plotly import plot

# Create mesh
N = 6
mesh = UnitCubeMesh(N, N, N)


# Create subdomains
class Free(dolfin.SubDomain):
    def inside(self, x, on_boundary):
        return x[0] > (1.0 - dolfin.DOLFIN_EPS) and on_boundary


class Fixed(dolfin.SubDomain):
    def inside(self, x, on_boundary):
        return x[0] < dolfin.DOLFIN_EPS and on_boundary


# Create a facet fuction in order to mark the subdomains
ffun = dolfin.MeshFunction("size_t", mesh, 2)
ffun.set_all(0)

# Mark the first subdomain with value 1
fixed = Fixed()
fixed_marker = 1
fixed.mark(ffun, fixed_marker)

# Mark the second subdomain with value 2
free = Free()
free_marker = 2
free.mark(ffun, free_marker)

# Create a cell function (but we are not using it)
cfun = dolfin.MeshFunction("size_t", mesh, 3)
cfun.set_all(0)


# Collect the functions containing the markers
marker_functions = pulse.MarkerFunctions(ffun=ffun, cfun=cfun)

# Create mictrotructure
f0 = Expression(("1.0", "0.0", "0.0"), degree=1, cell=mesh.ufl_cell())
s0 = Expression(("0.0", "1.0", "0.0"), degree=1, cell=mesh.ufl_cell())
n0 = Expression(("0.0", "0.0", "1.0"), degree=1, cell=mesh.ufl_cell())

# Collect the mictrotructure
microstructure = pulse.Microstructure(f0=f0, s0=s0, n0=n0)

# Create the geometry
geometry = pulse.Geometry(
    mesh=mesh,
    marker_functions=marker_functions,
    microstructure=microstructure,
)


# Use the default material parameters
class MooneyRivelin(pulse.Material):
    @staticmethod
    def default_parameters():
        return dict(C1=1.0, C2=1.0)

    def strain_energy(self, F_):

        # Get elastic part of deformation gradient,
        # in case of active strain model
        F = self.Fe(F_)

        # Active stress (which is zero for acitve strain)
        Wactive = self.Wactive(F, diff=0)

        I1 = pulse.kinematics.I1(F)
        I2 = pulse.kinematics.I2(F)

        return self.C1 * (I1 - 3) + self.C2 * (I2 - 3) + Wactive


# Select model for active contraction
active_model = pulse.ActiveModels.active_strain
# active_model = "active_stress"

# Set the activation
activation = Constant(0.1)

# Create material
material = MooneyRivelin(active_model=active_model, activation=activation)


# Make Dirichlet boundary conditions
def dirichlet_bc(W):
    V = W if W.sub(0).num_sub_spaces() == 0 else W.sub(0)
    return DirichletBC(V, Constant((0.0, 0.0, 0.0)), fixed)


# Make Neumann boundary conditions
neumann_bc = pulse.NeumannBC(traction=Constant(0.0), marker=free_marker)

# Collect Boundary Conditions
bcs = pulse.BoundaryConditions(dirichlet=(dirichlet_bc,), neumann=(neumann_bc,))

# Create problem
problem = pulse.MechanicsProblem(geometry, material, bcs)

# Solve problem
problem.solve()

V = dolfin.VectorFunctionSpace(geometry.mesh, "CG", 1)
u, p = problem.state.split(deepcopy=True)
u_int = interpolate(u, V)
mesh = Mesh(geometry.mesh)
dolfin.ALE.move(mesh, u_int)

fig = plot(geometry.mesh, show=False)
fig.add_plot(plot(mesh, color="red", show=False))
fig.show()
