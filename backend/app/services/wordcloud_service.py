"""Word cloud image generation."""
import base64
import io
from typing import Dict, List
from app.nlp.text_processor import get_clean_tokens


def generate_wordcloud_base64(text: str) -> str:
    """Generate a word cloud image and return as base64 string."""
    try:
        from wordcloud import WordCloud
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        tokens = get_clean_tokens(text, remove_stopwords=True)
        freq_text = " ".join(tokens)

        wc = WordCloud(
            width=900,
            height=500,
            background_color="white",
            max_words=150,
            colormap="viridis",
            prefer_horizontal=0.7,
            margin=2,
        ).generate(freq_text)

        buf = io.BytesIO()
        plt.figure(figsize=(12, 6))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    except Exception as e:
        # Return empty string if wordcloud fails (dependency issue)
        return ""


def get_wordcloud_data(text: str, top_n: int = 100) -> List[Dict]:
    """Return word frequency data suitable for frontend word cloud rendering."""
    from collections import Counter
    tokens = get_clean_tokens(text, remove_stopwords=True)
    counter = Counter(tokens)
    total = sum(counter.values()) or 1
    return [
        {
            "text": word,
            "value": count,
            "weight": round(count / total * 100, 3),
        }
        for word, count in counter.most_common(top_n)
    ]
