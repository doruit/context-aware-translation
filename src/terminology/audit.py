"""Audit and metrics tracking for terminology enforcement."""

from typing import List, Dict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TermApplication:
    """Represents a single application of a glossary term."""
    
    source_term: str
    target_term: str
    position: int
    original_text: str  # The actual text that was replaced (may have different case)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EnforcementAudit:
    """Audit record for a single enforcement operation."""
    
    original_text: str
    enforced_text: str
    applied_terms: List[TermApplication] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def add_application(
        self,
        source_term: str,
        target_term: str,
        position: int,
        original_text: str
    ) -> None:
        """Record a term application.
        
        Args:
            source_term: Source term from glossary
            target_term: Target term from glossary
            position: Position in text where replacement occurred
            original_text: The actual text that was replaced
        """
        self.applied_terms.append(
            TermApplication(
                source_term=source_term,
                target_term=target_term,
                position=position,
                original_text=original_text
            )
        )
    
    def get_summary(self) -> Dict:
        """Get audit summary.
        
        Returns:
            Dictionary with audit summary
        """
        return {
            "total_replacements": len(self.applied_terms),
            "unique_terms": len(set(app.source_term for app in self.applied_terms)),
            "replacements": [
                {
                    "source_term": app.source_term,
                    "target_term": app.target_term,
                    "original_text": app.original_text,
                    "position": app.position
                }
                for app in self.applied_terms
            ],
            "timestamp": self.timestamp.isoformat()
        }


class AuditCollector:
    """Collects and manages enforcement audits."""
    
    def __init__(self):
        """Initialize audit collector."""
        self._audits: List[EnforcementAudit] = []
    
    def create_audit(self, original_text: str, enforced_text: str) -> EnforcementAudit:
        """Create a new audit record.
        
        Args:
            original_text: Text before enforcement
            enforced_text: Text after enforcement
            
        Returns:
            New audit record
        """
        audit = EnforcementAudit(
            original_text=original_text,
            enforced_text=enforced_text
        )
        self._audits.append(audit)
        return audit
    
    def get_recent_audits(self, limit: int = 10) -> List[EnforcementAudit]:
        """Get most recent audit records.
        
        Args:
            limit: Maximum number of audits to return
            
        Returns:
            List of recent audits
        """
        return self._audits[-limit:]
    
    def get_statistics(self) -> Dict:
        """Get aggregate statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_replacements = sum(len(a.applied_terms) for a in self._audits)
        all_terms = [app.source_term for a in self._audits for app in a.applied_terms]
        
        return {
            "total_audits": len(self._audits),
            "total_replacements": total_replacements,
            "unique_terms_used": len(set(all_terms)),
            "avg_replacements_per_audit": (
                total_replacements / len(self._audits) if self._audits else 0
            )
        }
