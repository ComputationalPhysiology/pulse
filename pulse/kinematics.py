#!/usr/bin/env python
from dolfin import Identity, det
from dolfin import grad as Grad
from dolfin import inner, inv, tr

try:
    from dolfin_adjoint import Constant
except ImportError:
    from dolfin import Constant


from .dolfin_utils import get_dimesion


# Second order identity tensor
def SecondOrderIdentity(F):
    """Return identity with same dimension as input"""
    dim = get_dimesion(F)
    return Identity(dim)


def DeformationGradient(u, isochoric=False):
    """Return deformation gradient from displacement."""
    Id = SecondOrderIdentity(u)
    F = Id + Grad(u)
    if isochoric:
        return IsochoricDeformationGradient(F)
    else:
        return F


def IsochoricDeformationGradient(F):
    """Return the isochoric deformation gradient"""
    J = Jacobian(F)
    dim = get_dimesion(F)
    return pow(J, -1.0 / float(dim)) * F


def Jacobian(F):
    """Determinant of the deformation gradient"""
    return det(F)


def EngineeringStrain(F, isochoric=False):
    """Equivalent of engineering strain"""
    Id = SecondOrderIdentity(F)
    if isochoric:
        return IsochoricDeformationGradient(F) - Id
    else:
        return F - Id


def GreenLagrangeStrain(F, isochoric=False):
    """Green-Lagrange strain tensor"""
    Id = SecondOrderIdentity(F)
    C = RightCauchyGreen(F, isochoric)
    return 0.5 * (C - Id)


def LeftCauchyGreen(F, isochoric=False):
    """Left Cauchy-Green tensor"""
    if isochoric:
        F_ = IsochoricDeformationGradient(F)
    else:
        F_ = F

    return F_ * F_.T


def RightCauchyGreen(F, isochoric=False):
    """Left Cauchy-Green tensor"""
    if isochoric:
        F_ = IsochoricDeformationGradient(F)
    else:
        F_ = F

    return F_.T * F_


def EulerAlmansiStrain(F, isochoric=False):
    """Euler-Almansi strain tensor"""
    Id = SecondOrderIdentity(F)
    b = LeftCauchyGreen(F, isochoric)
    return 0.5 * (Id - inv(b))


# Invariants #####
class Invariants(object):
    def __init__(self, isochoric=True, *args):
        self._isochoric = isochoric

    @property
    def is_isochoric(self):
        return self._isochoric

    def _I1(self, F):

        C = RightCauchyGreen(F, self._isochoric)
        I1 = tr(C)
        return I1

    def _I2(self, F):
        C = RightCauchyGreen(F, self._isochoric)
        return 0.5 * (self._I1(F) * self._I1(F) - tr(C * C))

    def _I3(self, F):
        C = RightCauchyGreen(F, self._isochoric)
        return det(C)

    def _I4(self, F, a0):

        if a0 is not None:
            C = RightCauchyGreen(F, self._isochoric)
            I4 = inner(C * a0, a0)
        else:
            I4 = Constant(0.0)
        return I4

    def _I5(self, F, a0):
        if a0 is not None:
            C = RightCauchyGreen(F, self._isochoric)
            I5 = inner(C * a0, C * a0)
        else:
            I5 = Constant(0.0)
        return I5

    def _I6(self, F, b0):
        return self._I4(F, b0)

    def _I7(self, F, b0):
        return self._I5(F, b0)

    def _I8(self, F, a0, b0):
        if a0 is None or b0 is None:
            I8 = Constant(0.0)
        else:
            I8 = inner(F * a0, F * b0)
        return I8


# Transforms #####
# Pull-back of a two-tensor from the current to the reference
# configuration
def PiolaTransform(A, F):
    J = Jacobian(F)
    B = J * A * inv(F).T
    return B


# Push-forward of a two-tensor from the reference to the current
# configuration
def InversePiolaTransform(A, F):
    J = Jacobian(F)
    B = (1 / J) * A * F.T
    return B
