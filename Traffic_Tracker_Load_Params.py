__author__ = 'shahargino'

import cv2


# noinspection PyPep8Naming,PyUnboundLocalVariable,PyArgumentList,PyUnusedLocal
def Traffic_Tracker_Load_Params():

    algo_params = {'VJ': {},
                   'LKT': {}}

    # -----------------------------------------------------------------------------------------------------------------
    # LKT Parameters:
    algo_params['LKT']['max_points'] = 100   # Maximum number of interesting points
    algo_params['LKT']['min_points'] = 10    # Minimum number of interesting points
    algo_params['LKT']['velocity_thr'] = 1   # Velocity threshold (pixels-movement over 2 frames), features with a lower velocity will be dropped

    # Parameters for Shi-Tomasi corner detection:
    algo_params['LKT']['feature_params'] = dict(maxCorners=algo_params['LKT']['max_points'],  # Finds N strongest corners in the image
                                                qualityLevel=0.01,      # All corners below quality level [0,1] are rejected
                                                minDistance=5,          # Minimum possible Euclidean distance between the returned corners
                                                blockSize=3)            # Size of an average block for computing a derivative covariation matrix over each pixel neighborhood

    # Parameters for Lucas-Kanade optical flow:
    algo_params['LKT']['lk_params'] = dict(winSize=(15, 15),            # Size of the search window at each pyramid level
                                           maxLevel = 3,                # Use as many levels as pyramids have but no more than maxLevel
                                           criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    # -----------------------------------------------------------------------------------------------------------------
    # VJ Parameters:
    algo_params['VJ']['velocity_thr'] = 10   # Velocity threshold (pixels-movement over 2 frames), features with a lower velocity will be dropped
    algo_params['VJ']['area_thr'] = 1000     # Area threshold (pixels^2), features with a higher area different cannot match

    # Car dataset taken by Brad Philip and Paul Updike, California Institute of Technology SURF project for summer 2001.
    # 526 images of cars from the rear. 360 x 240 pixels. No scale normalisation. Jpeg format.
    # Quite a few repeat images. Taken of the freeways of southern California.
    algo_params['VJ']['VJ_Classifier'] = 'cars1.xml'

    algo_params['VJ']['cascade_params'] = dict(scaleFactor=1.01,       # Specifies how much the image size is reduced at each image scale
                                               minNeighbors=2,         # Specifies how many neighbors each candidate rectangle should have
                                               maxSize=(200, 200),     # Maximum possible object size, larger objects are ignored
                                               minSize=(50, 50))       # Minimum possible object size, smaller objects are ignored

    return algo_params
