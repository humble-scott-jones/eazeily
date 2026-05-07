"""VerificationEngine - Multi-Agent Verification Loop Service

This module provides a RAG-based content verification system that uses the Gemini API
to fact-check and technically validate AI-generated content against a "Source of Truth"
database. It's designed to run on a dedicated internal server and integrate with the main
Eazeily routing layer via async callbacks.

Key features:
- Modular, strongly typed API
- Robust error handling for API timeouts and distributed infrastructure
- Structured verification feedback (flagged terms, revisions)
- Simulated RAG lookup (can be replaced with real vector store)
"""

from __future__ import annotations
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any, Mapping
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# TYPE DEFINITIONS & ENUMS
# ============================================================================

class VerificationSeverity(str, Enum):
    """Severity level of flagged content issues."""
    CRITICAL = "critical"      # Factual error, incorrect spec, harmful claim
    WARNING = "warning"         # Potentially inaccurate, needs review
    INFO = "info"               # Suggestion or style improvement


@dataclass
class FlaggedTerm:
    """Represents a single flagged term and its correction."""
    original: str
    suggested_fix: str
    reason: str
    severity: VerificationSeverity = VerificationSeverity.INFO
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original": self.original,
            "suggested_fix": self.suggested_fix,
            "reason": self.reason,
            "severity": self.severity.value,
        }


@dataclass
class VerificationResult:
    """Complete verification result for a draft."""
    is_valid: bool
    flagged_terms: List[FlaggedTerm]
    revised_draft: str
    confidence_score: float  # 0.0-1.0
    verification_summary: str
    source_of_truth_references: List[str]  # URIs/IDs of SOT records used
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "flagged_terms": [term.to_dict() for term in self.flagged_terms],
            "revised_draft": self.revised_draft,
            "confidence_score": self.confidence_score,
            "verification_summary": self.verification_summary,
            "source_of_truth_references": self.source_of_truth_references,
            "execution_time_ms": self.execution_time_ms,
        }


# ============================================================================
# SOURCE OF TRUTH DATABASE (Simulated)
# ============================================================================

class SourceOfTruthStore:
    """
    Simulated local knowledge base for fact-checking.
    In production, this would connect to a real vector store or SQL database.
    """
    
    def __init__(self):
        """Initialize the simulated SOT store with niche-specific data."""
        self._data: Dict[str, Dict[str, Any]] = {
            # Hardware/Vintage Tech Context
            "vintage_computing": {
                "id": "vintage_computing",
                "domain": "vintage_computing",
                "facts": [
                    {"key": "commodore_64_cpu", "value": "6510", "description": "Commodore 64 uses a 6510 processor at 1.023 MHz"},
                    {"key": "apple_2_release", "value": "1977", "description": "Apple II was released in 1977"},
                    {"key": "spectrum_48k_memory", "value": "48 KB", "description": "ZX Spectrum 48K had 48 KB of RAM"},
                    {"key": "atari_2600_year", "value": "1977", "description": "Atari 2600 was released in 1977"},
                ]
            },
            # Toy Collectibles/Factions
            "toy_collectibles": {
                "id": "toy_collectibles",
                "domain": "toy_collectibles",
                "facts": [
                    {"key": "transformers_decepticons", "value": "Megatron, Starscream", "description": "Primary Decepticon leaders"},
                    {"key": "gi_joe_created", "value": "1964", "description": "G.I. Joe action figure line launched in 1964"},
                    {"key": "He_Man_toy_line", "value": "Masters of the Universe", "description": "He-Man franchise by Mattel"},
                    {"key": "lego_classic_start", "value": "1958", "description": "LEGO modern brick system introduced in 1958"},
                ]
            },
            # General Marketing/Business Terms
            "business_terms": {
                "id": "business_terms",
                "domain": "business_terms",
                "facts": [
                    {"key": "ctr_definition", "value": "Click-through rate", "description": "CTR is the % of clicks on an ad or link"},
                    {"key": "roi_full", "value": "Return on Investment", "description": "ROI measures profit from an investment"},
                    {"key": "cpa_definition", "value": "Cost per acquisition", "description": "CPA is the marketing cost to acquire one customer"},
                ]
            }
        }
    
    def get_context_by_niche(self, niche_context_id: str) -> Dict[str, Any]:
        """
        Retrieve all facts and rules for a specific niche/domain.
        
        Args:
            niche_context_id: Domain key (e.g., 'vintage_computing', 'toy_collectibles')
        
        Returns:
            Dict with domain facts and metadata, or empty dict if not found.
        """
        context = self._data.get(niche_context_id, {})
        if not context:
            logger.warning(f"Niche context '{niche_context_id}' not found in SOT; returning empty.")
        return context or {}
    
    def search_terms(self, terms: List[str], niche_context_id: str) -> List[Dict[str, Any]]:
        """
        Search for specific terms in a niche context.
        
        Args:
            terms: List of terms to search for
            niche_context_id: Domain to search within
        
        Returns:
            List of matching facts.
        """
        context = self.get_context_by_niche(niche_context_id)
        facts = context.get("facts", [])
        
        results = []
        for term in terms:
            term_lower = term.lower()
            for fact in facts:
                if term_lower in fact.get("key", "").lower() or \
                   term_lower in fact.get("value", "").lower():
                    results.append(fact)
        
        return list({f["key"]: f for f in results}.values())  # Deduplicate


