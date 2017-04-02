#!/usr/bin/env python
#   ____ _ _          ____            _             _
#  / ___(_) |_ _   _ / ___|___  _ __ | |_ _ __ ___ | |  Hackathon InVent 30.03.17
# | |   | | __| | | | |   / _ \| '_ \| __| '__/ _ \| |  ComputerVision algo for
# | |___| | |_| |_| | |__| (_) | | | | |_| | | (_) | |  accidents detection (vehicles)
#  \____|_|\__|\__, |\____\___/|_| |_|\__|_|  \___/|_|
#              |___/
# (c) Shahar Gino, April-2017, sgino209@gmail.com

__author__ = 'shahargino'

import cv2
import sys
import getopt
from time import time
from Report_Event import Report_Event
from Traffic_Tracker import Traffic_Tracker
from Traffic_Tracker_Load_Params import Traffic_Tracker_Load_Params

class Struct:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

# ---------------------------------------------------------------------------------------------------------------
def usage():
    print 'city_control.py -f [video_source]'
    print ''
    print 'Optional flags: --camera_id [CameraID]'
    print '                --algo params [Computer-Vision Parameters]'
    print '                --scale [Scale image (<=1), for a better performance]'
    print '                --out_duration [duration of output video, in seconds]'
    print '                --post_alerts_srv [POST server address]'
    print '                --post_alerts_port [POST server port]'
    print '                --post_ftp_uname [FTP user name]'
    print '                --post_ftp_pwd [FTP password]'
    print '                --post_ftp_cwd [FTP destination path]'
    print '                --post_alerts_dis // Disable posting alerts to server'
    print '                --out_video       // Saving location, use "None" to bypass (default supported)'
    print '                --get_ROI_en      // Get ROI from user'
    print '                --debug_en        // Verbose on/off - prints ROI movement'
    print '                --skip_tracker    // Skip Tracker core and submit dummy data to POST server'
    print '                --inter_frames_alerts [minimal frames between alerts]'
    print ''
    print 'Usage examples:'
    print '(-) city_control.py --skip_tracker'
    print '(-) city_control.py -f ../Input/Sample6.mp4 --debug_en --post_alerts_dis'
    print '(-) city_control.py -f ../Input/Sample6.mp4'

# ---------------------------------------------------------------------------------------------------------------
def main(argv):
    default_in_video = '/Users/shahargino/Documents/ImageProcessing/Hackathon_InVent_300317/Input/Kfir2.mp4'

    # Default parameters:
    args = Struct(
        in_video=default_in_video,
        camera_id=1,
        algo_params = Traffic_Tracker_Load_Params(),  # Load Computer-Vision parameters
        scale = 2,
        out_duration = 10,
        out_video = default_in_video.replace("Input", "Output").replace("mp4", "mov"),
        get_ROI_en = False,
        debug_en = False,
        skip_tracker = False,
        post_alerts_srv = "http://balipizza.co.il/citycontrol/Server/event.php",
        post_alerts_port=80,
        post_ftp_uname="balipizza",
        post_ftp_passwd="78963",
        post_ftp_cwd="/domains/balipizza.co.il/public_html/citycontrol/Records/",
        post_alerts_dis = False,
        inter_frames_alerts = 350
    )

    # -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- ..
    # User-Arguments parameters (overrides Defaults):
    try:
        opts, user_args = getopt.getopt(argv, "hf:",
                                        ["camera_id=", "algo_params=", "scale=", "out_duration=",
                                         "out_video=", "post_alerts_srv=", "post_alerts_port=",
                                         "post_ftp_uname=", "post_ftp_passwd=", "post_ftp_cwd=",
                                         "inter_frames_alerts="
                                         "get_ROI_en", "debug_en", "skip_tracker", "post_alerts_dis"])
        for opt, user_arg in opts:
            if opt == '-h':
                usage()
                sys.exit()
            elif opt in "-f":
                args.in_video = user_arg
                args.out_video = user_arg.replace("Input", "Output").replace("mp4", "mov")
            elif opt in "--camera_id":
                args.camera_id = user_arg
            elif opt in "--inter_frames_alerts":
                args.inter_frames_alerts = user_arg
            elif opt in "--algo_params":
                args.algo_params = user_arg
            elif opt in "--scale":
                args.scale = user_arg
            elif opt in "--out_duration":
                args.out_duration = user_arg
            elif opt in "--out_video":
                args.out_video = user_arg
            elif opt in "--post_alerts_srv":
                args.post_alerts_srv = user_arg
            elif opt in "--post_alerts_port":
                args.post_alerts_port = user_arg
            elif opt in "--post_ftp_uname":
                args.post_ftp_uname = user_arg
            elif opt in "--post_ftp_passwd":
                args.post_ftp_passwd = user_arg
            elif opt in "--post_ftp_cwd":
                args.post_ftp_cwd = user_arg
            elif opt in "--get_ROI_en":
                args.get_ROI_en = True
            elif opt in "--debug_en":
                args.debug_en = True
            elif opt in "--skip_tracker":
                args.skip_tracker = True
            elif opt in "--post_alerts_dis":
                args.post_alerts_dis = True

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- ..
    # Adaptive paremetrization:
    if args.scale == 2:
        args.algo_params['LKT']['lk_params'] = dict(winSize=(5, 5),  # Size of the search window at each pyramid level
                                                    maxLevel=3,      # Use as many levels as pyramids have but no more than maxLevel
                                                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

        args.algo_params['VJ']['cascade_params'] = dict(scaleFactor=1.01,    # Specifies how much the image size is reduced at each image scale
                                                        minNeighbors=2,      # Specifies how many neighbors each candidate rectangle should have
                                                        maxSize=(300, 300),  # Maximum possible object size, larger objects are ignored
                                                        minSize=(5, 5))      # Minimum possible object size, smaller objects are ignored

    # -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- ..

    res = {'alerts': {}}

    if not args.skip_tracker:

        # Call Trackers (VJ and LKT):
        res = Traffic_Tracker(args.in_video,           # Video source
                              args.algo_params,        # Computer-Vision Parameters
                              args.scale,              # Scale image (<=1), for a better performance
                              args.get_ROI_en,         # Get ROI from user
                              args.out_duration,       # Duration of output video, in seconds
                              args.out_video,          # Saving location, use "None" to bypass
                              args.post_alerts_dis,    # Disable posting alerts to server
                              args.post_alerts_srv,
                              args.post_alerts_port,
                              args.post_ftp_uname,
                              args.post_ftp_passwd,
                              args.post_ftp_cwd,
                              args.camera_id,
                              args.inter_frames_alerts,
                              args.debug_en)           # Verbose on/off - prints ROI movement

    # -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- .. -- ..
    # Event logging:
    if args.skip_tracker:

        res = {'alerts': {}}
        res['alerts'][0] = {'alType': 'Accident',
                            'alTime': 'frame 17',
                            'alX': 37,
                            'alY': 21}

        if not args.post_alerts_dis:

            Report_Event(args.camera_id,
                     args.out_video,
                     args.out_duration,
                     res['alerts'][0],
                     args.post_alerts_srv,
                     args.post_alerts_port,
                     args.post_ftp_uname,
                     args.post_ftp_passwd,
                     args.post_ftp_cwd,
                     args.skip_tracker,
                     args.debug_en)

    print(args.in_video + ' Done!')

# ---------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    t0 = time()
    print 'Start'

    main(sys.argv[1:])

    t1 = time()
    t_elapsed_sec = t1 - t0
    print('Done! (%.2f sec)' % t_elapsed_sec)
