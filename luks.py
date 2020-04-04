#!/usr/bin/env python3

import os
import sys
import subprocess
import getpass

help = """
Help example:
  luks.py [op_command] [arguments]
Opperation commands [op_command]:
  create [path_to_storage_file] [mount_storage_name] [storage_size_in_GB] [raid_parts_count]
  open [path_to_storage_file] [mount_storage_name] [raid_parts_count]
  close [mount_storage_name]
"""

password = ""

def make_storage(file_path, size):
  if not os.path.exists(file_path):
    os.system("dd if=/dev/zero of=%s bs=1G count=%d" % (file_path, size))

def open_mapper(path, name):
  if os.path.exists(path):
    sp = subprocess.Popen(["cryptsetup open %s %s" % (path, name)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, text=True)
    stdout, stderr = sp.communicate(input="%s\n" % password)

def close_mapper(name):
  if os.path.exists("/dev/mapper/%s" % name):
    os.system("cryptsetup close %s" % name)

def create_luks():
  if len(sys.argv) != 6:
    print("Error: Wrong arguments count")
    exit(help)

  path_to_storage = str(sys.argv[2])
  storage_name = str(sys.argv[3])
  size_of_storage = int(sys.argv[4])
  raid_parts = int(sys.argv[5])

  global password
  password = getpass.getpass("Enter password to a storage container:", sys.stdout)

  if raid_parts <= 1:
    make_storage(path_to_storage, size_of_storage)
    sp = subprocess.Popen(["cryptsetup luksFormat %s" % path_to_storage], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, text=True)
    stdout, stderr = sp.communicate(input="%s\n%s\n" % (password, password))
    open_mapper(path_to_storage, storage_name)
    if os.path.exists("/dev/mapper/%s" % storage_name):
      os.system("mkfs -t ext4 /dev/mapper/%s" % storage_name)
      close_mapper(storage_name)
  else:
    raid_files = ""
    for i in range(0, raid_parts):
      raid_path_to_storage = "%s%d" % (path_to_storage, i)
      raid_storage_name = "%s%d" % (storage_name, i)
      raid_files += "/dev/mapper/" + raid_storage_name + " "
      make_storage(raid_path_to_storage, size_of_storage)
      sp = subprocess.Popen(["cryptsetup luksFormat %s" % raid_path_to_storage], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, text=True)
      stdout, stderr = sp.communicate(input="%s\n%s\n" % (password, password))
      open_mapper(raid_path_to_storage, raid_storage_name)

    os.system("mdadm --create --verbose /dev/md/%s --level=stripe --raid-devices=%d %s" % (storage_name, raid_parts, raid_files))
    os.system("mkfs -t ext4 /dev/md/%s" % storage_name)

    if os.path.exists("/dev/md/%s" % storage_name):
      os.system("mdadm --stop --verbose /dev/md/%s" % storage_name)
    
    for i in range(0, raid_parts):
      raid_storage_name = "%s%d" % (storage_name, i)
      close_mapper(raid_storage_name)

def open_luks():
  if len(sys.argv) != 5:
    print("Error: Wrong arguments count")
    exit(help)

  path_to_storage = str(sys.argv[2])
  storage_name = str(sys.argv[3])
  raid_parts = int(sys.argv[4])

  global password
  password = getpass.getpass("Enter password to a storage container:", sys.stdout)

  if raid_parts <= 1:
    open_mapper(path_to_storage, storage_name)
    if os.path.exists("/dev/mapper/%s" % storage_name):
      os.system("mkdir -p /run/media/%s/%s" % (os.getlogin(), storage_name))
      os.system("mount -o rw,user /dev/mapper/%s /run/media/%s/%s" % (storage_name, os.getlogin(), storage_name))
      os.system("chown %s /run/media/%s/%s" % (os.getlogin(), os.getlogin(), storage_name))
  else:
    raid_files = ""
    for i in range(0, raid_parts):
      raid_path_to_storage = "%s%d" % (path_to_storage, i)
      raid_storage_name = "%s%d" % (storage_name, i)
      raid_files += "/dev/mapper/" + raid_storage_name + " "
      open_mapper(raid_path_to_storage, raid_storage_name)

    print("mdadm --assemble /dev/md/%s %s" % (storage_name, raid_files))
    os.system("mdadm --assemble /dev/md/%s %s" % (storage_name, raid_files))
    os.system("mkdir -p /run/media/%s/%s" % (os.getlogin(), storage_name))
    os.system("mount -o rw,user /dev/md/%s /run/media/%s/%s" % (storage_name, os.getlogin(), storage_name))
    os.system("chown %s /run/media/%s/%s" % (os.getlogin(), os.getlogin(), storage_name))

def close_luks():
  if len(sys.argv) != 3:
    print("Error: Wrong arguments count")
    exit(help) 
  
  storage_name = str(sys.argv[2])

  if os.path.exists("/run/media/%s/%s" % (os.getlogin(), storage_name)):
    os.system("umount -d -q /run/media/%s/%s" % (os.getlogin(), storage_name))
    os.system("rm -rf /run/media/%s/%s" % (os.getlogin(), storage_name))

  if os.path.exists("/dev/md/%s" % storage_name):
    os.system("mdadm --stop --verbose /dev/md/%s" % storage_name)

  if os.path.exists("/dev/mapper/%s" % storage_name):
    close_mapper(storage_name)
  else:
    i = 0
    while os.path.exists("/dev/mapper/%s%d" % (storage_name, i)):
      close_mapper("%s%d" % (storage_name, i))
      i += 1
  
op_commands = {
  "create" : create_luks,
  "open" : open_luks,
  "close" : close_luks
}

#Main
if os.geteuid() != 0:
  exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

if len(sys.argv) > 1 and sys.argv[1] in op_commands:
  op_commands[sys.argv[1]]()
else:
  print("Error: First argument must be an [op_command]")
  exit(help)