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
import signal
import sys

"""
 Define Variables
"""
DEBUG = True
VERSION = "0.5"

PW_WARN = '\nNOTICE: You may be prompted for you password,\n'
PW_WARN += 'NOTICE: this is directly from the ssh client, not keploy\n'

class KeployVariables:
  def __init__(self, user=None):
    self.ssh_bin = getSSHBinary()
    self.ssh_config = '/etc/ssh/ssh_config'
    if (not os.access(self.ssh_config, os.R_OK)):
      self.ssh_config = None
    self.ssh_home_dir = os.path.expanduser('~/.ssh')
    self.tmp_file = os.path.join(self.ssh_home_dir, 'keyploy.tmp')
    self.id_files = (os.path.join(self.ssh_home_dir, 'id_rsa.pub'),
                     os.path.join(self.ssh_home_dir, 'id_dsa.pub'),
                     os.path.join(self.ssh_home_dir, 'identity.pub'))
    self.host_files = [os.path.join(self.ssh_home_dir, 'known_hosts'),
                       os.path.join(self.ssh_home_dir, 'known_hosts2')]
    self.auth_keys_file = os.path.join(self.ssh_home_dir, 'authorized_keys')
    self.user = user

  def set(self, name, value):
    setattr(self, name, value)

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
  type = ['WARNING', 'ERROR']
  out = '%s: %s' % (type[ret], msg)
  if ret == 0:
    print out
  elif ret == 1:
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
def getSSHBinary():
  """
  Try to locate the ssh binary using which.
  If 'None' we found nothing
  If 'False' it is not executeable (should not happen, but why not test?)

  returns str(ssh_bin)
	"""
  ssh_bin = os.popen('/usr/bin/which ssh').read().strip()
  if ssh_bin == '':
    ssh_bin = None
  elif not os.access(ssh_bin, os.X_OK):
    ssh_bin = False
  return ssh_bin

def getHostsFromFile(get_from=None, known=False, verbose=True):
  """
  Read hosts from provided file.  If no file specified,
  try to read ~/.ssh/known_hosts

  returns list(hosts)
  """
  debugOut('getHostsFromFile(get_from=%s, known=%s, verbose=%s)' % (get_from,
      known, verbose))
  global host_files
  if get_from is not None:
    if os.access(get_from, os.R_OK):
      standardOut('Using user-defined host list from file: %s' % (
        get_from), verbose)
      host_files = [get_from]
  else:    
    if known:
      # First check to see if we can even get useful data out of the 
      # known_hosts file
      execute = "grep HashKnownHosts %s | awk '{print $2}'" % (ssh_config)
      debugOut(execute, '\tExecuting')
      is_hash = os.popen(execute).read().strip()
      debugOut(is_hash, '\tIs known_hosts hashed')
      if is_hash == "yes":
        msg = "The known_hosts files are hashed.  Please "
        msg += "specify host or alternate file to parse at cli"
        errorOut(msg)
      for f in host_files:
        try:
          os.path.exists(f)
        except:
          pass
        else:
          host_files.remove(f)
  hosts = []
  for x in host_files:
    execute = 'cat %s | cut -f1 -d" " | sed -e "s/,.*//g" | uniq' % (x)
    debugOut(execute, '\tExecuting')
    si, so, se = os.popen3(execute)
    for h in so.readlines():
      h = h.strip()
      debugOut(h, '\tFound Host')
      hosts.append(h)
  return list(hosts)

def getIdentity(id_file, verbose=True):
  """
  Read the identity file into a variable so that it is easier to push
  to the external host(s)

  returns str(identity)
  """
  debugOut('getIdentity(id_file=%s, verbose=%s)' % (id_file, verbose))
  if os.access(id_file, os.R_OK):
    identity = os.popen('head -1 %s' % (id_file)).read().strip()
    standardOut('\tProcessed identity:\n\t\t%s' % (id_file), verbose)
    debugOut(identity, '\tIdentity')
  else:
    errorOut('Could not find/access identity file: %s' % (id_file))
  return str(identity)

def findDefaultIdentityFile(id_files, verbose=True):
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
    else:
      errorOut('Could not find/access default identity files')

def toggleAgentForwarding(on, ssh_call, end_ssh_call, verbose=True):
  """
  This function checks the state of ForwardAgent in remote system's
  ~/.ssh/config file, and toggles it, on/off as necessary

  returns bool(status)
  """
  command = ''
  forward_option = 'ForwardAgent'
  ssh_user_config_file = os.path.join(ssh_home_dir, 'config')
  command +=  'grep -v \"%s\" %s > %s 2> /dev/null;' % (
    forward_option, ssh_user_config_file, tmp_file)
  command += 'mv -f %s %s 2>/dev/null; chmod 600 %s 2>/dev/null;' % (
    tmp_file, ssh_user_config_file, ssh_user_config_file)
  if on:
    command += 'echo \'%s yes\' >> %s 2> /dev/null; grep \"%s\" %s' % (
      forward_option, ssh_user_config_file, forward_option, ssh_user_config_file)
  remote_command=ssh_call+command+end_ssh_call
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

def pushToRemote(vars, options, hosts):
  for host in hosts:
    ssh_call = '%s -qq %s %s \'' % (vars.ssh_bin, options.login_name, host)
    end_ssh_call = '\''
    standardOut('\tWorking on host: %s' % (host),
                options.verbose)
    if options.forward:
      toggleAgentForwarding(False, ssh_call, end_ssh_call, options.verbose)
    command = ''
    try:
      old_identity
    except:
      use_identity = identity
    else:
      use_identity = old_identity
    # Make ssh home dir and set permissions
    command += 'mkdir %s &> /dev/null; chmod 700 %s;' % (
      ssh_home_dir, ssh_home_dir)
    # Remove identity from file and set permissions
    command +=  'grep -v \"%s\" %s > %s 2> /dev/null;' % (
      identity, auth_keys_file, tmp_file)
    command += 'mv -f %s %s 2>/dev/null;' % (tmp_file, auth_keys_file)
    command += 'chmod 600 %s 2> /dev/null;' % (auth_keys_file)
    if not options.remove or options.old_id_file:
      use_identity = identity
      # Then append the pub identity into the authorized_keys file, and grep it
      command += 'echo \'%s\' >> %s 2> /dev/null; chmod 600 %s; grep \"%s\" %s' % (
        use_identity, auth_keys_file, auth_keys_file, use_identity, auth_keys_file)
    remote_command=ssh_call+command+end_ssh_call
    debugOut(remote_command, 'Executing')
    ret = os.popen(remote_command).readlines()
    if ret:
      if options.old_id_file:
        status = 'changed'
      elif options.remove:
        status = 'failed to remove'
      else:
        status = 'deployed'
      for line in ret:
        debugOut(line)
    else:
      if options.remove:
        status = 'removed'
      else:
        status = 'failed to deploy'
    standardOut('\t\tPublic Identity Key: %s' % (status), options.verbose)

    if options.forward:
      if (not options.remove) or (options.old_id_file):
        toggleAgentForwarding(True, ssh_call, end_ssh_call, options.verbose)
