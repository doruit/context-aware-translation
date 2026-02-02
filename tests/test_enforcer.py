"""Unit tests for terminology enforcer."""

import pytest
from src.terminology.glossary_loader import GlossaryEntry
from src.terminology.enforcer import TerminologyEnforcer
from src.terminology.audit import EnforcementAudit


class TestTerminologyEnforcer:
    """Test suite for TerminologyEnforcer."""
    
    @pytest.fixture
    def basic_glossary(self):
        """Create basic glossary entries for testing."""
        return [
            GlossaryEntry("incident", "incident"),
            GlossaryEntry("problem", "probleem"),
            GlossaryEntry("change request", "wijzigingsverzoek"),
            GlossaryEntry("service desk", "servicedesk"),
        ]
    
    @pytest.fixture
    def overlapping_glossary(self):
        """Create glossary with overlapping terms."""
        return [
            GlossaryEntry("critical incident", "kritiek incident"),
            GlossaryEntry("incident", "incident"),
            GlossaryEntry("service", "dienst"),
            GlossaryEntry("service desk", "servicedesk"),
        ]
    
    def test_basic_enforcement(self, basic_glossary):
        """Test basic term enforcement."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "We have a problem with the incident management."
        result = enforcer.enforce(text)
        
        assert "probleem" in result
        assert "incident" in result
    
    def test_case_preservation_uppercase(self, basic_glossary):
        """Test that uppercase terms are replaced with uppercase."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "PROBLEM reported in INCIDENT system"
        result = enforcer.enforce(text)
        
        assert "PROBLEEM" in result
        assert "INCIDENT" in result
    
    def test_case_preservation_titlecase(self, basic_glossary):
        """Test that title case terms are replaced with title case."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "Problem reported as an Incident"
        result = enforcer.enforce(text)
        
        assert "Probleem" in result
        assert "Incident" in result
    
    def test_case_preservation_lowercase(self, basic_glossary):
        """Test that lowercase terms are replaced with lowercase."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "the problem is related to the incident"
        result = enforcer.enforce(text)
        
        assert "probleem" in result
        assert "incident" in result
    
    def test_word_boundaries(self, basic_glossary):
        """Test that replacements respect word boundaries."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        # "incident" should not match within "incidental"
        text = "An incidental incident occurred"
        result = enforcer.enforce(text)
        
        # "incident" should be replaced, but "incidental" should remain
        assert "incident" in result.lower()
        assert "incidental" in result.lower()
    
    def test_overlapping_terms_longest_first(self, overlapping_glossary):
        """Test that longest matching terms are applied first."""
        # Sort by length descending (as done in glossary loader)
        sorted_glossary = sorted(
            overlapping_glossary,
            key=lambda e: len(e.source),
            reverse=True
        )
        enforcer = TerminologyEnforcer(sorted_glossary)
        
        text = "We have a critical incident at the service desk"
        result = enforcer.enforce(text)
        
        # "critical incident" should be replaced as a whole, not separately
        assert "kritiek incident" in result
        assert "servicedesk" in result
    
    def test_multiple_occurrences(self, basic_glossary):
        """Test that all occurrences are replaced."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "The incident caused a problem. Another incident was logged."
        result = enforcer.enforce(text)
        
        # Count occurrences
        assert result.lower().count("incident") == 2
        assert result.lower().count("probleem") == 1
    
    def test_punctuation_handling(self, basic_glossary):
        """Test that terms are replaced even with adjacent punctuation."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "Problem: incident detected. Service desk, please respond!"
        result = enforcer.enforce(text)
        
        assert "Probleem:" in result or "probleem:" in result.lower()
        assert "incident" in result
        assert "servicedesk" in result or "Servicedesk" in result
    
    def test_empty_text(self, basic_glossary):
        """Test enforcement on empty text."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        result = enforcer.enforce("")
        assert result == ""
    
    def test_no_matching_terms(self, basic_glossary):
        """Test text with no matching glossary terms."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "This is a test with no glossary terms"
        result = enforcer.enforce(text)
        
        # Text should remain unchanged
        assert result == text
    
    def test_audit_tracking(self, basic_glossary):
        """Test that audit tracks applied terms correctly."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "We have a problem with the incident"
        audit = EnforcementAudit(original_text=text, enforced_text="")
        
        result = enforcer.enforce(text, audit)
        audit.enforced_text = result
        
        # Check audit recorded the replacements
        assert len(audit.applied_terms) == 2
        
        # Verify term details
        term_targets = [app.target_term for app in audit.applied_terms]
        assert "probleem" in term_targets
        assert "incident" in term_targets
    
    def test_multiword_terms(self, basic_glossary):
        """Test enforcement of multi-word terms."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "Please create a change request for the service desk"
        result = enforcer.enforce(text)
        
        assert "wijzigingsverzoek" in result
        assert "servicedesk" in result
    
    def test_special_characters_in_terms(self):
        """Test terms with special regex characters."""
        glossary = [
            GlossaryEntry("C++ programming", "C++ programmeren"),
            GlossaryEntry("$variable", "$variabele"),
        ]
        enforcer = TerminologyEnforcer(glossary)
        
        text = "Using C++ programming with $variable"
        result = enforcer.enforce(text)
        
        assert "C++ programmeren" in result
        assert "$variabele" in result
    
    def test_get_applicable_terms(self, basic_glossary):
        """Test getting list of applicable terms."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        text = "We have an incident and a problem"
        applicable = enforcer.get_applicable_terms(text)
        
        # Should find "incident" and "problem"
        assert len(applicable) == 2
        source_terms = [entry.source for entry in applicable]
        assert "incident" in source_terms
        assert "problem" in source_terms
    
    def test_no_double_replacement(self, basic_glossary):
        """Test that already-replaced terms are not replaced again."""
        enforcer = TerminologyEnforcer(basic_glossary)
        
        # If target term appears in source text, it should only be replaced once
        text = "The incident and the incident are related"
        result = enforcer.enforce(text)
        
        # Both "incident" occurrences should be in result
        assert result.lower().count("incident") == 2
    
    def test_unicode_handling(self):
        """Test enforcement with Unicode characters."""
        glossary = [
            GlossaryEntry("café", "koffiehuis"),
            GlossaryEntry("naïve", "naïef"),
        ]
        enforcer = TerminologyEnforcer(glossary)
        
        text = "The café has a naïve approach"
        result = enforcer.enforce(text)
        
        assert "koffiehuis" in result
        assert "naïef" in result


