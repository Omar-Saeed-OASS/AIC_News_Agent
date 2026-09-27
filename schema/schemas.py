from pydantic import BaseModel, Field

class ResearchQuestion(BaseModel):
    """Schema for research brief generation."""
    research_brief: str = Field(
        description="A research question that will be used to guide the research.",
    )

class Summary(BaseModel):
    """Research summary with key findings."""

    summary: str
    key_excerpts: str

