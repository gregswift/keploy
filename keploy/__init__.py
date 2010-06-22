#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# keploy - SSH Public Key Deplyment Utility
# Copyright © 2007 Greg Swift gregswift@gmail.com
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

class KeployError(Exception):
  def __init__(self, message, code=255):
    Exception.__init__(self, message, code)

"""
 Define Variables
"""
DEBUG = False
VERSION = "1.0"

PW_WARN = '\nNOTICE: You may be prompted for you password,\n'
PW_WARN += 'NOTICE: this is directly from the ssh client, not keploy\n'

SSH_BIN = os.popen('/usr/bin/which ssh 2> /dev/null').read().strip()
if SSH_BIN == '':
  raise KeployError, ('SSH binary not locatable by /usr/bin/which', 100)
elif not os.access(SSH_BIN, os.X_OK):
  raise KeployError, ('SSH Binary not executable by your user', 101)
SSH_DIR = '~/.ssh'
SSH_LOCAL_DIR = os.path.expanduser(SSH_DIR)
SSH_CONFIGS = ('/etc/ssh/ssh_config', os.path.join(SSH_DIR,'config'))
SSH_START_CALL = SSH_BIN+' -qq %s %s \''
SSH_END_CALL = '\''
# Local Files
ID_FILES = (os.path.join(SSH_LOCAL_DIR, 'id_rsa.pub'),
    os.path.join(SSH_LOCAL_DIR, 'id_dsa.pub'),
    os.path.join(SSH_LOCAL_DIR, 'identity.pub'))
HOST_FILES = [os.path.join(SSH_LOCAL_DIR, 'known_hosts'),
    os.path.join(SSH_LOCAL_DIR, 'known_hosts2')]
# Files on remote host
TMP_FILE = os.path.join(SSH_DIR, 'keyploy.tmp')
AUTH_KEYS_FILE = os.path.join(SSH_DIR, 'authorized_keys')

"""
 Define Output Functions and cleanUp Function
"""
def standardOut(msg, on=True):
  """
  When quiet is not enabled, display msg provided.
  """
  if (on):
    print msg

def debugOut(msg, name=None, on=DEBUG):
  """
  When debug is enabled, output is printed to the display.
  """
  if name is not None:
    name = name+': '
  else:
    name = ''
  try:
    if on:
      print 'DEBUG: %s%s' % (name, msg)
    else:
      pass
  except:
    print 'MALFORMED DEBUG: %s%s' % (name, msg)

def errorOut(msg, ret=1):
  """
  When debug is enabled, output is printed to the display.

  returns nothing
  """
  if ret >= 1:
    prefix = 'ERROR'
  else:
    prefix = 'WARNING'
  out = '%s: %s' % (prefix, msg)
  if ret == 0:
    print out
  elif ret >= 1:
    out += '\n'
    sys.stderr.write(out)
    cleanUp(ret)

def cleanUp(ret):
  """
  Do a clean and proper sys.exit()

  executes sys.exit(int(ret))
  """
  sys.exit(ret)


"""
 Define Primary Functions
"""
def isHostsFileHashed(verbose=False):
  """
  Check to see if we can even get useful data out of the known_hosts files

  returns bool()
  """
  for config in SSH_CONFIGS:
    if os.path.exists(config) and not os.access(config, os.R_OK):
      raise KeployError, 'Unable to read config file %s' % (config)
    execute = "grep HashKnownHosts %s | awk '{print $2}'" % (config)
    debugOut(execute, '\tExecuting', verbose)
    is_hash = os.popen(execute).read().strip()
    debugOut(is_hash, '\tIs known_hosts hashed', verbose)
    if is_hash == "yes":
      return True
    return False

def getHostsFromFile(host_files, verbose=False):
  """
  Read hosts from provided file(s).

  returns list(hosts)
  """
  debugOut('getHostsFromFile(host_files=%s, verbose=%s)' % (host_files,
      verbose))
  if not isinstance(host_files, (list, tuple)):
    host_files = [host_files]
  hosts = []
  for host_file in host_files:
    if not os.path.exists(host_file):
      continue
    elif not os.access(host_file, os.R_OK):
      raise KeployError, 'Unable to parse hosts from file: %s' % (host_file)
    for line in open(host_file).readlines():
      host = line.strip().split()[0]
      if ',' in host:
        host = host.split(',')[0]
      if host not in hosts:
        debugOut(host, '\tFound Host')
        hosts.append(host)
  return list(hosts)

