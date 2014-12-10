import pxssh

s = pxssh.pxssh()
if not s.login ('localhost', '', ''):
    print "SSH session failed on login."
    print str(s)
else:
    print "SSH session login successful"
    s.sendline ('uptime')
    s.prompt()         # match the prompt
    print s.before     # print everything before the prompt.
    s.logout()
    
#We can also execute multiple command like this:
s.sendline ('uptime;df -h')