import cv2 # for opencv
import pyttsx3 # to make baseline image work
import threading
import time
import datetime
import smtplib # for sending emails
from email.message import EmailMessage # for dynamic email content

# --- Initialize variables ---
initial_frame = None
status_list = [None,None]
video = cv2.VideoCapture(0) # Creative the VideoCapture object

# Recording video
frame_rate = 20
frame_size = (int(video.get(3)), int(video.get(4))) # width and height
fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Video format (4 character code)
# output = cv2.VideoWriter('video.mp4', fourcc, frame_rate, frame_size) # Output stream

start_recording = False
recording_started_time = None
intruder_left_time = None
timer_started = False
recording_buffer_seconds = 3
maximum_recording_seconds = 26 # added 5 second buffer

# A must for baseline image to work. Do not understand why, but look into later
engine = pyttsx3.init()

# # Email
# send_email_alert = False
# sender_add='<email>' # store sender's mail id; need to add email
# receiver_add='<email>' # store receiver's mail id; need to add email
# password='<password>' # store password to log in; need to add password

# --- While webcam is on ---
while True:
  check, frame = video.read()
  status = 0

  # Gray conversion
  gray_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

  # Noise reduction (smoothing)
  blur_frame = cv2.GaussianBlur(gray_frame,(25,25),0)

  # First captured frame is the  baseline image
  if initial_frame is None:
    initial_frame = blur_frame
    continue

  # Difference between baseline and new (current) frame
  delta_frame = cv2.absdiff(initial_frame,blur_frame)
  
  # 2nd param = threshold that determines if pixel should be black or white
  threshold = cv2.threshold(delta_frame, 70, 255, cv2.THRESH_BINARY)[1]
  
  # Identify all the contours in the image
  # 3 params: (a) image, (b) contour retrieval mode, (c) contour approximation method
  (contours,_) = cv2.findContours(threshold,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

  for c in contours:
    # Filter out small contours
    if cv2.contourArea(c) < 5000:
      continue
    status = 1
    a = cv2.contourArea(c)
    (x, y, w, h) = cv2.boundingRect(c)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 1)
  
  # Add contours larger than a certain size to status_list
  status_list.append(status)
	
  # Identifies intruder(s)
  if status_list[-1] >= 1:
    if status_list[-2] == 0:
      print("New intruder!")
      # Already started recording, turn off timer_started
      if start_recording:
        # Reset time if intruder was in the frame for < 5 seconds
        # if time.time() - recording_started_time <= maximum_recording_seconds:
        timer_started = False
      # Did not yet start recording, then record
      else:
        start_recording = True
        # Stringify the datetime for recording filename
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        output = cv2.VideoWriter(f'{current_time}.mp4', fourcc, frame_rate, frame_size) # Output stream
        recording_started_time = time.time()
        print("Started recording!")
  elif start_recording: # If we previously detected intruder, but not currently
    # Timer started
    if timer_started:
      # Check if intruder left the scene
      if time.time() - intruder_left_time > recording_buffer_seconds:
        start_recording = False
        timer_started = False
        output.release() # save video
        print("Recording stopped: intruder left 3 seconds ago")
        send_email_alert = True
    # Start timer since intruder left screen
    else:
      timer_started = True
      intruder_left_time = time.time()

  if start_recording:
    output.write(frame) # Write frame to output video stream
    # If started recording, stop recording video for 20 seconds max
    if time.time() - recording_started_time > maximum_recording_seconds:
      start_recording = False
      timer_started = False
      output.release() # save video
      print("Recording stopped: 20 seconds limit")
      send_email_alert = True
    
  #   # Comment out this section to enable email notification 
  # if send_email_alert:
  #   # Create the SMTP server object by giving SMPT server address and port number
  #   smtp_server=smtplib.SMTP("smtp.gmail.com",587)
  #   smtp_server.ehlo() # Set the ESMTP protocol
  #   smtp_server.starttls() # Set up to TLS connection
  #   smtp_server.ehlo() # Cal the ehlo() again as encryption happens on calling startttls()
  #   smtp_server.login(sender_add,password) # log into email id

  #   # Email body
  #   email_body_msg = "This is an intruder alert! Intruder appeared at " + str(current_time) + "."
  #   email_subject_msg = str(current_time)

  #   # Create a text/plain message body
  #   msg = EmailMessage()
  #   msg.set_content(email_body_msg)
    
  #   # Email 'headers'
  #   msg['Subject'] = f'Notification: Intruder alert - {email_subject_msg}'
  #   msg['From'] = sender_add
  #   msg['To'] = receiver_add

  #   # Send mail by specifying the from and to address and the message 
  #   smtp_server.sendmail(sender_add,receiver_add,msg.as_string())
  #   print('Successfully sent mail') # Print a message when sending the mail
  #   smtp_server.quit() # Terminate the server

  #   send_email_alert = False

  cv2.imshow("Baseline Frame",initial_frame)
  cv2.imshow("gray_frame Frame",gray_frame)
  cv2.imshow("Delta Frame",delta_frame)
  cv2.imshow("Threshold Frame",threshold)
  cv2.imshow("Color Frame",frame)

  # Quit when 'q' is pressed
  if cv2.waitKey(1) == ord('q'):
    break

# --- Stop webcam ---
# After the loop, stop recording video, release engine and video object
engine.stop()
video.release()
output.release()

# Destroy all windows
cv2.destroyAllWindows