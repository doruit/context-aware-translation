"""Deterministic terminology enforcer with regex-based replacements."""

import re
from typing import List, Tuple, Optional
from .glossary_loader import GlossaryEntry
from .audit import EnforcementAudit


class TerminologyEnforcer:
    """Enforces glossary terms in translated text with case and punctuation handling."""
    
    def __init__(self, entries: List[GlossaryEntry]):
        """Initialize enforcer with glossary entries.
        
        Args:
            entries: List of glossary entries (should be sorted by length desc)
        """
        self.entries = entries
    
    def enforce(
        self,
        text: str,
        audit: Optional[EnforcementAudit] = None
    ) -> str:
        """Enforce glossary terms in text.
        
        Strategy:
        1. Process entries longest-first to avoid partial matches
        2. Use word boundaries to avoid substring replacements
        3. Preserve case when possible
        4. Handle punctuation attached to terms
        
        Args:
            text: Text to enforce terminology in
            audit: Optional audit record to track replacements
            
        Returns:
            Text with enforced terminology
        """
        enforced_text = text
        
        # Track positions that have been replaced to avoid overlapping replacements
        replaced_ranges: List[Tuple[int, int]] = []
        
        for entry in self.entries:
            # Find all matches for this term
            matches = list(self._find_matches(enforced_text, entry.source))
            
            # Process matches in reverse order to maintain positions
            for match_obj, matched_text in reversed(matches):
                start, end = match_obj.span()
                
                # Skip if this range overlaps with an already-replaced range
                if self._overlaps_with_any(start, end, replaced_ranges):
                    continue
                
                # Get case-preserved replacement
                replacement = self._preserve_case(matched_text, entry.target)
                
                # Perform replacement
                enforced_text = (
                    enforced_text[:start] + replacement + enforced_text[end:]
                )
                
                # Record this replacement
                replaced_ranges.append((start, start + len(replacement)))
                
                # Add to audit if provided
                if audit:
                    audit.add_application(
                        source_term=entry.source,
                        target_term=entry.target,
                        position=start,
                        original_text=matched_text
                    )
        
        return enforced_text
    
    def _find_matches(
        self,
        text: str,
        term: str
    ) -> List[Tuple[re.Match, str]]:
        """Find all matches of a term in text with word boundaries.
        
        Args:
            text: Text to search in
            term: Term to search for
            
        Returns:
            List of (match_object, matched_text) tuples
        """
        # Escape special regex characters in the term
        escaped_term = re.escape(term)
        
        # Create pattern with word boundaries
        # \b doesn't work well with some characters, so we use a more robust approach
        pattern = r'(?<!\w)' + escaped_term + r'(?!\w)'
        
        matches = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matches.append((match, match.group(0)))
        
        return matches
    
    def _preserve_case(self, original: str, replacement: str) -> str:
        """Preserve case pattern from original text when replacing.
        
        Args:
            original: Original matched text
            replacement: Replacement text
            
        Returns:
            Replacement text with preserved case pattern
        """
        # If original is all uppercase, make replacement uppercase
        if original.isupper():
            return replacement.upper()
        
        # If original is title case (first letter upper), make replacement title case
        if original and original[0].isupper() and not original[1:].isupper():
            return replacement[0].upper() + replacement[1:].lower()
        
        # If original is all lowercase, make replacement lowercase
        if original.islower():
            return replacement.lower()
        
        # Default: return replacement as-is
        return replacement
    
    def _overlaps_with_any(
        self,
        start: int,
        end: int,
        ranges: List[Tuple[int, int]]
    ) -> bool:
        """Check if a range overlaps with any in a list.
        
        Args:
            start: Start position
            end: End position
            ranges: List of (start, end) tuples
            
        Returns:
            True if overlaps with any range, False otherwise
        """
        for r_start, r_end in ranges:
            # Check for overlap: ranges overlap if one starts before the other ends
            if start < r_end and end > r_start:
                return True
        return False
    
    def get_applicable_terms(self, text: str) -> List[GlossaryEntry]:
        """Get list of glossary terms that appear in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of applicable glossary entries
        """
        applicable = []
        
        for entry in self.entries:
            matches = self._find_matches(text, entry.source)
            if matches:
                applicable.append(entry)
        
        return applicable
