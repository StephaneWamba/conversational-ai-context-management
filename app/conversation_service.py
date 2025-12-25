"""Main FastAPI service for conversation management."""

import logging
import time
from contextlib import asynccontextmanager
from typing import List, Tuple
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.api.health import check_all_dependencies, check_readiness
from app.core.config import settings
from app.core.dependencies import services
from app.models.response import (
    ConversationResponse,
    CreateConversationResponse,
    MemoryResponse,
    MessageRequest,
    MessageResponse,
)
from app.monitoring import metrics
from app.services.context_compressor import ContextCompressor
from app.services.token_manager import TokenManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    await services.initialize()
    yield
    await services.shutdown()


app = FastAPI(
    title="Conversational AI Context Management",
    description="API for managing long conversations with context compression",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Overall health status and individual service statuses.
    """
    health_status = await check_all_dependencies(
        database=services.database,
        semantic_memory=services.semantic_memory,
        memory_manager=services.memory_manager,
    )
    status_code = (
        status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=health_status,
        status_code=status_code,
    )


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Returns:
        Readiness status for all required dependencies.
    """
    readiness = await check_readiness(
        database=services.database,
        semantic_memory=services.semantic_memory,
        memory_manager=services.memory_manager,
    )
    status_code = (
        status.HTTP_200_OK if readiness["ready"] else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=readiness,
        status_code=status_code,
    )


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/conversations", response_model=CreateConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(request: MessageRequest):
    """
    Create a new conversation and send the first message.

    Args:
        request: Message request with user_id and content

    Returns:
        Conversation response with first turn
    """
    start_time = time.time()
    try:
        metrics.conversations_total.inc()

        # Create conversation
        conversation = await services.database.create_conversation(
            user_id=request.user_id,
            session_id=request.session_id or f"session_{request.user_id}",
        )

        # Add user message
        user_message = await services.database.add_message(
            conversation_id=conversation.id,
            role="user",
            content=request.content,
            turn_number=1,
        )
        # Add to short-term memory
        await services.memory_manager.add_message_to_short_term_memory(
            conversation_id=conversation.id,
            role="user",
            content=request.content,
            turn_number=1,
        )

        # Generate response
        response_text, tokens_used, context_tokens, response_tokens = await _generate_response(
            conversation_id=conversation.id,
            user_id=request.user_id,
            user_message=request.content,
            turn_number=1,
        )

        # Add assistant message
        assistant_message = await services.database.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            turn_number=2,
            tokens_used=tokens_used,
        )
        # Add to short-term memory
        await services.memory_manager.add_message_to_short_term_memory(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            turn_number=2,
        )

        metrics.messages_total.inc()
        metrics.response_latency_seconds.observe(time.time() - start_time)
        metrics.tokens_used_total.inc(tokens_used)
        metrics.context_tokens_total.inc(context_tokens)
        metrics.response_tokens_total.inc(response_tokens)

        # Return both conversation and first message response
        return CreateConversationResponse(
            conversation=ConversationResponse(
                id=conversation.id,
                user_id=conversation.user_id,
                session_id=conversation.session_id,
                total_turns=conversation.total_turns,
                total_tokens_used=conversation.total_tokens_used,
                created_at=conversation.created_at.isoformat() if conversation.created_at else "",
                updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
            ),
            message=MessageResponse(
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                response=response_text,
                turn_number=2,
                tokens_used=tokens_used,
                context_tokens=context_tokens,
                response_tokens=response_tokens,
            ),
        )
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}", exc_info=True)
        metrics.message_errors_total.inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}",
        ) from e


