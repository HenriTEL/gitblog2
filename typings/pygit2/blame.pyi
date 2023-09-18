"""
This type stub file was generated by pyright.
"""

def wrap_signature(csig): # -> Signature | None:
    ...

class BlameHunk:
    @property
    def lines_in_hunk(self):
        """Number of lines"""
        ...
    
    @property
    def boundary(self): # -> bool:
        """Tracked to a boundary commit"""
        ...
    
    @property
    def final_start_line_number(self):
        """Final start line number"""
        ...
    
    @property
    def final_committer(self): # -> Signature | None:
        """Final committer"""
        ...
    
    @property
    def final_commit_id(self): # -> Oid:
        ...
    
    @property
    def orig_start_line_number(self):
        """Origin start line number"""
        ...
    
    @property
    def orig_committer(self): # -> Signature | None:
        """Original committer"""
        ...
    
    @property
    def orig_commit_id(self): # -> Oid:
        ...
    
    @property
    def orig_path(self): # -> None:
        """Original path"""
        ...
    


class Blame:
    def __del__(self): # -> None:
        ...
    
    def __len__(self):
        ...
    
    def __getitem__(self, index): # -> BlameHunk:
        ...
    
    def for_line(self, line_no): # -> BlameHunk:
        """
        Returns the <BlameHunk> object for a given line given its number in the
        current Blame.

        Parameters:

        line_no
            Line number, starts at 1.
        """
        ...
    
    def __iter__(self): # -> GenericIterator:
        ...
    