def getIdentity(id_file, verbose=False):
  """
  Read the identity file into a variable so that it is easier to push
  to the external host(s)

  returns str(identity)
  """
  debugOut('getIdentity(id_file=%s, verbose=%s)' % (id_file, verbose))
  if os.access(id_file, os.R_OK):
    identity = open(id_file).readlines()[0].strip()
    standardOut('\tProcessed identity:\n\t\t%s' % (id_file), verbose)
    debugOut(identity, '\tIdentity')
    return str(identity)
  raise KeployError('Could not find/access identity file: %s' % (id_file))

def findDefaultIdentityFile(id_files, verbose=False):
  """
  Return the first identity file name that is available from the provided list

  returns str(id_file)
  """
  debugOut('findDefaultIdentity(id_files=%s, verbose=%s)' % (id_files, verbose))
  for id_file in id_files:
    debugOut(id_file, '\tTrying to grab identity from')
    if os.access(id_file, os.R_OK):
      standardOut('\tFound identity file:\n\t\t%s' % (id_file), verbose)
      return str(id_file)
  raise KeployError('Could not find/access default identity files')

def toggleAgentForwarding(on, host, login_name, verbose=False):
  """
  This function checks the state of ForwardAgent in remote system's
  ~/.ssh/config file, and toggles it, on/off as necessary

  returns bool(status)
  """
  ssh_call = SSH_START_CALL % (login_name, host)
  command = ''
  forward_option = 'ForwardAgent'
  command +=  'grep -v \"%s\" %s > %s 2> /dev/null;' % (
    forward_option, SSH_CONFIGS[1], TMP_FILE)
  command += 'mv -f %s %s 2>/dev/null; chmod 600 %s 2>/dev/null;' % (
    TMP_FILE, SSH_CONFIGS[1], SSH_CONFIGS[1])
  if on:
    command += 'echo \'%s yes\' >> %s 2> /dev/null; grep \"%s\" %s' % (
      forward_option, SSH_CONFIGS[1], forward_option, SSH_CONFIGS[1])
  remote_command=ssh_call+command+SSH_END_CALL
  debugOut(remote_command, 'Executing')
  ret = os.popen(remote_command).readlines()
  if ret:
    if on:
      status = (True, 'enabled')
    else:
      status = (False, 'failed to disable')
    for line in ret:
      debugOut(line)
  else:
    if on:
      status = (False, 'failed to enable')
    else:
      status = (True, 'disabled')
  return status
  #standardOut('\t\tAgent Forwarding: %s' % (status), verbose)

def pushToRemoteHosts(hosts, identity, login_name, forward=False,
    remove_old=False, old_identity=None, verbose=False):
  if not isinstance(hosts, (tuple, list)):
    hosts = list(hosts)
  for host in hosts:
    command = buildSSHPushCommand(host, identity, login_name, forward,
        remove_old, old_identity, verbose)
    debugOut(command, 'Executing')
    ret = os.popen(command).readlines()
    if ret:
      if old_identity:
        status = 'changed'
      elif remove_old:
        status = 'failed to remove'
      else:
        status = 'deployed'
      for line in ret:
        debugOut(line)
    else:
      if remove_old:
        status = 'removed'
      else:
        status = 'failed to deploy'
    standardOut('\t\tPublic Identity Key: %s' % (status), verbose)

    if forward and not remove_old:
      toggleAgentForwarding(True, host, login_name, verbose)

def buildSSHPushCommand(host, identity, login_name, forward=False,
      remove_old=False, old_identity=None, verbose=False):
    ssh_call = SSH_START_CALL % (login_name, host)
    standardOut('\tWorking on host: %s' % (host), verbose)
    if forward:
      toggleAgentForwarding(False, host, login_name, verbose)
    command = ''
    if old_identity is None:
      old_identity = identity
    # Make ssh home dir and set permissions
    command += 'mkdir %s &> /dev/null; chmod 700 %s;' % (SSH_DIR, SSH_DIR)
    # Remove identity from file and set permissions
    command +=  'grep -v \"%s\" %s > %s 2> /dev/null;' % (
      old_identity, AUTH_KEYS_FILE, TMP_FILE)
    command += 'mv -f %s %s 2>/dev/null;' % (TMP_FILE, AUTH_KEYS_FILE)
    command += 'chmod 600 %s 2> /dev/null;' % (AUTH_KEYS_FILE)
    if not remove_old:
      # Then append the pub identity into the authorized_keys file, and grep it
      command += 'echo \'%s\' >> %s 2> /dev/null; chmod 600 %s; grep \"%s\" %s' % (
        identity, AUTH_KEYS_FILE, AUTH_KEYS_FILE, identity, AUTH_KEYS_FILE)
    return ssh_call+command+SSH_END_CALL
