"""
This type stub file was generated by pyright.
"""

class Refspec:
    """The constructor is for internal use only.
    """
    def __init__(self, owner, ptr) -> None:
        ...
    
    @property
    def src(self):
        """Source or lhs of the refspec"""
        ...
    
    @property
    def dst(self):
        """Destinaton or rhs of the refspec"""
        ...
    
    @property
    def force(self): # -> bool:
        """Whether this refspeca llows non-fast-forward updates"""
        ...
    
    @property
    def string(self):
        """String which was used to create this refspec"""
        ...
    
    @property
    def direction(self):
        """Direction of this refspec (fetch or push)"""
        ...
    
    def src_matches(self, ref): # -> bool:
        """Return True if the given string matches the source of this refspec,
        False otherwise.
        """
        ...
    
    def dst_matches(self, ref): # -> bool:
        """Return True if the given string matches the destination of this
        refspec, False otherwise."""
        ...
    
    def transform(self, ref):
        """Transform a reference name according to this refspec from the lhs to
        the rhs. Return an string.
        """
        ...
    
    def rtransform(self, ref):
        """Transform a reference name according to this refspec from the lhs to
        the rhs. Return an string.
        """
        ...
    


