
class Permission(object):
    
    """
        Hold Guild permissions on a per channel basis.
    """
    
    NONE            = 0x00
    READ            = 0x01
    COMMAND         = 0x02
    CONFIGURATION   = 0x04
    SYSTEM          = 0x08
    ALL             = NONE | READ | COMMAND | CONFIGURATION | SYSTEM
    
    permissions = {
        "read":             READ,
        "command":          COMMAND,
        "configuration":    CONFIGURATION,
    }
    
    permissions_privileged = {
        "system":           SYSTEM,
    }
    
    permissions_all = dict(permissions)
    permissions_all.update(permissions_privileged)
    
    @classmethod
    def get_names(cls, permission):
        return [k for (k, v) in cls.permissions_all.items() if (permission & v)]
    
    def __init__(self):
        self.configuration = 0
        self.channels = {}
    
    def get(self, channel_id):
        return self.channels.get(channel_id, Permission.NONE)
    
    def get_enabled(self, channel_id):
        return (self.get(channel_id) * (self.configuration > 0) * (len(self.channels) > 0)) or Permission.CONFIGURATION
    
    def add(self, channel_id, permission):
        if not (self.get(channel_id) & Permission.CONFIGURATION) and (permission & Permission.CONFIGURATION):
            self.configuration += 1
        self.channels.update({channel_id: self.get(channel_id) | permission})
    
    def delete(self, channel_id, permission):
        if channel_id in self.channels:
            if (self.get(channel_id) & Permission.CONFIGURATION) and (permission & Permission.CONFIGURATION):
                self.configuration -= 1
            p = self.get(channel_id) & ~permission
            if p:
                self.channels.update({channel_id: p})
            else:
                self.channels.pop(channel_id)
    
    def erase(self, channel_id):
        if channel_id in self.channels:
            if (self.get(channel_id) & Permission.CONFIGURATION):
                self.configuration -= 1
            self.channels.pop(channel_id)
    
    def clear(self):
        self.configuration = 0
        self.channels = {}
