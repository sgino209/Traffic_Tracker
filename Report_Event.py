__author__ = 'shahargino'

from httplib import HTTPConnection
from ftplib import FTP
from sys import platform
from subprocess import call


# noinspection PyPep8Naming,PyUnboundLocalVariable,PyArgumentList,PyUnusedLocal
def Report_Event(camera_id, out_video, out_duration, value,
                 post_alerts_srv, post_alerts_port, post_ftp_uname, post_ftp_passwd, post_ftp_cwd, skip_tracker, debug_en):

    # POST alert to server
    def printText(txt):
        lines = txt.split('\n')
        for line in lines:
            print line.strip()

    short_fname = out_video.split('/')[-1]
    if platform == "linux2":
        call(['ffmpeg', 'i ' + out_video, 'filter:v "setpts=12.0*PTS" ' + out_video.replace("mov", "mp4")])

    if platform == "linux2" or skip_tracker:
        short_fname = short_fname.replace("mov", "mp4")

    host_server = post_alerts_srv.split('/')[2]
    ftp_server = post_alerts_srv.split('/')[2]

    print ('Results --> %s' % out_video)

    if debug_en:
        print "Sending Video result over FTP: %s --> %s" % (short_fname, ftp_server)

    if not skip_tracker:
        session = FTP(ftp_server, post_ftp_uname, post_ftp_passwd)
        session.cwd(post_ftp_cwd)
        file_h = open(out_video, 'rb')  # file to send
        session.storbinary('STOR %s' % short_fname, file_h)  # send the file
        file_h.close()  # close file and FTP
        session.quit()

    httpServ = HTTPConnection(host_server, post_alerts_port)
    httpServ.connect()

    quote = "CamID=%s" % camera_id + "&" + \
            "Duration=%s" % out_duration + "&" + \
            "FileURL=%s" % short_fname + "&" + \
            "EventType=%s" % value['alType'] + "&" + \
            "EventROI=[%d,%d]" % (value['alX'], value['alY'])

    if debug_en:
        print "Sending Request to %s: %s" % (post_alerts_srv, quote)

    # specify we're sending parameters that are url encoded
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    # send out the POST request
    httpServ.request('POST', post_alerts_srv, quote, headers)

    response = httpServ.getresponse()
    print "Output from %s:" % post_alerts_srv
    printText(response.read())

    httpServ.close()
