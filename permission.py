
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
        "system":           SYSTEM,
    }
    
    def __init__(self, guild_id):
        self.id = guild_id
        self.configuration = 0
        self.channels = {}
    
    def get_permission(self, channel_id):
        return self.channels.get(channel_id, Permission.NONE)
    
    def get(self, channel_id, permission_default):
        return (self.get_permission(channel_id) * bool(self.configuration) * (len(self.channels) > 0)) | permission_default
    
    def add(self, channel_id, permission):
        if not (self.get_permission(channel_id) & Permission.CONFIGURATION) and (permission & Permission.CONFIGURATION):
            self.configuration += 1
        self.channels.update({channel_id: self.channels.get(channel_id, Permission.NONE) | permission})
    
    def delete(self, channel_id, permission):
        if (self.get_permission(channel_id) & Permission.CONFIGURATION) and (permission & Permission.CONFIGURATION):
            self.configuration -= 1
        p = self.channels.get(channel_id, Permission.NONE) & ~permission
        if p:
            self.channels.update({channel_id: p})
        elif channel_id in self.channels:
            self.channels.pop(channel_id)
    
    def clear(self, channel_id):
        if channel_id in self.channels:
            if (self.get_permission(channel_id) & Permission.CONFIGURATION):
                self.configuration -= 1
            self.channels.pop(channel_id)
