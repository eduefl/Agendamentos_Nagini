def normalize_service_name(name: str) -> str:
    lower_words = {"de", "da", "do", "das", "dos", "e"}
    words = name.strip().lower().split()

    formatted = [
        word.capitalize() if index == 0 or word not in lower_words else word
        for index, word in enumerate(words)
    ]

    return " ".join(formatted)
