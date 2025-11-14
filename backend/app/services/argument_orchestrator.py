"""
ArgumentOrchestrator - Handles argument submission and verdict regeneration.
"""

import json
from typing import Dict, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.case import Case
from app.models.argument import Argument
from app.models.document import Document
from app.models.verdict import Verdict
from app.services.openai_service import OpenAIService


class ArgumentOrchestrator:
    """Orchestrates argument submission and verdict regeneration."""

    @staticmethod
    def submit_argument(
        case_id: UUID,
        side: str,
        argument_text: str,
        user_id: UUID,
        db: Session
    ) -> Dict:
        """
        Submit an argument and automatically generate new verdict for next round.

        Args:
            case_id: Case UUID
            side: 'A' or 'B'
            argument_text: The argument text
            user_id: User submitting the argument
            db: Database session

        Returns:
            Dict with 'argument' and 'verdict' objects

        Raises:
            Exception: If submission fails or max rounds exceeded
        """
        # Get case
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case not found: {case_id}")

        # Validate case status
        if case.status == 'finalized':
            raise Exception("Cannot submit arguments to a finalized case")

        if case.status == 'draft':
            raise Exception("Case must have an initial verdict before arguments can be submitted")

        # Check if max rounds exceeded
        if case.current_round >= case.max_rounds:
            raise Exception(f"Maximum rounds ({case.max_rounds}) already reached. Case ready for finalization.")

        # Get current round
        current_round = case.current_round

        # Check if this side already submitted an argument for this round
        existing_arg = db.query(Argument).filter(
            Argument.case_id == case_id,
            Argument.round == current_round,
            Argument.side == side
        ).first()

        if existing_arg:
            raise Exception(f"Side {side} has already submitted an argument for round {current_round}")

        # Create argument record
        argument = Argument(
            case_id=case_id,
            round=current_round,
            side=side,
            argument_text=argument_text,
            submitted_by=user_id
        )

        db.add(argument)
        db.commit()
        db.refresh(argument)

        # Check if both sides have now submitted arguments for this round
        side_a_arg = db.query(Argument).filter(
            Argument.case_id == case_id,
            Argument.round == current_round,
            Argument.side == 'A'
        ).first()

        side_b_arg = db.query(Argument).filter(
            Argument.case_id == case_id,
            Argument.round == current_round,
            Argument.side == 'B'
        ).first()

        # Only generate new verdict if BOTH sides have submitted
        verdict = None
        if side_a_arg and side_b_arg:
            try:
                verdict = ArgumentOrchestrator.generate_verdict_with_arguments(
                    case_id, current_round, db
                )

                # Increment case round
                case.current_round = current_round + 1
                db.commit()

            except Exception as e:
                raise Exception(f"Failed to generate verdict after arguments: {str(e)}")

        return {
            'argument': argument,
            'verdict': verdict,
            'waiting_for_other_side': verdict is None
        }

    @staticmethod
    def generate_verdict_with_arguments(
        case_id: UUID,
        round_number: int,
        db: Session
    ) -> Verdict:
        """
        Generate verdict for a round that includes arguments from both sides.

        Args:
            case_id: Case UUID
            round_number: Current round (1-5)
            db: Database session

        Returns:
            Created Verdict object

        Raises:
            Exception: If verdict generation fails
        """
        # Get case
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception(f"Case not found: {case_id}")

        # Get all documents
        documents = db.query(Document).filter(
            Document.case_id == case_id,
            Document.status == 'ready'
        ).all()

        side_a_docs = [doc for doc in documents if doc.side == 'A']
        side_b_docs = [doc for doc in documents if doc.side == 'B']

        # Get arguments for this round
        arguments = db.query(Argument).filter(
            Argument.case_id == case_id,
            Argument.round == round_number
        ).all()

        side_a_args = [arg for arg in arguments if arg.side == 'A']
        side_b_args = [arg for arg in arguments if arg.side == 'B']

        # Get previous verdict (from round_number - 1)
        previous_verdict = db.query(Verdict).filter(
            Verdict.case_id == case_id,
            Verdict.round == round_number - 1
        ).first()

        # Build prompt with arguments
        prompt = ArgumentOrchestrator.build_verdict_with_arguments_prompt(
            case=case,
            side_a_docs=side_a_docs,
            side_b_docs=side_b_docs,
            side_a_args=side_a_args,
            side_b_args=side_b_args,
            previous_verdict=previous_verdict,
            round_number=round_number
        )

        # Call GPT
        try:
            client = OpenAIService.get_client()

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced AI judge delivering fair and reasoned verdicts based on evidence and arguments. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2500,
                response_format={"type": "json_object"}
            )

            # Parse response
            verdict_json_str = response.choices[0].message.content
            verdict_dict = json.loads(verdict_json_str)

            # Validate
            required_fields = ['summary', 'winner', 'confidence_score', 'issues', 'final_decision', 'key_evidence_cited']
            missing_fields = [field for field in required_fields if field not in verdict_dict]

            if missing_fields:
                raise Exception(f"Missing required fields in verdict: {', '.join(missing_fields)}")

            # Get token usage
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None

            # Create verdict record
            verdict = Verdict(
                case_id=case_id,
                round=round_number,
                verdict_json=verdict_dict,
                model_used='gpt-4o-mini',
                tokens_used=tokens_used
            )

            db.add(verdict)
            db.commit()
            db.refresh(verdict)

            return verdict

        except Exception as e:
            raise Exception(f"Failed to generate verdict: {str(e)}")

    @staticmethod
    def build_verdict_with_arguments_prompt(
        case: Case,
        side_a_docs: List[Document],
        side_b_docs: List[Document],
        side_a_args: List[Argument],
        side_b_args: List[Argument],
        previous_verdict: Verdict,
        round_number: int
    ) -> str:
        """
        Build prompt for verdict generation with arguments.

        Args:
            case: Case object
            side_a_docs: Side A documents
            side_b_docs: Side B documents
            side_a_args: Side A arguments for this round
            side_b_args: Side B arguments for this round
            previous_verdict: Previous round's verdict
            round_number: Current round number

        Returns:
            Prompt string
        """
        # Build document summaries
        side_a_doc_summary = "\n\n".join([
            f"**{doc.title}** ({doc.file_type})\n{(doc.full_text or '')[:800]}"
            for doc in side_a_docs
        ])

        side_b_doc_summary = "\n\n".join([
            f"**{doc.title}** ({doc.file_type})\n{(doc.full_text or '')[:800]}"
            for doc in side_b_docs
        ])

        # Build argument summaries
        side_a_arg_text = "\n\n".join([
            f"**Argument {i+1}:**\n{arg.argument_text}"
            for i, arg in enumerate(side_a_args)
        ]) if side_a_args else "No arguments submitted"

        side_b_arg_text = "\n\n".join([
            f"**Argument {i+1}:**\n{arg.argument_text}"
            for i, arg in enumerate(side_b_args)
        ]) if side_b_args else "No arguments submitted"

        # Previous verdict summary
        prev_verdict_summary = "N/A"
        if previous_verdict and previous_verdict.verdict_json:
            vj = previous_verdict.verdict_json
            prev_verdict_summary = f"""
**Previous Verdict (Round {previous_verdict.round}):**
- Winner: {vj.get('winner', 'N/A')}
- Confidence: {vj.get('confidence_score', 'N/A')}
- Summary: {vj.get('summary', 'N/A')}
- Decision: {vj.get('final_decision', 'N/A')}
"""

        prompt = f"""You are an AI judge presiding over a mock trial case. This is Round {round_number} of arguments.

**CASE INFORMATION:**
- Title: {case.title}
- Case Number: {case.case_number}
- Type: {case.case_type}
- Jurisdiction: {case.jurisdiction}
- Description: {case.description or 'N/A'}

**CURRENT ROUND:** {round_number}

{prev_verdict_summary}

**SIDE A EVIDENCE:**
{side_a_doc_summary}

**SIDE A ARGUMENTS (Round {round_number}):**
{side_a_arg_text}

**SIDE B EVIDENCE:**
{side_b_doc_summary}

**SIDE B ARGUMENTS (Round {round_number}):**
{side_b_arg_text}

**INSTRUCTIONS:**
1. Review the previous verdict and the new arguments from both sides
2. Consider how the arguments address or challenge the previous findings
3. Re-evaluate the evidence in light of the new arguments
4. Determine if the arguments change your assessment
5. Update your verdict accordingly
6. Explain what impact (if any) the arguments had on your decision

**IMPORTANT:** You must respond with ONLY a valid JSON object in the following format:

{{
    "summary": "Brief 2-3 sentence summary of how this round affected the case",
    "winner": "A" or "B" or "undecided",
    "confidence_score": 0.85,
    "issues": [
        {{
            "issue": "Question or issue being decided",
            "finding": "Your finding on this issue",
            "reasoning": "Detailed reasoning with evidence and argument citations"
        }}
    ],
    "final_decision": "Your updated verdict with reasoning (3-5 sentences)",
    "key_evidence_cited": ["Document and argument references that were most important"]
}}

Provide your verdict as a JSON object only:"""

        return prompt

    @staticmethod
    def get_case_arguments(case_id: UUID, db: Session) -> List[Argument]:
        """
        Get all arguments for a case, ordered by round and side.

        Args:
            case_id: Case UUID
            db: Database session

        Returns:
            List of Argument objects
        """
        return db.query(Argument).filter(
            Argument.case_id == case_id
        ).order_by(Argument.round, Argument.side).all()
