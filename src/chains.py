"""LangChain model integration, reusable LLMChain, and streaming helpers."""

from collections.abc import Iterator
import re
from collections.abc import Callable

from langchain_classic.chains import LLMChain
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .prompts import (
    ASSESSMENT_CHAT_TEMPLATE,
    NARRATIVE_CHAT_TEMPLATE,
)
from .utils import contains_unsafe_medical_advice


def create_chat_model(model_name: str, api_key: str) -> ChatOpenAI:
    """Build a deterministic ChatOpenAI model for general educational output."""
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        temperature=0,
    )


def build_assessment_chain(llm: ChatOpenAI) -> LLMChain:
    """Create the reusable legacy chain required by the course assignment."""
    return LLMChain(
        llm=llm,
        prompt=ASSESSMENT_CHAT_TEMPLATE,
        output_key="assessment_json",
        verbose=False,
    )


def stream_narrative(
    llm: ChatOpenAI,
    assessment_json: str,
    language: str,
    on_filtered: Callable[[], None] | None = None,
) -> Iterator[str]:
    """Stream safe complete sentences, withholding medication advice and thresholds."""
    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(
        language=language,
        assessment_json=assessment_json,
    )
    buffer = ""
    yielded_safe_text = False
    filtered_text = False

    for chunk in llm.stream(messages):
        content = chunk.content
        if isinstance(content, str) and content:
            buffer += content
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    buffer += block["text"]

        while True:
            boundary = re.search(r"(?<=[.!?])(?:\s+|\n+)", buffer)
            if boundary is None:
                break
            sentence = buffer[: boundary.start() + 1].strip()
            buffer = buffer[boundary.end() :]
            if not sentence:
                continue
            if contains_unsafe_medical_advice(sentence):
                if not filtered_text and on_filtered is not None:
                    on_filtered()
                filtered_text = True
                continue
            yielded_safe_text = True
            yield sentence + " "

    trailing = buffer.strip()
    if trailing:
        if contains_unsafe_medical_advice(trailing):
            if not filtered_text and on_filtered is not None:
                on_filtered()
            filtered_text = True
        else:
            yielded_safe_text = True
            yield trailing

    if filtered_text:
        if language == "Urdu":
            yield " ذاتی مشورے کے لیے کسی مستند طبی ماہر سے رابطہ کریں۔"
        else:
            yield " For personalized advice, consult a qualified healthcare professional."
    elif not yielded_safe_text:
        if language == "Urdu":
            yield "ذاتی مشورے کے لیے کسی مستند طبی ماہر سے رابطہ کریں۔"
        else:
            yield "Please consult a qualified healthcare professional for personalized advice."


def demonstrate_message_roles() -> list[SystemMessage | HumanMessage | AIMessage]:
    """Show a fictional three-message conversation for the assignment explainer."""
    return [
        SystemMessage(
            content="You provide cautious general information and do not diagnose."
        ),
        HumanMessage(content="I have had a mild cough for one day."),
        AIMessage(
            content="I can share general information, but a clinician can advise about your situation."
        ),
    ]