@app.post("/api/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: UUID, request: MessageRequest):
    """
    Send a message in an existing conversation.

    Args:
        conversation_id: Conversation ID
        request: Message request with content

    Returns:
        Message response with assistant reply
    """
    start_time = time.time()
    try:
        # Get conversation
        conversation = await services.database.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Verify user_id matches
        if conversation.user_id != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User ID mismatch",
            )

        turn_number = conversation.total_turns + 1

        # Add user message
        user_message = await services.database.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.content,
            turn_number=turn_number,
        )
        # Add to short-term memory
        await services.memory_manager.add_message_to_short_term_memory(
            conversation_id=conversation_id,
            role="user",
            content=request.content,
            turn_number=turn_number,
        )

        # Generate response
        response_text, tokens_used, context_tokens, response_tokens = await _generate_response(
            conversation_id=conversation_id,
            user_id=request.user_id,
            user_message=request.content,
            turn_number=turn_number,
        )

        # Add assistant message
        assistant_message = await services.database.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            turn_number=turn_number + 1,
            tokens_used=tokens_used,
        )
        # Add to short-term memory
        await services.memory_manager.add_message_to_short_term_memory(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            turn_number=turn_number + 1,
        )

        assistant_turn = turn_number + 1
        if assistant_turn % settings.summary_interval == 0:
            await _create_summary(conversation_id, request.user_id, assistant_turn)

        metrics.messages_total.inc()
        metrics.response_latency_seconds.observe(time.time() - start_time)
        metrics.tokens_used_total.inc(tokens_used)
        metrics.context_tokens_total.inc(context_tokens)
        metrics.response_tokens_total.inc(response_tokens)

        return MessageResponse(
            conversation_id=conversation_id,
            message_id=assistant_message.id,
            response=response_text,
            turn_number=turn_number + 1,
            tokens_used=tokens_used,
            context_tokens=context_tokens,
            response_tokens=response_tokens,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}", exc_info=True)
        metrics.message_errors_total.inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        ) from e


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: UUID):
    """
    Get conversation details.

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation response
    """
    conversation = await services.database.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        session_id=conversation.session_id,
        total_turns=conversation.total_turns,
        total_tokens_used=conversation.total_tokens_used,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
    )


@app.get("/api/conversations/{conversation_id}/memory", response_model=MemoryResponse)
async def get_memory(conversation_id: UUID):
    """
    Get memory state for a conversation.

    Args:
        conversation_id: Conversation ID

    Returns:
        Memory state response
    """
    conversation = await services.database.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    memory_state = await services.memory_manager.get_memory_state(
        conversation_id=conversation_id,
        user_id=conversation.user_id,
    )

    # Get summary details
    summaries_list = []
    if memory_state.long_term:
        summaries_list = [
            {
                "turn_range": summary["turn_range"],
                "summary": summary["summary"],
                "key_facts": summary.get("key_facts"),
            }
            for summary in memory_state.long_term.summaries
        ]

    return MemoryResponse(
        conversation_id=conversation_id,
        short_term_turns=memory_state.short_term.turn_count,
        long_term_summaries=len(
            memory_state.long_term.summaries) if memory_state.long_term else 0,
        semantic_results=len(memory_state.semantic),
        total_context_tokens=memory_state.total_context_tokens,
        total_turns=conversation.total_turns,
        summaries=summaries_list,
    )


async def _generate_response(
    conversation_id: UUID,
    user_id: str,
    user_message: str,
    turn_number: int,
) -> Tuple[str, int, int, int]:
    """
    Generate a response for a user message.

    Args:
        conversation_id: Conversation ID
        user_id: User identifier
        user_message: User message content
        turn_number: Current turn number

    Returns:
        Tuple of (response_text, total_tokens_used, context_tokens, response_tokens)
    """
    memory_start = time.time()
    # Get memory state
    memory_state = await services.memory_manager.get_memory_state(
        conversation_id=conversation_id,
        user_id=user_id,
        query_text=user_message,
    )
    metrics.memory_retrieval_duration_seconds.observe(
        time.time() - memory_start)

    # Build context messages
    messages = []
    token_manager = TokenManager()

    # Get active constraints
    active_constraints = await services.constraint_manager.get_active_constraints(conversation_id)

    # Extract new constraints from recent messages (every turn)
    recent_messages = memory_state.short_term.messages[-3:
                                                       ] if memory_state.short_term.messages else []
    new_constraints = await services.constraint_manager.extract_constraints(
        conversation_id=conversation_id,
        messages=recent_messages + [{"role": "user", "content": user_message}],
        turn_number=turn_number,
    )

    # Store new constraints
    for constraint in new_constraints:
        try:
            await services.constraint_manager.store_constraint(constraint)
            active_constraints.append(constraint)
        except Exception:
            pass

    # Build enhanced system prompt with constraints
    base_prompt = """You are a helpful assistant. Maintain full context from the current conversation:
- Remember and reference all information shared in previous messages
- Be consistent with facts, details, and topics already discussed
- Use the conversation history to provide coherent and contextually aware responses"""

    # Add constraints prompt (re-inject every 5 turns or if constraints exist)
    constraint_prompt = ""
    if turn_number % 5 == 0 or active_constraints:
        constraint_prompt = services.constraint_manager.build_constraint_prompt(
            active_constraints)

    system_prompt = base_prompt + constraint_prompt
    system_tokens = token_manager.count_tokens(system_prompt)

    # Add long-term memory (summaries)
    if memory_state.long_term:
        for summary in memory_state.long_term.summaries:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {summary['summary']}",
            })

    # Add semantic memory (relevant past conversations)
    for semantic_result in memory_state.semantic:
        messages.append({
            "role": "system",
            "content": f"Relevant past conversation: {semantic_result.summary}",
        })

    for msg in memory_state.short_term.messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    if (not memory_state.short_term.messages or
            memory_state.short_term.messages[-1].get("content") != user_message or
            memory_state.short_term.messages[-1].get("role") != "user"):
        messages.append({"role": "user", "content": user_message})

    # Check token budget
    available_budget = token_manager.get_available_budget(
        system_tokens=system_tokens,
        response_tokens=settings.response_tokens,
    )
    context_tokens = token_manager.count_tokens_messages(messages)

    # Compress if needed
    compressed = False
    if await services.context_compressor.should_compress(context_tokens, available_budget):
        compression_start = time.time()
        messages = await services.context_compressor.compress_context(
            messages, target_tokens=available_budget
        )
        context_tokens = token_manager.count_tokens_messages(messages)
        compressed = True
        metrics.compression_events_total.inc()
        metrics.summarization_duration_seconds.observe(
            time.time() - compression_start)

    # Generate response
    response_text = await services.llm_service.generate_response(
        messages=messages,
        system_prompt=system_prompt,
        max_tokens=settings.response_tokens,
    )

    # Calculate total tokens
    response_tokens = token_manager.count_tokens(response_text)
    total_tokens = system_tokens + context_tokens + response_tokens

    return response_text, total_tokens, context_tokens, response_tokens


