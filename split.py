import glob			# Getting files in a directory
import cv2			# Checking each individual frame for camera angle
import numpy as np  # Convolving frames
import time			# Execution timing

"""
This script was used for the NCAM070 in Newark, DE at the intersection of
W Main St and Trabant Student Center.

This special camera rotates horizontally between west, south, and east on some
regular interval. However, this interval cannot be guranteed to stay regular,
and so each frame of every downloaded buffer video must be placed in its
separate DIRECTION.avi video file, and sent to each respective cardinal
direction dynamically and programmatically.

*.ts video files are loaded from the buffer/ directory (that deldot.py
downloads to) and then in order, every video frame is scored, then sent to the
correct corresponding direction.

:author: James Villemarette (@jvillemare)
"""

ref_west = cv2.imread('reference/west.png', cv2.IMREAD_GRAYSCALE)
ref_south = cv2.imread('reference/south.png', cv2.IMREAD_GRAYSCALE)
ref_east = cv2.imread('reference/east.png', cv2.IMREAD_GRAYSCALE)

def convolve(frame):
	"""Drops resolution, converts to grayscale and returns it"""
	f = cv2.resize(frame, (128, 72), interpolation=cv2.INTER_AREA)
	return cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)

def score(f1, f2):
	"""Runs the absolute difference on two images, thresholds it, then sums
	the difference. The difference sum is then related to maximum possible
	value (128 wide * 72 high * 255 white), squared, and then returned."""
	diff = cv2.absdiff(f1, f2)
	_, diff = cv2.threshold(diff, 80, 255, cv2.THRESH_BINARY)
	num_diff = np.sum(diff)
	max = 2350080
	return ((max - num_diff)/max)**2

def west(frame):
	"""
	Get the probability of the frame being West Main Street.
	:returns: 0.0 (0%) to 1.0 (100%) likeliness.
	"""
	return score(ref_west, convolve(frame))

def south(frame):
	"""Get the probability of the frame being South College Avenue."""
	return score(ref_south, convolve(frame))

def east(frame):
	"""Get the probability of the frame being East Main Street."""
	return score(ref_east, convolve(frame))

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0) # only difference

if __name__ == "__main__":
	script_start = time.time()
	video_files = glob.glob("buffer/*.ts") # change me

	fps = 30
	fourcc = cv2.VideoWriter_fourcc(*'XVID')
	vid_west  = cv2.VideoWriter('other/west.avi', fourcc, fps, (1280, 720))
	vid_south = cv2.VideoWriter('other/south.avi', fourcc, fps, (1280, 720))
	vid_east  = cv2.VideoWriter('other/east.avi', fourcc, fps, (1280, 720))
	vw, vs, ve = 0, 0, 0

	i = 1
	l = len(video_files)
	#hitme = 25
	for vid in video_files:
		print('On video ' + vid + ' ' + str(i) + '/' + str(l) + \
		' (' + str(round((i/l)*100, 1)) + '%)', end=' ')
		start = time.time()
		cap = cv2.VideoCapture(vid)
		cap_i = 0
		cap_l = cap.get(cv2.CAP_PROP_FRAME_COUNT) # num of frames in vid
		cap_dropped = 0 # number of frames dropped
		while cap_i < cap_l: # go over every frame in video
			ret, frame = cap.read()
			if frame is None:
				print('On frame ' + str(cap_i) + '/' + str(cap_l) + ' and found None frame. Skipping...')
				break
			sm = softmax([west(frame), south(frame), east(frame)]) # compute softmax
			sm_i = list(sm).index(max(sm)) # get index of max val
			if sm[sm_i] > 0.38:
				if sm_i == 0: # west
					vid_west.write(frame)
					vw += 1
				elif sm_i == 1: # south
					vid_south.write(frame)
					vs += 1
				elif sm_i == 2: # east
					vid_east.write(frame)
					ve += 1
			else:
				cap_dropped += 1
				pass # reject low confidence frames. 0.33 is lowest probability
			cap_i += 1
		# helpful print info
		i += 1
		end = time.time()
		duration = end - start
		print('\tTook ' + str(round(duration, 1)) + ' seconds, or ' + \
		str(round(cap_i/duration, 1)) + ' fps.\tDropped ' + \
		str(cap_dropped) + '/' + str(cap_i) + ' low confidence frames.')
		#if i == hitme:
		#	break
	# more helpful print info
	script_end = time.time()
	script_duration = script_end - script_start
	print('Done, took ' + str(round(script_duration, 1)) + ' seconds')
	for direction, frame_count in [('west', vw), ('south', vs), ('east', ve)]:
		print('Video ' + direction + ' frame count: ' + str(frame_count) + \
		' (or ' + str(round(frame_count/fps, 1)) + ' seconds total)')

# ===
