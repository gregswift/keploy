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
try:
  import paramiko
except ImportError:
  paramiko = False
from binascii import hexlify

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
  raise KeployError('SSH binary not locatable by /usr/bin/which', 100)
elif not os.access(SSH_BIN, os.X_OK):
  raise KeployError('SSH Binary not executable by your user', 101)
SSH_DIR = '~/.ssh'
SSH_LOCAL_DIR = os.path.expanduser(SSH_DIR)
SSH_CONFIGS = ('/etc/ssh/ssh_config', os.path.join(SSH_DIR,'config'))
SSH_FORWARD_OPTION = 'ForwardAgent'
SSH_START_CALL = SSH_BIN+' -qq %s %s \''
SSH_END_CALL = '\''
# Local Files
ID_FILES = (os.path.join(SSH_LOCAL_DIR, 'id_rsa.pub'),
    os.path.join(SSH_LOCAL_DIR, 'id_dsa.pub'),
    os.path.join(SSH_LOCAL_DIR, 'identity.pub'))
HOST_FILES = [os.path.join(SSH_LOCAL_DIR, 'known_hosts'),
    os.path.join(SSH_LOCAL_DIR, 'known_hosts2')]
# Files on remote host
TMP_FILE = os.path.join(SSH_DIR, 'keploy.tmp')
AUTH_KEYS_FILE = os.path.join(SSH_DIR, 'authorized_keys')

"""
 Define subclasses of paramiko to meet the behavior patterns we want to run
"""
class UnknownHostsPolicy(paramiko.MissingHostKeyPolicy):
    """
    Policy for automatically adding the hostname and new host key to the
    local L{HostKeys} object, and saving it.  This is used by L{SSHClient}.
    """
    def __init__(self, accept_unknown_hosts):
      self.accept_unknown_hosts = accept_unknown_hosts

    def missing_host_key(self, client, hostname, key):
      if not self.accept_unknown_hosts:
        print "Found unknown host: %s" % hostname
        fingerprint = getFingerPrint(key)
        print "Host key: %s" % fingerprint
        self.accept_unknown_hosts = prompt("Accept unknown host key?", "n")
      if self.accept_unknown_hosts:
        client._host_keys.add(hostname, key.get_name(), key)
        if client._host_keys_filename is not None:
          client.save_host_keys(client._host_keys_filename)
        standardOut('Adding %s host key for %s: %s' %
            (key.get_name(), hostname, fingerprint))
      else:
        raise paramiko.SSHException, 'Unknown host %s' % hostname
        #standardOut('Host key for %s not accepted, skipping host' % hostname)

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

def prompt(question, default=None, string=False, integer=False,
      hide_answer=False):
  """
  This function provides for interaction with the user via stdin/out.
  First we display the question followed by the default in square brackets.
 
  By default, this is a Yes/No prompt, but if you set either
  string or integer to True, it will validate that they answer with that type
 
  If you want to prompt without printing what is typed enable hide_answer,
  this is useful for functions such as getting a password.

  default return is bool()
  string and integer return as their types
  """
  def throwInvalid(resp):
    print "Invalid response: %s" % (resp)

  if (string or integer):
    if (default is None):
      default = ''
    display = default
  else:
    (yes, no) = ("y", "n")
    if (default):
      if (default.lower() == yes):
        yes = yes.upper()
      elif (default.lower() == no):
        no = no.upper()
    display = '%s/%s' % (yes, no)

  while True:
    if (display):
      question += " [%s]" % (display)
    if (hide_answer):
      answer = getpass(question)
    else:
      print "%s" % (question),
      answer = raw_input()
    if (not answer):
      if (default is not None):
        answer = default
      else:
        continue
    if (string and answer is not None):
      try:
        answer = str(answer)
      except:
        throwInvalid(answer)
        continue
      break
    elif (integer):
      try:
        answer = int(answer)
      except:
        throwInvalid(answer)
        continue
      break
    else:
      if (answer == yes.lower()):
        answer = True
      elif (answer == no.lower()):
        answer = False
      else:
        throwInvalid(answer)
        continue  
      break
  return answer

"""
 Define Primary Functions
"""
def getFingerPrint(key):
  hex_fp = key.get_fingerprint()
  ascii_fp = ''
  i = 0
  for c in hexlify(hex_fp):
    if i == 2:
        ascii_fp += ':'
        i = 1
    else:
        i += 1
    ascii_fp += c
  return ascii_fp

def isHostsFileHashed(verbose=False):
  """
  Check to see if we can even get useful data out of the known_hosts files

  returns bool()
  """
  for config in SSH_CONFIGS:
    if os.path.exists(config) and not os.access(config, os.R_OK):
      raise KeployError('Unable to read config file %s' % (config), 30)
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
      raise KeployError('Unable to parse hosts from file %s' % (host_file), 45)
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
  raise KeployError('Could not find/access identity file %s' % (id_file), 65)

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
  raise KeployError('Could not find/access default identity files', 60)

