"""
VerdictOrchestrator - Core AI judge logic for generating verdicts.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.case import Case
from app.models.document import Document
from app.models.verdict import Verdict
from app.services.openai_service import OpenAIService


class VerdictOrchestrator:
    """Orchestrates verdict generation using AI."""

    @staticmethod
    def fetch_case_context(case_id: UUID, db: Session) -> Dict:
        """
        Fetch all context needed for verdict generation.

        Args:
            case_id: Case UUID
            db: Database session

        Returns:
            Dict with case, documents, arguments, previous verdict

        Raises:
            Exception: If case not found
        """
        # Get case
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case not found: {case_id}")

        # Get documents for both sides
        documents = db.query(Document).filter(
            Document.case_id == case_id,
            Document.status == 'ready'
        ).all()

        side_a_docs = [doc for doc in documents if doc.side == 'A']
        side_b_docs = [doc for doc in documents if doc.side == 'B']

        return {
            'case': case,
            'side_a_docs': side_a_docs,
            'side_b_docs': side_b_docs,
            'arguments': [],  # Will be populated for later rounds
            'previous_verdict': None  # Will be populated for later rounds
        }

    @staticmethod
    def validate_documents(context: Dict) -> None:
        """
        Validate that both sides have submitted documents.

        Args:
            context: Case context dict

        Raises:
            ValueError: If documents missing
        """
        if not context['side_a_docs']:
            raise ValueError("Side A has not submitted any documents")

        if not context['side_b_docs']:
            raise ValueError("Side B has not submitted any documents")

    @staticmethod
    def build_verdict_prompt(context: Dict, round_number: int) -> str:
        """
        Build prompt for GPT to generate verdict.

        Args:
            context: Case context
            round_number: Current round (0 for initial verdict)

        Returns:
            Prompt string
        """
        case = context['case']
        side_a_docs = context['side_a_docs']
        side_b_docs = context['side_b_docs']

        # Build document summaries
        side_a_summary = "\n\n".join([
            f"**{doc.title}** ({doc.file_type})\n{doc.full_text[:1000]}"
            for doc in side_a_docs
        ])

        side_b_summary = "\n\n".join([
            f"**{doc.title}** ({doc.file_type})\n{doc.full_text[:1000]}"
            for doc in side_b_docs
        ])

        prompt = f"""You are an AI judge presiding over a mock trial case.

**CASE INFORMATION:**
- Title: {case.title}
- Case Number: {case.case_number}
- Type: {case.case_type}
- Jurisdiction: {case.jurisdiction}
- Description: {case.description or 'N/A'}

**CURRENT ROUND:** {round_number} (Initial Verdict - no arguments yet)

Your task is to analyze the evidence submitted by both sides and deliver an initial verdict.

**SIDE A EVIDENCE:**
{side_a_summary}

**SIDE B EVIDENCE:**
{side_b_summary}

**INSTRUCTIONS:**
1. Carefully review all evidence from both sides
2. Identify the key legal issues
3. Analyze each issue based on the evidence presented
4. Determine which side has the stronger case
5. Provide reasoning for your decision
6. Assign a confidence score (0.0 to 1.0)

**IMPORTANT:** You must respond with ONLY a valid JSON object in the following format:

{{
    "summary": "Brief 2-3 sentence summary of the case",
    "winner": "A" or "B" or "undecided",
    "confidence_score": 0.85,
    "issues": [
        {{
            "issue": "Question or issue being decided",
            "finding": "Your finding on this issue",
            "reasoning": "Detailed reasoning with evidence citations"
        }}
    ],
    "final_decision": "Your final verdict with reasoning (3-5 sentences)",
    "key_evidence_cited": ["Document titles that were most important"]
}}

Provide your verdict as a JSON object only:"""

        return prompt

    @staticmethod
    def parse_verdict_json(json_string: str) -> Dict:
        """
        Parse and validate verdict JSON from GPT response.

        Args:
            json_string: JSON string from GPT

        Returns:
            Parsed dict

        Raises:
            Exception: If JSON invalid or missing required fields
        """
        try:
            verdict_dict = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in verdict response: {str(e)}")

        # Validate required fields
        required_fields = ['summary', 'winner', 'confidence_score', 'issues', 'final_decision', 'key_evidence_cited']
        missing_fields = [field for field in required_fields if field not in verdict_dict]

        if missing_fields:
            raise Exception(f"Missing required fields in verdict: {', '.join(missing_fields)}")

        # Validate winner value
        if verdict_dict['winner'] not in ['A', 'B', 'undecided']:
            raise Exception(f"Invalid winner value: {verdict_dict['winner']}")

        return verdict_dict

    @staticmethod
    def generate_initial_verdict(case_id: UUID, db: Session) -> Verdict:
        """
        Generate initial verdict (Round 0) for a case.

        Args:
            case_id: Case UUID
            db: Database session

        Returns:
            Created Verdict object

        Raises:
            Exception: If verdict already exists or generation fails
        """
        # Check if Round 0 verdict already exists
        existing_verdict = db.query(Verdict).filter(
            Verdict.case_id == case_id,
            Verdict.round == 0
        ).first()

        if existing_verdict:
            raise Exception("Round 0 verdict already exists for this case")

        # Fetch context
        context = VerdictOrchestrator.fetch_case_context(case_id, db)

        # Validate documents
        VerdictOrchestrator.validate_documents(context)

        # Build prompt
        prompt = VerdictOrchestrator.build_verdict_prompt(context, round_number=0)

        # Call GPT
        try:
            client = OpenAIService.get_client()

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced AI judge delivering fair and reasoned verdicts based on evidence. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low for consistent legal reasoning
                max_tokens=2000,
                response_format={"type": "json_object"}  # Ensure JSON response
            )

            # Parse response
            verdict_json_str = response.choices[0].message.content
            verdict_dict = VerdictOrchestrator.parse_verdict_json(verdict_json_str)

            # Get token usage
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None

            # Create verdict record
            verdict = Verdict(
                case_id=case_id,
                round=0,
                verdict_json=verdict_dict,
                model_used='gpt-4o-mini',
                tokens_used=tokens_used
            )

            db.add(verdict)
            db.commit()
            db.refresh(verdict)

            # Update case status
            case = context['case']
            case.status = 'in_progress'
            case.current_round = 1  # Ready for first argument round
            db.commit()

            return verdict

        except Exception as e:
            raise Exception(f"Failed to generate verdict: {str(e)}")

    @staticmethod
    def get_verdict_by_round(case_id: UUID, round_number: int, db: Session) -> Optional[Verdict]:
        """
        Get verdict for a specific round.

        Args:
            case_id: Case UUID
            round_number: Round number
            db: Database session

        Returns:
            Verdict or None
        """
        return db.query(Verdict).filter(
            Verdict.case_id == case_id,
            Verdict.round == round_number
        ).first()

    @staticmethod
    def get_all_verdicts(case_id: UUID, db: Session) -> List[Verdict]:
        """
        Get all verdicts for a case.

        Args:
            case_id: Case UUID
            db: Database session

        Returns:
            List of Verdict objects
        """
        return db.query(Verdict).filter(
            Verdict.case_id == case_id
        ).order_by(Verdict.round).all()