class TestGlossaryEntry:
    """Test suite for GlossaryEntry."""
    
    def test_creation(self):
        """Test entry creation."""
        entry = GlossaryEntry("source term", "target term")
        
        assert entry.source == "source term"
        assert entry.target == "target term"
        assert entry.source_length == 11
    
    def test_whitespace_stripping(self):
        """Test that whitespace is stripped."""
        entry = GlossaryEntry("  source  ", "  target  ")
        
        assert entry.source == "source"
        assert entry.target == "target"


class TestEnforcementAudit:
    """Test suite for EnforcementAudit."""
    
    def test_add_application(self):
        """Test adding term application to audit."""
        audit = EnforcementAudit(
            original_text="test",
            enforced_text="test"
        )
        
        audit.add_application("incident", "incident", 0, "incident")
        
        assert len(audit.applied_terms) == 1
        assert audit.applied_terms[0].source_term == "incident"
        assert audit.applied_terms[0].target_term == "incident"
    
    def test_get_summary(self):
        """Test audit summary generation."""
        audit = EnforcementAudit(
            original_text="test",
            enforced_text="test"
        )
        
        audit.add_application("incident", "incident", 0, "incident")
        audit.add_application("problem", "probleem", 10, "problem")
        
        summary = audit.get_summary()
        
        assert summary['total_replacements'] == 2
        assert summary['unique_terms'] == 2
        assert len(summary['replacements']) == 2