async def _create_summary(conversation_id: UUID, user_id: str, current_turn: int) -> None:
    """
    Create a summary for a range of turns and index it in semantic memory.

    Args:
        conversation_id: Conversation ID
        user_id: User identifier
        current_turn: Current turn number
    """
    try:
        summary_start = time.time()
        # Get messages in the range to summarize
        start_turn = max(1, current_turn - settings.summary_interval + 1)
        messages = await services.database.get_messages(conversation_id)
        range_messages = [m for m in messages if start_turn <=
                          m.turn_number <= current_turn]

        if not range_messages:
            return

        # Calculate original tokens
        token_manager = TokenManager()
        original_tokens = sum(token_manager.count_tokens(m.content)
                              for m in range_messages)

        # Create summary text
        summary_text = "\n".join(
            [f"{m.role}: {m.content}" for m in range_messages]
        )

        # Generate summary
        summary = await services.llm_service.summarize(summary_text)

        # Validate and correct summary using active constraints
        active_constraints = await services.constraint_manager.get_active_constraints(conversation_id)
        validated_summary = await _validate_and_correct_summary(
            summary, active_constraints, range_messages
        )

        # Store summary in PostgreSQL
        compressed_tokens = token_manager.count_tokens(validated_summary)
        tokens_saved = original_tokens - compressed_tokens

        summary_obj = await services.database.create_summary(
            conversation_id=conversation_id,
            summary=validated_summary,
            compressed_tokens=compressed_tokens,
            turn_range_start=start_turn,
            turn_range_end=current_turn,
        )

        try:
            embedding = await services.embedding_service.generate_embedding(validated_summary)
            await services.semantic_memory.store_conversation(
                conversation_id=conversation_id,
                summary_id=summary_obj.id,
                user_id=user_id,
                text=validated_summary,
                embedding=embedding,
                turn_range_start=start_turn,
                turn_range_end=current_turn,
            )
        except Exception:
            pass

        metrics.summaries_created_total.inc()
        metrics.summary_tokens_saved_total.inc(tokens_saved)
        metrics.summarization_duration_seconds.observe(
            time.time() - summary_start)
    except Exception:
        pass


async def _validate_and_correct_summary(
    summary: str, constraints: List, original_messages: List
) -> str:
    """
    Validate and correct summary using constraints.

    Args:
        summary: Generated summary text
        constraints: Active constraints
        original_messages: Original messages that were summarized

    Returns:
        Validated and corrected summary
    """
    # Check for corrections that need to be applied
    corrections = [c for c in constraints if c.constraint_type == "correction"]

    if not corrections:
        return summary

    # Build correction prompt
    correction_notes = []
    for corr in corrections:
        old_val = corr.constraint_value.get("old_value")
        new_val = corr.constraint_value.get("new_value")
        if old_val and new_val:
            correction_notes.append(f"Use {new_val} instead of {old_val}")

    if correction_notes:
        correction_prompt = f"""The following summary may contain incorrect values. Please correct them:
        
Corrections to apply:
{chr(10).join(correction_notes)}

Summary to correct:
{summary}

Corrected summary (ensure all corrections are applied):"""

        try:
            corrected = await services.llm_service.summarize(
                correction_prompt, max_tokens=300
            )
            return corrected
        except Exception:
            return summary

    return summary