def oldToggleAgentForwarding(on, host, login_name, verbose=False):
  """
  DEPRECATED IN FAVOR OF paramiko and toggleSSHConfigOption
  
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

def toggleAgentForwarding(connection, state, verbose=False):
  """
  Uses setRemoteSSHConfigOption to change the state of ForwardAgent
  in the remote user's ~/.ssh/config file on/off.
  
  returns tuple(status, details)
  """
  raise KeployError, 'Incomplete function'

def setRemoteSSHConfigOption(connection, option, value=None, verbose=False):
  """
  Removes existing value of an SSH config option in the remote users's
  ~/.ssh/config file, and then set its to value if one

  returns bool(status)
  """
  commands = ['grep -v \"%s\" %s > %s' % (option, SSH_CONFIGS[1], TMP_FILE)]
  commands.append('mv -f %s %s' % (TMP_FILE, SSH_CONFIGS[1]))
  commands.append('chmod 600 %s ' % (SSH_CONFIGS[1]))
  if value:
    commands.append('echo \'%s %s\' >> %s' % (option, value, SSH_CONFIGS[1]))
    commands.append('grep \"%s %s\" %s' % (option, value, SSH_CONFIGS[1]))
  commands = tuple(commands)
  debugOut(commands, 'Executing:')
  for command in commands:
    connection = paramiko.SSHClient()
    try:
      (si, so, se) = connection.exec_command(command)
    except paramiko.SSHException, e:
      #TODO: add conditional if needed
      #if e ?
      #print e
      raise KeployError, 'Unable to set %s to %s' % (option, value)
    if se:
      #Todo... test and determine action
      pass
  if so:
    return True
  return False

def pushToRemoteHosts(hosts, identity, login_name, forward=False,
    remove_old=False, old_identity=None, accept_new_hosts=False,
    accept_changed_hosts=False, verbose=False):
  if not isinstance(hosts, (tuple, list)):
    hosts = list(hosts)
  connection = paramiko.SSHClient()
  for known_hosts in HOST_FILES:
    if os.access(known_hosts, os.R_OK):
      connection.load_host_keys(known_hosts)
      connection._host_keys
  connection.load_system_host_keys()
  connection.set_missing_host_key_policy(UnknownHostsPolicy(accept_new_hosts))
  for host in hosts:
    if paramiko:
      while True:
        try:
          connection.connect(host, username=login_name)
        except paramiko.SSHException, e:
          if e.message.startswith('Unknown server'):
            standardOut('Host key for %s not accepted, skipping.' % host)
            next_host = True
            break
        except paramiko.BadHostKeyException, e:
          if accept_changed_hosts:
            clear_old_host_key = True
          else:
            old_host_fp = getFingerPrint(e.expected_key)
            standardOut('WARNING: Host key for %s does NOT match!' % host)
            standardOut('WARNING: Invalid host fingerprint: %s' % old_host_fp)
            msg = 'Clear old host key? (If not expected, JUST SAY NO!)'
            clear_old_host_key = prompt(msg, default='n')
          if clear_old_host_key:
            #TODO: add support for key type changing??
            # Changing key types doesn't work because paramiko's underlying
            # dictionary objects don't support removing values
            key_class = e.key.__class__.__name__
            if key_class == 'RSAKey':
              key_type = 'ssh-rsa'
            elif key_class == 'DSSKey':
              key_type = 'ssh-dss'
            else:
              raise KeployError('Unknown ssh key type %s.' % (key_class), 80)
            if key_type != connection._host_keys[host].keys()[0]:
              msg = 'Replacing a key with a different type is not supported,'
              msg += ' please\nmanually remove the old key from the local'
              msg += ' known_hosts file. You can\nuse the following command:\n'
              msg += '    ssh-keygen -R %s' % host
              raise KeployError(msg, 85)
            connection._host_keys.add(host, key_type, e.key)
          else:
            # At this point we've decided not to skip this host
            next_host = True
            break
      if next_host:
        continue
      command = buildSSHPushCommand(host, identity)
      if forward:
        toggleSSHConfigOption(connection, 'FordwardAgent', False, verbose)

    else:
      # This is the older process for systems that don't have paramiko
      command = oldbuildSSHPushCommand(host, identity, login_name, forward,
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
      oldToggleAgentForwarding(True, host, login_name, verbose)

def oldBuildSSHPushCommand(host, identity, login_name, forward=False,
      remove_old=False, old_identity=None, verbose=False):
  ssh_call = SSH_START_CALL % (login_name, host)
  standardOut('\tWorking on host: %s' % (host), verbose)
  if forward:
    oldToggleAgentForwarding(False, host, login_name, verbose)
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

def verifyEnvironment(connection, verbose=False):
  # Commands to make ssh home dir and set permissions
  commands = ['mkdir %s' % (SSH_DIR), 'chmod 700 %s' % (SSH_DIR)]
  
def removeIdentity(connection, identity, verbose=False):
  # Command Remove identity from file and set permissions
  commands = ['grep -v \"%s\" %s > %s' % (old_identity, AUTH_KEYS_FILE,
      TMP_FILE)]
  commands.append('mv -f %s %s' % (TMP_FILE, AUTH_KEYS_FILE))
  commands.append('chmod 600 %s' % (AUTH_KEYS_FILE))
  
def addIdentity(connection, identity, verbose=False):
  # Append the pub identity into the authorized_keys file, and verify it
  commands = ['echo \'%s\' >> %s' % (identity, AUTH_KEYS_FILE)]
  commands.append('chmod 600 %s' % (AUTH_KEYS_FILE))
  commands.append('grep \"%s\" %s' % (AUTH_KEYS_FILE))



#[xaeth@sblap12lx keploy]$ ssh localhost
#The authenticity of host 'localhost (127.0.0.1)' can't be established.
#RSA key fingerprint is 93:c7:b9:e2:55:59:b0:04:f9:92:d3:bc:b9:3b:dc:bb.
#Are you sure you want to continue connecting (yes/no)? yes
#Warning: Permanently added 'localhost' (RSA) to the list of known hosts.
#Password: 

#[xaeth@sblap12lx keploy]$ tail -1 ~/.ssh/known_hosts > a
#[xaeth@sblap12lx keploy]$ ssh-keygen -l -f a
#2048 93:c7:b9:e2:55:59:b0:04:f9:92:d3:bc:b9:3b:dc:bb localhost (RSA)
