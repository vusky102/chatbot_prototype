__all__ = ["RAGService"]


def __getattr__(name):
    if name == "RAGService":
        from .service import RAGService

        return RAGService
    raise AttributeError(name)