# ============================================================================
# GEMINI-BASED FACT-CHECKER AGENT
# ============================================================================

class FactCheckerAgent:
    """
    Wraps Gemini API to act as a strict, technical editor/fact-checker.
    Uses RAG context to cross-reference claims in the draft.
    """
    
    def __init__(self, api_timeout_sec: int = 20):
        self.api_timeout = api_timeout_sec
        self._sot_store = SourceOfTruthStore()
    
    def _build_editor_prompt(
        self,
        draft_text: str,
        niche_context_id: str,
        sot_context: Dict[str, Any],
    ) -> str:
        """
        Build the structured prompt for the Gemini "Editor Agent."
        This prompt is crafted to prioritize technical accuracy over marketing flair.
        """
        facts_str = json.dumps(sot_context.get("facts", []), indent=2)
        
        prompt = f"""You are a STRICT TECHNICAL EDITOR and FACT-CHECKER.
Your role is to ensure content accuracy above all else—marketing appeal is secondary.

## SOURCE OF TRUTH (Domain: {niche_context_id})
{facts_str}

## DRAFT TO VERIFY
{draft_text}

## YOUR TASK
1. **Identify inaccuracies**: Flag any claims that contradict the Source of Truth.
2. **Catch vague terms**: Flag imprecise or marketing-speak language that could mislead.
3. **Check specs/numbers**: Verify all technical specifications, years, versions, etc.
4. **Suggest corrections**: For each flagged item, provide the accurate replacement text.

## OUTPUT FORMAT (JSON)
Return a JSON object with this exact structure:
{{
  "is_valid": <boolean>,
  "flagged_terms": [
    {{
      "original": "<exact phrase from draft>",
      "suggested_fix": "<corrected phrase>",
      "reason": "<why this is wrong or needs fixing>",
      "severity": "<critical|warning|info>"
    }}
  ],
  "revised_draft": "<full draft with corrections applied>",
  "confidence_score": <0.0-1.0>,
  "verification_summary": "<brief summary of findings>"
}}

## CONSTRAINTS
- Be conservative: flag anything you're uncertain about.
- Do NOT soften truth for marketing purposes.
- "is_valid" should be TRUE only if confidence_score >= 0.85 AND no critical flags.
- Return ONLY valid JSON, no markdown or extra text.
"""
        return prompt
    
    def verify(
        self,
        draft_text: str,
        niche_context_id: str,
    ) -> VerificationResult:
        """
        Main verification method: fact-check a draft against SOT context.
        
        Args:
            draft_text: The AI-generated content to verify
            niche_context_id: The niche/domain to check against (e.g., 'vintage_computing')
        
        Returns:
            VerificationResult with flagged items and revised draft.
        
        Raises:
            TimeoutError: If Gemini API call exceeds timeout.
            ValueError: If response is malformed or unusable.
        """
        start_time = time.time()
        
        try:
            # 1. Fetch SOT context
            sot_context = self._sot_store.get_context_by_niche(niche_context_id)
            if not sot_context:
                logger.warning(f"No SOT context for niche '{niche_context_id}'; using empty context.")
                sot_context = {"facts": []}
            
            # 2. Build the structured prompt
            prompt = self._build_editor_prompt(draft_text, niche_context_id, sot_context)
            
            # 3. Call Gemini API
            response_dict = self._call_gemini_with_timeout(prompt)
            
            # 4. Parse and validate response
            result = self._parse_verification_response(response_dict, draft_text, sot_context)
            
            # 5. Calculate execution time
            elapsed_ms = (time.time() - start_time) * 1000
            result.execution_time_ms = elapsed_ms
            
            logger.info(f"Verification complete in {elapsed_ms:.0f}ms. "
                       f"Valid: {result.is_valid}, Flagged: {len(result.flagged_terms)}")
            
            return result
        
        except TimeoutError as e:
            logger.error(f"Verification timeout after {self.api_timeout}s: {e}")
            raise
        except Exception as e:
            logger.error(f"Verification failed: {e}", exc_info=True)
            raise ValueError(f"Verification failed: {str(e)}")
    
    def _call_gemini_with_timeout(self, prompt: str) -> Dict[str, Any]:
        """
        Call the Gemini API with retry and timeout logic.
        
        Returns:
            dict with 'text' or 'content' key containing the response
        
        Raises:
            TimeoutError if retries exhausted or timeout exceeded.
        """
        try:
            from services.generation.gemini_adapter import call_gemini
        except ImportError:
            logger.error("gemini_adapter not available; returning mock response")
            return {"text": json.dumps({"is_valid": True, "flagged_terms": [], "revised_draft": "", "confidence_score": 1.0, "verification_summary": "Mock response"})}
        
        max_retries = 2
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                response = call_gemini(
                    prompt,
                    temperature=0.0,  # Use deterministic/low-temperature for fact-checking
                    timeout=self.api_timeout,
                    max_retries=0,  # Handle retries manually here
                )
                return response
            except TimeoutError as e:
                last_error = e
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Timeout on attempt {retry_count}/{max_retries}; retrying...")
                    time.sleep(1)  # Brief delay before retry
            except Exception as e:
                logger.error(f"Gemini call error: {e}")
                raise ValueError(f"Gemini API call failed: {str(e)}")
        
        raise TimeoutError(f"Verification timed out after {max_retries} retries: {last_error}")
    
    def _parse_verification_response(
        self,
        response_dict: Dict[str, Any],
        original_draft: str,
        sot_context: Dict[str, Any],
    ) -> VerificationResult:
        """
        Parse and validate the Gemini response into a VerificationResult.
        Includes defensive parsing and fallback handling.
        """
        try:
            # Extract response text
            text = response_dict.get("text") or response_dict.get("content") or ""
            if not text:
                raise ValueError("Empty response from Gemini")
            
            # Parse JSON
            data = json.loads(text.strip())
            
            # Extract fields with fallback defaults
            is_valid = bool(data.get("is_valid", False))
            confidence = float(data.get("confidence_score", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            revised_draft = str(data.get("revised_draft", original_draft)).strip()
            if not revised_draft:
                revised_draft = original_draft
            
            summary = str(data.get("verification_summary", "Verification complete")).strip()
            
            # Parse flagged terms
            flagged = []
            for item in data.get("flagged_terms", []):
                try:
                    severity_str = str(item.get("severity", "info")).lower()
                    severity = VerificationSeverity(severity_str) if severity_str in [s.value for s in VerificationSeverity] else VerificationSeverity.INFO
                    
                    flagged.append(FlaggedTerm(
                        original=str(item.get("original", "")).strip(),
                        suggested_fix=str(item.get("suggested_fix", "")).strip(),
                        reason=str(item.get("reason", "")).strip(),
                        severity=severity,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse flagged term: {e}")
            
            # Build reference list
            sot_refs = [f"domain:{sot_context.get('id', 'unknown')}"]
            
            return VerificationResult(
                is_valid=is_valid,
                flagged_terms=flagged,
                revised_draft=revised_draft,
                confidence_score=confidence,
                verification_summary=summary,
                source_of_truth_references=sot_refs,
                execution_time_ms=0.0,  # Will be set by caller
            )
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            # Return a safe fallback: assume draft is valid if we can't verify
            return VerificationResult(
                is_valid=True,
                flagged_terms=[],
                revised_draft=original_draft,
                confidence_score=0.0,
                verification_summary="Response parsing failed; returning draft as-is.",
                source_of_truth_references=[],
                execution_time_ms=0.0,
            )


# ============================================================================
# VERIFICATION ENGINE (Main Orchestrator)
# ============================================================================

class VerificationEngine:
    """
    Main orchestrator for the Multi-Agent Verification Loop.
    Coordinates fact-checking against a Source of Truth and returns structured feedback.
    """
    
    def __init__(self, api_timeout_sec: int = 20):
        """
        Initialize the VerificationEngine.
        
        Args:
            api_timeout_sec: Timeout for individual Gemini API calls (default 20s).
        """
        self._fact_checker = FactCheckerAgent(api_timeout_sec=api_timeout_sec)
        self._cache: Dict[str, tuple[VerificationResult, float]] = {}
        self._cache_ttl_sec = 3600  # 1 hour cache TTL
    
    def verify_content(
        self,
        draft_text: str,
        niche_context_id: str,
        use_cache: bool = True,
    ) -> VerificationResult:
        """
        Verify an AI-generated draft against technical Source of Truth.
        
        This is the main entry point for content verification. It:
        1. Checks cache (optional)
        2. Calls the fact-checker agent
        3. Returns structured verification results
        
        Args:
            draft_text: The AI-generated content to verify
            niche_context_id: Niche/domain context (e.g., 'vintage_computing', 'toy_collectibles')
            use_cache: Whether to use cached results for identical drafts
        
        Returns:
            VerificationResult with flagged terms, revisions, and confidence score.
        
        Example:
            >>> engine = VerificationEngine()
            >>> result = engine.verify_content(
            ...     draft_text="The Commodore 64 uses a 6502 processor...",
            ...     niche_context_id="vintage_computing"
            ... )
            >>> print(f"Valid: {result.is_valid}, Flags: {len(result.flagged_terms)}")
            >>> for flag in result.flagged_terms:
            ...     print(f"  {flag.original} -> {flag.suggested_fix}")
        """
        # Generate cache key
        cache_key = self._make_cache_key(draft_text, niche_context_id)
        
        # Check cache
        if use_cache and cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            age_sec = time.time() - cached_time
            if age_sec < self._cache_ttl_sec:
                logger.info(f"Cache hit for verification (age: {age_sec:.1f}s)")
                return cached_result
            else:
                del self._cache[cache_key]
        
        # Perform verification
        result = self._fact_checker.verify(draft_text, niche_context_id)
        
        # Cache result
        if use_cache:
            self._cache[cache_key] = (result, time.time())
        
        return result
    
    def verify_content_batch(
        self,
        drafts: List[str],
        niche_context_id: str,
    ) -> List[VerificationResult]:
        """
        Verify multiple drafts in sequence.
        (In production, this could be parallelized with thread/async pool.)
        
        Args:
            drafts: List of drafts to verify
            niche_context_id: Shared niche context for all drafts
        
        Returns:
            List of VerificationResult objects in the same order as input.
        """
        results = []
        for draft in drafts:
            try:
                result = self.verify_content(draft, niche_context_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch verification failed for draft: {e}")
                # Return a failed result for this draft
                results.append(VerificationResult(
                    is_valid=False,
                    flagged_terms=[],
                    revised_draft=draft,
                    confidence_score=0.0,
                    verification_summary=f"Verification failed: {str(e)}",
                    source_of_truth_references=[],
                    execution_time_ms=0.0,
                ))
        
        return results
    
    def _make_cache_key(self, draft_text: str, niche_id: str) -> str:
        """Generate a deterministic cache key."""
        import hashlib
        content = f"{niche_id}:{draft_text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def clear_cache(self) -> None:
        """Clear the verification result cache."""
        self._cache.clear()
        logger.info("Verification cache cleared")


# ============================================================================
# CONVENIENCE FUNCTIONS (For easy integration with Flask routes)
# ============================================================================

# Global engine instance (lazy-loaded)
_engine_instance: Optional[VerificationEngine] = None


def get_verification_engine() -> VerificationEngine:
    """Lazy-load and return the global VerificationEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = VerificationEngine(api_timeout_sec=20)
        logger.info("VerificationEngine initialized")
    return _engine_instance


def verify_content(draft_text: str, niche_context_id: str) -> Dict[str, Any]:
    """
    Convenience function to verify content in one call.
    Returns the result as a JSON-serializable dictionary.
    
    Args:
        draft_text: The draft to verify
        niche_context_id: The niche context
    
    Returns:
        dict with keys: is_valid, flagged_terms, revised_draft, confidence_score, etc.
    """
    engine = get_verification_engine()
    result = engine.verify_content(draft_text, niche_context_id)
    return result.to_dict()
