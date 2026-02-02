"""TSV glossary loader for terminology management."""

import csv
from pathlib import Path
from typing import List, Dict


class GlossaryEntry:
    """Represents a single glossary term entry."""
    
    def __init__(self, source: str, target: str):
        """Initialize glossary entry.
        
        Args:
            source: Source term (any language)
            target: Target term (Dutch)
        """
        self.source = source.strip()
        self.target = target.strip()
        # Store length for sorting (longest first to avoid partial matches)
        self.source_length = len(self.source)
    
    def __repr__(self) -> str:
        return f"GlossaryEntry(source='{self.source}', target='{self.target}')"


class GlossaryLoader:
    """Loads and manages TSV glossary files."""
    
    def __init__(self, glossary_path: Path):
        """Initialize glossary loader.
        
        Args:
            glossary_path: Path to TSV file (source<tab>target format)
        """
        self.glossary_path = glossary_path
        self._entries: List[GlossaryEntry] = []
    
    def load(self) -> List[GlossaryEntry]:
        """Load glossary from TSV file.
        
        Returns:
            List of glossary entries sorted by source length (longest first)
            
        Raises:
            FileNotFoundError: If glossary file doesn't exist
            ValueError: If glossary format is invalid
        """
        if not self.glossary_path.exists():
            raise FileNotFoundError(f"Glossary file not found: {self.glossary_path}")
        
        entries = []
        
        with open(self.glossary_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            
            for line_num, row in enumerate(reader, start=1):
                # Skip empty lines
                if not row or all(not cell.strip() for cell in row):
                    continue
                
                # Skip comment lines
                if row[0].strip().startswith('#'):
                    continue
                
                # Validate format
                if len(row) < 2:
                    raise ValueError(
                        f"Invalid glossary format at line {line_num}: "
                        f"Expected 2 columns (source<tab>target), got {len(row)}"
                    )
                
                source = row[0].strip()
                target = row[1].strip()
                
                # Skip empty entries
                if not source or not target:
                    continue
                
                entries.append(GlossaryEntry(source, target))
        
        # Sort by source length descending to handle overlapping terms
        # (e.g., "critical incident" before "incident")
        entries.sort(key=lambda e: e.source_length, reverse=True)
        
        self._entries = entries
        return entries
    
    def get_entries(self) -> List[GlossaryEntry]:
        """Get loaded glossary entries.
        
        Returns:
            List of glossary entries
        """
        return self._entries
    
    def get_statistics(self) -> Dict[str, int]:
        """Get glossary statistics.
        
        Returns:
            Dictionary with statistics (total_terms, etc.)
        """
        return {
            "total_terms": len(self._entries),
            "longest_term": max((e.source_length for e in self._entries), default=0),
            "shortest_term": min((e.source_length for e in self._entries), default=0),
        }
