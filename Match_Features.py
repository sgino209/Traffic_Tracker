__author__ = 'shahargino'

import numpy as np


# noinspection PyPep8Naming,PyUnboundLocalVariable,PyArgumentList,PyUnusedLocal
def Match_Features(set0, set1, minDistThr, minAreaThr):

    list0 = []
    list1 = []

    for a, b, w1, h1 in set0:
        for c, d, w0, h0 in set1:

            EucDist = ((a+w1/2) - (c+w0/2))**2 - ((b+h1/2) - (d+h0/2))**2
            AreaDist = np.abs(w0*h0 - w1*h1)

            if EucDist > 0:
                EucDist = np.sqrt(EucDist)

            if EucDist < minDistThr and AreaDist < minAreaThr:

                if not [a, b, w1, h1] in list0:
                    list0.append([a, b, w1, h1])

                if not [c, d, w0, h0] in list1:
                    list1.append([c, d, w0, h0])

    set0_out = np.array(list0)
    set1_out = np.array(list1)

    return set0_out, set1_out
