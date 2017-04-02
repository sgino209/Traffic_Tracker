__author__ = 'shahargino'

# References:  (1) http://docs.opencv.org/2.4/modules/imgproc/doc/feature_detection.html
#              (2) http://docs.opencv.org/2.4/modules/video/doc/motion_analysis_and_object_tracking.html

import cv2
import numpy as np
from sys import platform
from Match_Features import Match_Features
from nestedROIs import nestedROIs
from get_ROI import get_ROI
from IsInROI import IsInROI
from subprocess import call
from Report_Event import Report_Event
from datetime import datetime
if platform == 'darwin':
    from common import draw_str

# noinspection PyPep8Naming,PyUnboundLocalVariable,PyArgumentList,PyUnusedLocal
def Traffic_Tracker(src, algo_params, scale, get_ROI_en, out_duration, out_video, post_alerts_dis,
                    post_alerts_srv, post_alerts_port, post_ftp_uname, post_ftp_passwd, post_ftp_cwd,
                    camera_id, inter_frames_alerts, debug_verbose_en):

    res = {'alerts': {}}
    if platform == 'darwin':
        line_type = cv2.LINE_AA
    else:
        line_type = cv2.CV_AA

    # ------------------------------------ I N I T -------------------------------------------------

    # Obtain video object:
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print("Error loading source file: " + src)
        exit(1)

    # Retrieve intrinsic video parameters:
    w,h = 0,0
    if platform == 'linux2':
        fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
        w = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH) * scale)
        h = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT) * scale)
        framesNum = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
    else:
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * scale)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * scale)
        framesNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = []
    if platform == 'darwin':
        fourcc = cv2.VideoWriter_fourcc('S', 'V', 'Q', '3')  # MacOs
    elif platform == 'linux2':
        fourcc = cv2.cv.CV_FOURCC(*'XVID')                   # Linux
    else:
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))           # Windows

    # Output Video Init:
    out_video_clone = out_video.replace('.','_alert' + '_' + datetime.now().strftime("%d%m%y_%H%M%S") + '.')
    out_clone_timer = 0
    out_clone_pending = False
    if out_video != "None":
        out = cv2.VideoWriter(out_video, fourcc, fps, (w, h))
        out_clone = cv2.VideoWriter(out_video_clone, fourcc, fps, (w, h))

    # Create a colors vector (random) for later markings:
    color = np.random.randint(0, 255, (algo_params['LKT']['max_points'], 3))

    # Load VJ database (cascade XML):
    face_cascade = cv2.CascadeClassifier(algo_params['VJ']['VJ_Classifier'])

    # -------------------------- P R E - P R O C E S S i N G ---------------------------------------

    # Take first frame, select ROI and find corners in it:
    frmIndex = 1
    ret, old_frame_pre = cap.read()
    if not ret:
        print("Error loading first frame")
        exit(1)

    if scale != 1:
        old_frame = cv2.resize(old_frame_pre, (0, 0), fx=scale, fy=scale)
    else:
        old_frame = old_frame_pre

    ROI = [0, 0, w, h]
    if get_ROI_en:
        ROI = get_ROI(old_frame, debug_verbose_en)  # ROI = [upper-left point (x,y), width, height]

    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **algo_params['LKT']['feature_params'])

    cars_prev = face_cascade.detectMultiScale(old_frame, **algo_params['VJ']['cascade_params'])
    # cars_prev = cv2.groupRectangles(np.array(cars_prev_pre).tolist(), 3, 0.2)

    # Create a mask image for drawing purposes:
    mask = np.zeros_like(old_frame)

    # --------------------------- M A I N - P R O C E S S I N G ------------------------------------

    carsAvg = 0
    velAvg = 0
    lastAlertFrm = -1000
    value = {}
    while 1:

        # Read next frame:
        ret, frame_pre = cap.read()
        if not ret:
            print("Error loading frame %d" % frmIndex)
            break
        frmIndex += 1

        # Scale support (performance-wise):
        if scale != 1:
            frame = cv2.resize(frame_pre, (0, 0), fx=scale, fy=scale)
        else:
            frame = frame_pre

        # - - - - - - - - - - - - - - - - - - L K T - R e l a t e d - - - - - - - - - - - - - - - - - - - - - - - - -

        # Color Space Conversion (CVC):
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # LKT: Calculate optical flow + "good points" selection:
        p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **algo_params['LKT']['lk_params'])
        good_new_LKT = p1[st == 1]
        good_old_LKT = p0[st == 1]

        # LKT: Draw the tracks:
        LKT_velAvg = 0
        LKT_velCnt = 0
        for i, (new, old) in enumerate(zip(good_new_LKT, good_old_LKT)):

            a, b = new.ravel()
            c, d = old.ravel()

            vx = abs(a - c)
            vy = abs(b - d)

            velocity = np.sqrt(vx ** 2 + vy ** 2)

            if velocity > algo_params['LKT']['velocity_thr'] and IsInROI(a, b, ROI):

                if debug_verbose_en:
                    cv2.circle(frame, (a, b), 5, color[i].tolist(), -1)
                    LKT_velAvg = (LKT_velAvg * LKT_velCnt + velocity) / (LKT_velCnt + 1)
                    LKT_velCnt += 1
            else:
                st[i] = 0

            if debug_verbose_en:
                print ('LKT: Frame %d - feature #%d: (x,y)=(%.2f,%.2f) velocity=%.2f' % (frmIndex, i, a, b, velocity))

        # Re-Select good points:
        good_new_LKT = p1[st == 1]
        good_old_LKT = p0[st == 1]

        # Update features:
        if len(good_new_LKT) < algo_params['LKT']['min_points']:
            p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **algo_params['LKT']['feature_params'])
        else:
            p0 = good_new_LKT.reshape(-1, 1, 2)

        # - - - - - - - - - - - - - - - - - - - V J - R e l a t e d - - - - - - - - - - - - - - - - - - - - - - - - -

        # VJ: Car detection + matching over 2 sequential frames (create a synced order)
        cars = face_cascade.detectMultiScale(frame, **algo_params['VJ']['cascade_params'])
        good_new_VJ, good_old_VJ = Match_Features(cars, cars_prev, algo_params['VJ']['velocity_thr'], algo_params['VJ']['area_thr'])

        ROIs = []
        cars_num = 0
        VJ_velAvg = 0
        VJ_velCnt = 0
        for i, (new, old) in enumerate(zip(good_new_VJ, good_old_VJ)):

            a, b, w1, h1 = new.ravel()
            c, d, w0, h0 = old.ravel()

            vx = abs((a + w1 / 2) - (c + w0 / 2))
            vy = abs((b + h1 / 2) - (d + h0 / 2))

            velocity = np.sqrt(vx ** 2 + vy ** 2)

            # Is the VJ moving and in user's ROI?
            if velocity > algo_params['VJ']['velocity_thr'] and IsInROI(a, b, ROI):

                # Does the VJ contains any LKT feature?
                for x, y in good_new_LKT:
                    if IsInROI(x, y, new):

                        # Mark ROIs:
                        x = int(x)
                        y = int(y)
                        cv2.rectangle(frame, (x - w1/2, y-h1/2), (x + w1/2, y + h1/2), color=(0,255,0), thickness=2)
                        cv2.putText(frame, '[%d]=%.2f' % (i,velocity), (x - w1 / 2, y - h1 / 2 - 5),
                                    cv2.FONT_HERSHEY_PLAIN, 1.0, (0,255,0), lineType=line_type)

                        # Register the VJ rectangle as an ROI:
                        ROIs.append(new)
                        break

                if debug_verbose_en:
                    cv2.rectangle(frame, (a, b), (a + w1, b + h1), color=(255,0,0), thickness=1)
                    cv2.putText(frame, "%d" % i, (a + w1/2, b-5),
                                cv2.FONT_HERSHEY_PLAIN, 1.0, (255,0,0), lineType=line_type)

                cars_num += 1
                VJ_velAvg = (VJ_velAvg * VJ_velCnt + velocity) / (VJ_velCnt + 1)
                VJ_velCnt += 1

            if debug_verbose_en:
                print ('VJ: Frame %d - feature #%d: (x,y,w,h)=(%d,%d,%d,%d) velocity=%.2f' % (frmIndex, i, a, b, w1, h1, velocity))

        # - - - - - - - - - - - - - V J / L K T - I n t e g r a t i o n  +  M i s c. - - - - - - - - - - - - - - - -

        # Alerts detection:
        for i1,roi1 in enumerate(ROIs):
            for i2,roi2 in enumerate(ROIs):

                if i1 > i2:

                    d_ = np.sqrt((roi1[0]-roi2[0])**2 + (roi1[1]-roi2[1])**2)
                    w_ = min(roi1[2],roi2[2])
                    h_ = min(roi1[3],roi2[3])

                    if (w_/2 < d_ < w_) and not nestedROIs(roi1,roi2):
                        a = min(roi1[0],roi2[0])
                        b = min(roi1[1],roi2[1])

                        if (frmIndex - lastAlertFrm) > inter_frames_alerts:
                            value = {'alType': 'Accident',
                                     'alTime': 'frame %s' % frmIndex,
                                     'alX': a+w_/2,
                                     'alY': b+h_/2}

                            res['alerts'][str(len(res['alerts']))] = value

                            if not post_alerts_dis:

                                out_clone_timer = 50
                                out_clone_pending = True

                            if debug_verbose_en:
                                print 'Alert detected: (x,y)=(%d,%d)' % (a+w/2,b+h/2)

                        lastAlertFrm = frmIndex

                    if debug_verbose_en:
                        print 'ROI #%d --> (%d,%d,%d,%d)' % (i1,roi1[0],roi1[1],roi1[2],roi1[3])

        # Draw:
        for key, value in res['alerts'].iteritems():
            a = value['alX']
            b = value['alY']
            w_ = 70
            h_ = 70
            cv2.rectangle(frame, (a, b), (a + w_, b + h_), color=(0,0,255), thickness=4)
            cv2.putText(frame, "ALERT #%s" % key, (a, b-5),
                        cv2.FONT_HERSHEY_PLAIN, 1.0, (0,0,255), lineType=line_type)

        img = cv2.add(frame, mask)
        if platform == 'darwin':
            draw_str(img, (20, 20), 'Frame #%d , LKT=%d , VJ=%d , Cars=%d , Alerts=%d' %
                     (frmIndex, len(good_new_LKT), cars_num, len(ROIs), len(res['alerts'])))
            draw_str(img, (20, 40), 'Press \'q\' to quit')
            cv2.imshow('frame', img)

        # Save frame:
        if out_video != "None":
            out.write(img)
            out_clone.write(img)

        # Quit if user pressed 'q' or if no more frames:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if src > 0 and frmIndex >= framesNum:
            break

        # Update the previous frame:
        old_gray = frame_gray.copy()

        # Update the previous cars:
        cars_prev = cars

        # Update statistics:
        carsAvg_LKT = (carsAvg * (frmIndex - 1) + len(good_new_LKT)) / frmIndex
        carsAvg_VJ = (carsAvg * (frmIndex - 1) + cars_num) / frmIndex
        carsAvg = (carsAvg_LKT + carsAvg_VJ) / 2

        velAvg_LKT = (velAvg * (frmIndex - 1) + LKT_velAvg) / frmIndex
        velAvg_VJ = (velAvg * (frmIndex - 1) + VJ_velAvg) / frmIndex
        velAvg = (velAvg_LKT + velAvg_VJ) / 2

        # Alerts Reporting:
        if out_clone_pending:

            if out_clone_timer > 0:

                out_clone_timer = - 1

            else:

                if out_video != "None":
                    out_clone.release()

                Report_Event(camera_id,
                             out_video_clone,
                             out_duration,
                             value,
                             post_alerts_srv,
                             post_alerts_port,
                             post_ftp_uname,
                             post_ftp_passwd,
                             post_ftp_cwd,
                             debug_verbose_en)

                # Reopen clone video (for future alert):
                out_video_clone = out_video.replace('.', '_alert' + '_' + datetime.now().strftime("%d%m%y_%H%M%S") + '.')
                out_clone = cv2.VideoWriter(out_video_clone, fourcc, fps, (w, h))

                out_clone_pending = False

    # ----------------------------------------------------------------------------------------------

    # Done:
    cap.release()
    if out_video != "None":
        print ('Results --> %s' % out_video)
        out.release()
        out_clone.release()

    if platform == 'linux2':
        call(['ffmpeg', 'i '+ out_video,'filter:v "setpts=12.0*PTS" ' + out_video.replace("mov","mp4")])

    cv2.destroyAllWindows()

    res['carsAvg'] = str(carsAvg)
    res['velAvg'] = str(format(velAvg, '.2f'))

    return res
