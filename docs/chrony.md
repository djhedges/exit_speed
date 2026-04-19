This is to perfer the GPS time and avoid large difts when the pi is off for too long.

```
sudo apt install chrony pps-tools
```

Add the following to `/etc/chrony/chrony.conf`.
```
# Get time from GPSD via Shared Memory (SHM)
refclock SHM 0 poll 2 refid GPS precision 1e-1 offset 0.125 delay 0.2 prefer trust

# If your GPS has a PPS pin connected to a GPIO:
# refclock PPS /dev/pps0 lock GPS refid PPS

# Allow Chrony to 'step' the clock immediately if the offset is large
makestep 1 -1
```

You should see `#*` and not `#?` after 10 seconds.
```
$ chronyc sources -v

  .-- Source mode  '^' = server, '=' = peer, '#' = local clock.
 / .- Source state '*' = current best, '+' = combined, '-' = not combined,
| /             'x' = may be in error, '~' = too variable, '?' = unusable.
||                                                 .- xxxx [ yyyy ] +/- zzzz
||      Reachability register (octal) -.           |  xxxx = adjusted offset,
||      Log2(Polling interval) --.      |          |  yyyy = measured offset,
||                                \     |          |  zzzz = estimated error.
||                                 |    |           \
MS Name/IP address         Stratum Poll Reach LastRx Last sample               
===============================================================================
#* GPS                           0   2   377     4  -1132us[-1305us] +/-  200ms
```
