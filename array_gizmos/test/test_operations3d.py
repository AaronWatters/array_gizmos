import unittest
from array_gizmos import operations3d, transforms3d
import numpy as np

pi2 = np.pi * 0.5

class Test_airplane_transforms(unittest.TestCase):

    def test1(self, translation=(1,1,1), yaw=1, pitch=1, roll=1):
        translation = np.array(translation)
        M = transforms3d.airplane_matrix(translation, yaw, pitch, roll)
        (t, y, p, r) = transforms3d.airplane_parameters(M)
        self.assertAlmostEqual(t.tolist(), translation.tolist())
        self.assertAlmostEqual(y, yaw)
        self.assertAlmostEqual(p, pitch)
        self.assertAlmostEqual(r, roll)

    def testa(self):
        return self.test1([5,6,7], 0.2, 0.4, 0.6)
    
    def testb(self):
        return self.test1([5,-6,7], 0.42, -0.4, 0.6)
    
    def testc(self):
        return self.test1([-15,-6,7], -0.8, -0.4, 0.6)
    
    def testpi2(self):
        return self.test1([-15,-6,7], -0.8, pi2, 0)
    
    def testnpi2(self):
        return self.test1([-15,-6,7], -0.8, -pi2, 0)
    
class Test_specific_shape(unittest.TestCase):
    
    def test432(self):
        s0 = (4,3,2)
        size = 12
        Ar = np.arange(4*3*2)
        A = Ar.reshape(s0)
        Asp = operations3d.specific_shape(A, size)
        for i in range(size):
            i0 = i // 3
            for j in range(size):
                j0 = j // 4
                for k in range(size):
                    k0 = k // 6
                    self.assertEqual(Asp[i,j,k], A[i0,j0,k0])

class Test_resample(unittest.TestCase):
    
    def test432(self):
        s0 = (4,3,2)
        sizes = (8,9,6)
        Ar = np.arange(4*3*2)
        A = Ar.reshape(s0)
        Asp = operations3d.resample(A, sizes)
        for i in range(8):
            i0 = i // 2
            for j in range(9):
                j0 = j // 3
                for k in range(6):
                    k0 = k // 3
                    self.assertEqual(Asp[i,j,k], A[i0,j0,k0])

class Test_rectify(unittest.TestCase):
    
    def test432(self):
        s0 = (4,3,2)
        sizes = (8,9,6)
        (dI, dJ, dK) = (4,6,6)
        dside = 2
        Ar = np.arange(4*3*2)
        A = Ar.reshape(s0)
        Asp = operations3d.rectify(A, dI, dJ, dK, dside)
        self.assertEqual(Asp.shape, sizes)
        for i in range(8):
            i0 = i // 2
            for j in range(9):
                j0 = j // 3
                for k in range(6):
                    k0 = k // 3
                    self.assertEqual(Asp[i,j,k], A[i0,j0,k0])
