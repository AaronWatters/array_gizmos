

import numpy as np

def avg_subsample0(array2d, dI, dJ):
    """
    Subsample a 2d array with strides dI, dJ and return
    the average value in the subsample entries.
    The slow way for testing.
    """
    M, N = array2d.shape
    M1 = M // dI
    N1 = N // dJ
    result = np.zeros((M1, N1), dtype=array2d.dtype)
    for i in range(M1):
        for j in range(N1):
            result[i, j] = np.mean(array2d[i*dI:(i+1)*dI, j*dJ:(j+1)*dJ])
    return result

def avg_subsample(array2d, dI, dJ):
    """
    Subsample a 2d array with strides dI, dJ and return
    the average value in the subsample entries.
    The fast way using numpy fancy indexing.
    """
    M, N = array2d.shape
    M1 = M // dI
    N1 = N // dJ
    Mtrunc = M1 * dI
    Ntrunc = N1 * dJ
    array2dtrunc = array2d[:Mtrunc, :Ntrunc]
    blocks = array2dtrunc.reshape(M1, dI, N1, dJ)
    result = blocks.mean(axis=(1, 3))
    return result
