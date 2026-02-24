#!/usr/bin/env python3
"""
Diagram Router — analyzes text and picks the optimal diagram type.
Detection only. Does NOT extract elements — the agent does that.

Usage:
    python3 diagram_router.py "User logs in, system checks credentials..."
    → {"diagram_type": "flowchart", "confidence": 0.85, "reasoning": "..."}
"""

import json
import re
import sys


def detect_type(text: str) -> dict:
    """
    Analyze input text and determine the best diagram type.
    
    Returns:
        {
            "diagram_type": "flowchart" | "architecture" | "sequence" | "mindmap" | "timeline" | "er" | "simple",
            "confidence": 0.0-1.0,
            "reasoning": "why this type was chosen"
        }
    """
    text_lower = text.lower()
    
    scores = {
        "flowchart": _score_flowchart(text_lower),
        "architecture": _score_architecture(text_lower),
        "sequence": _score_sequence(text_lower),
        "mindmap": _score_mindmap(text_lower),
        "timeline": _score_timeline(text_lower),
        "er": _score_er(text_lower),
    }
    
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    
    if best_score < 0.2:
        return {
            "diagram_type": "simple",
            "confidence": 0.5,
            "reasoning": "No strong pattern detected, defaulting to simple diagram"
        }
    
    reasons = {
        "flowchart": "Detected steps, decisions, or process flow",
        "architecture": "Detected system components, services, or layers",
        "sequence": "Detected message passing between actors/services",
        "mindmap": "Detected central concept with branches or categories",
        "timeline": "Detected chronological events or dates",
        "er": "Detected entities with attributes and relationships",
    }
    
    return {
        "diagram_type": best_type,
        "confidence": round(min(best_score, 1.0), 2),
        "reasoning": reasons[best_type]
    }


def _score_flowchart(text: str) -> float:
    keywords = [
        "if ", "then", "else", "step", "process", "decision", "start", "end",
        "flow", "when", "next", "begin", "check", "validate", "verify",
        "approve", "reject", "submit", "retry", "loop", "repeat"
    ]
    patterns = [
        r'\bif\b.*\bthen\b', r'\bif\s+(yes|no|valid|invalid)\b',
        r'step\s*\d', r'\d\.\s+\w+',  # numbered steps
        r'(first|second|third|finally|lastly)',
        r'(yes|no)\s*[,:]', r'if\s+(yes|no|true|false|valid|invalid)',
    ]
    
    score = sum(0.15 for k in keywords if k in text)
    score += sum(0.25 for p in patterns if re.search(p, text))
    
    # Strong signal: "if X, do Y, else Z" pattern
    if re.search(r'if\s+\w+.*,\s*(do|show|go|redirect|return)', text):
        score += 0.4
    
    return min(score, 1.0)


def _score_architecture(text: str) -> float:
    keywords = [
        "service", "database", "api", "frontend", "backend", "server",
        "client", "layer", "component", "system", "microservice", "gateway",
        "queue", "cache", "load balancer", "proxy", "container", "cluster",
        "rest", "grpc", "graphql", "webhook", "endpoint"
    ]
    patterns = [
        r'(front.?end|back.?end)', r'(micro.?service|web.?server)',
        r'(api|db|cdn|dns|ssl|http|tcp)\b',
        r'(connects?\s+to|communicates?\s+with|talks?\s+to)',
        r'(layer|tier)\s*\d',
    ]
    
    score = sum(0.15 for k in keywords if k in text)
    score += sum(0.25 for p in patterns if re.search(p, text))
    return min(score, 1.0)


def _score_sequence(text: str) -> float:
    keywords = [
        "sends", "receives", "request", "response", "calls", "returns",
        "message", "actor", "reply", "acknowledge", "notify", "publish",
        "subscribe", "emit", "trigger", "callback", "webhook"
    ]
    patterns = [
        r'\w+\s+sends?\s+\w+\s+to\s+\w+',  # "A sends X to B"
        r'\w+\s+(calls?|requests?)\s+\w+',   # "A calls B"
        r'\w+\s+returns?\s+\w+',              # "B returns X"
        r'\w+\s+responds?\s+(with|to)\s+',    # "B responds with X"
        r'(request|response)\s+(from|to)\s+',
    ]
    
    score = sum(0.15 for k in keywords if k in text)
    score += sum(0.3 for p in patterns if re.search(p, text))
    
    # Strong signal: multiple "X to Y" patterns
    to_patterns = len(re.findall(r'\b\w+\s+to\s+\w+\b', text))
    if to_patterns >= 3:
        score += 0.3
    
    return min(score, 1.0)


def _score_mindmap(text: str) -> float:
    keywords = [
        "aspects of", "categories", "branches", "related to", "subtopics",
        "brainstorm", "ideas", "concepts", "topics", "main topic",
        "central", "branching", "hierarchy", "breakdown", "subdivisions",
        "mind map", "mindmap", "overview of", "types of", "kinds of",
        "areas of", "components of", "parts of", "elements of"
    ]
    patterns = [
        r'aspects?\s+of\s+', r'main\s+(topic|concept|idea)',
        r'central\s+(concept|idea|theme)', r'branches?\s+(into|to|of)',
        r'subdivided\s+into', r'related\s+(concepts|ideas|topics)',
        r'has\s+branches', r'types?\s+of\s+',
        r'\w+\s*\([^)]+,\s*[^)]+\)',  # "Topic (sub1, sub2)" pattern
    ]
    
    score = sum(0.2 for k in keywords if k in text)
    score += sum(0.3 for p in patterns if re.search(p, text))
    
    # Nested parens with commas = strong mind map signal
    nested_groups = len(re.findall(r'\w+\s*\([^)]+,\s*[^)]+\)', text))
    if nested_groups >= 2:
        score += 0.4
    
    return min(score, 1.0)


def _score_timeline(text: str) -> float:
    keywords = [
        "timeline", "history", "evolution", "milestone", "era",
        "chronolog", "founded", "launched", "released", "established"
    ]
    patterns = [
        r'\b\d{4}\b',  # years
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d',
        r'(before|after)\s+\d{4}',
        r'\d{4}\s*[-–:]\s*\w+',  # "2008: something" or "2008 - something"
    ]
    
    score = sum(0.2 for k in keywords if k in text)
    score += sum(0.25 for p in patterns if re.search(p, text))
    
    # Strong signal: multiple years
    years = len(re.findall(r'\b(19|20)\d{2}\b', text))
    if years >= 3:
        score += 0.4
    elif years >= 2:
        score += 0.2
    
    return min(score, 1.0)


def _score_er(text: str) -> float:
    keywords = [
        "entity", "relationship", "has many", "belongs to", "one to many",
        "many to many", "one to one", "attributes", "fields", "table",
        "schema", "foreign key", "primary key", "column", "record"
    ]
    patterns = [
        r'(has\s+many|belongs\s+to|has\s+one)',
        r'(one|many)\s+to\s+(one|many)',
        r'entity\s+\w+\s+has',
        r'(table|entity)\s+\w+',
        r'attributes?\s*[:=]',
    ]
    
    score = sum(0.2 for k in keywords if k in text)
    score += sum(0.3 for p in patterns if re.search(p, text))
    
    # Strong signal: multiple "has many" / "belongs to"
    rel_count = len(re.findall(r'(has\s+many|belongs\s+to|has\s+one)', text))
    if rel_count >= 2:
        score += 0.4
    
    return min(score, 1.0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 diagram_router.py 'text describing what to diagram'")
        sys.exit(1)
    
    result = detect_type(" ".join(sys.argv[1:]))
    print(json.dumps(result, indent=2))
