#!/bin/bash

source /usr/share/seecr-tools/functions.d/network

if ! lsmod | grep "^dummy" >/dev/null; then
    modprobe dummy numdummies=8
fi

TEMP=$(getopt \
    --options "" \
    --long device::,ip:: \
    -n "$0" -- "$@")

eval set -- "$TEMP"

DEVICE=$(network_get_nic)
while true ; do
    case "$1" in
        --device)
            case "$2" in
                "") show_usage ; exit 1 ;;
                *) DEVICE=$2 ; shift 2 ;;
            esac ;;
        --ip)
            case "$2" in
                "") show_usage ; exit 1 ;;
                *) IPADDR=$2 ; shift 2;;
            esac ;;
        --) shift ; break ;;
        *) echo "Unknown option specified." ; exit 1 ;;
    esac
done


SRCIP=$(ip addr show ${DEVICE}| head -n 3 | tail -n 1 | awk '{print $2}' | awk -F/ '{print $1}')
VHID=$(echo "${IPADDR}" | awk -F'.' '{print $NF}')
FREE_DUMMY=$(ip link | grep dummy | grep DOWN | head -n 1 | awk '{print $2}' | tr -d :)
if [ -z "${FREE_DUMMY}" ]; then
    echo "No free dummy device found!"
    exit 1
fi
SHAREDPASSWORD="3f09e646d"

export FREE_DUMMY
function cleanup_dummy {
    echo "releasing ${FREE_DUMMY}"
    ifconfig ${FREE_DUMMY} down
}

trap cleanup_dummy SIGTERM SIGINT
ifconfig ${FREE_DUMMY} -arp ${IPADDR} netmask 255.255.255.255

exec ucarp \
    --interface=${DEVICE} \
    --vhid=${VHID} \
    --srcip=${SRCIP} \
    --addr=${IPADDR} \
    --pass=${SHAREDPASSWORD} &

PID=$!
wait ${PID}
