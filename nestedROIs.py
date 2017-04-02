__author__ = 'shahargino'


# noinspection PyPep8Naming,PyUnboundLocalVariable,PyArgumentList,PyUnusedLocal
def nestedROIs(roi1, roi2):

    x1 = roi1[0]
    y1 = roi1[1]
    w1 = roi1[2]
    h1 = roi1[3]

    x2 = roi2[0]
    y2 = roi2[1]
    w2 = roi2[2]
    h2 = roi2[3]

    return (x1 < x2 < x1 + w1) and (y1 < y2 < y1 + h1) or \
           (x2 < x1 < x2 + w2) and (y2 < y1 < y2 + h2)
