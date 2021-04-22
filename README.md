# VIP: FLIE Spring 2021 Repository

This repository is for VIP: FLIE with Professor Barner for the Spring 2021
semester.

## Notes

 - DelDOT is the State of Delaware's Department of Transportation.
 - DelDOT runs several publicly viewable traffic cameras in the state.
 - `NCAM070` was chosen as it monitors an area with heavy pedestrian traffic in
 front of the Trabant Student Center at the University of Delaware (UD).
 - Video files from the DelDOT camera were downloaded using `deldot.py` from
 `NCAM070` over the course of several days at different intervals.
 - Video files are saved to a directory created at runtime, `buffer/`
 - `split.py` combines all these 10 to 20 second `.ts` video clips there were
 downloaded into big metafiles, `west.avi`, `south.avi`, and `east.avi`, as the
 `NCAM070` camera faces different cardinal directions at different times of day.
 - Social distancing and facemask analysis are then run on these `west.avi`
 cardinal direction videos.
 - Other files to be committed later.
