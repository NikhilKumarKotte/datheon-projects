from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """
    Base model with extra='forbid' to ensure strict conformance with the expected schema.
    Rejects any unmapped or hallucinated keys in model outputs.
    """
    model_config = ConfigDict(extra="forbid")
