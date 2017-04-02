__author__ = 'shahargino'

# noinspection PyPep8Naming,PyUnboundLocalVariable,PyArgumentList,PyUnusedLocal
def IsInROI(x, y, ROI):

    return (x > ROI[0]) and (x < ROI[0] + ROI[2]) and \
           (y > ROI[1]) and (y < ROI[1] + ROI[3])
