# Notes for setting up MLX90640 infrared sensors and Raspiberry Pi Zeros.


## Pi Zero Setup

Download and dd the image to an SD card.

```
sudo dd if=2021-05-07-raspios-buster-armhf-lite.img of=/dev/sdd bs=4M conv=fsync status=progress
```

### Boot Files

The following files on the boot partition need to be changed or created.

Enable SSH and dwc2.
```
touch boot_mount_point/ssh
echo 'dtoverlay=dwc2' >> boot_mount_point/config.txt
```

Edit `cmdline.txt` and insert `modules-load=dwc2,g_ether` right after
`rootwait`.

### Root Partition

You'll want to setup a usb network interface by editing
`root_mount_point/etc/network/interfaces.d/usb0`

```
allow-hotplug usb0
iface usb0 inet static
address 192.168.4.4
netmask 255.255.255.0
network 192.168.4.0
broadcast 192.168.4.255
gateway 192.168.4.3
```

Only way I could get the Pi Zero to add a route for the 192 network was by
adding the following /etc/rc.local.  I had zero luck with /etc/dhcpcd.confg

```
route add default gw 192.168.4.3
```

### Exit Speed Setup

```
sudo apt install git python3-pip
mkdir ~/git
cd ~/git
git clone https://github.com/djhedges/exit_speed.git
sudo pip3 install -r ~/git/exit_speed/requirements.txt
```

## Main Pi Host

On the Pi host that runs Exit Speed and is not connected to the tire infrared
sensors we'll want to also setup a usb0 network interface.

```
allow-hotplug usb0
iface usb0 inet static
address 192.168.4.3
netmask 255.255.255.0
network 192.168.4.0
broadcast 192.168.4.255
gateway 192.168.4.3
```

### NAT and IP Forwarding

```
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
iptables -A FORWARD -i usb0 -o wlan0 -m state \
  --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i wlan0 -o usb0 -j ACCEPT
sudo apt-get install iptables-persistent
```
