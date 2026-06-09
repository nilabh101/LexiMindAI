"""PDF report generation using ReportLab."""
import io
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


BRAND_BLUE = colors.HexColor("#6366F1")
BRAND_PURPLE = colors.HexColor("#8B5CF6")
DARK = colors.HexColor("#1E1B4B")
LIGHT_BG = colors.HexColor("#F8FAFC")
ACCENT = colors.HexColor("#0EA5E9")


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("title", fontSize=28, fontName="Helvetica-Bold",
                                 textColor=DARK, alignment=TA_CENTER, spaceAfter=6),
        "tagline": ParagraphStyle("tagline", fontSize=12, fontName="Helvetica",
                                   textColor=BRAND_BLUE, alignment=TA_CENTER, spaceAfter=20),
        "h1": ParagraphStyle("h1", fontSize=16, fontName="Helvetica-Bold",
                              textColor=DARK, spaceBefore=14, spaceAfter=6,
                              borderPad=4),
        "h2": ParagraphStyle("h2", fontSize=13, fontName="Helvetica-Bold",
                              textColor=BRAND_BLUE, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", fontSize=10, fontName="Helvetica",
                                textColor=colors.HexColor("#374151"), leading=16, spaceAfter=6),
        "small": ParagraphStyle("small", fontSize=9, fontName="Helvetica",
                                 textColor=colors.grey, spaceAfter=4),
        "highlight": ParagraphStyle("highlight", fontSize=10, fontName="Helvetica-Bold",
                                     textColor=BRAND_BLUE, spaceAfter=4),
    }
    return styles


def _kpi_table(data: List[List], col_widths=None):
    col_widths = col_widths or [7 * cm, 9 * cm]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def generate_report(
    filename: str,
    stats: Dict[str, Any],
    sentiment: Dict[str, Any],
    topics: Dict[str, Any],
    style: Dict[str, Any],
    dna: Dict[str, Any],
    insights: List[Dict],
    summary: Dict[str, Any],
    word_freq: List[Dict],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"LexiMind AI Report — {filename}",
        author="LexiMind AI Platform",
    )

    s = _styles()
    story = []

    # Cover
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("LexiMind AI", s["title"]))
    story.append(Paragraph("Transforming Documents into Actionable Intelligence", s["tagline"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"<b>Document:</b> {filename}", s["body"]))
    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        s["body"],
    ))
    story.append(Spacer(1, 0.5 * cm))

    # Executive Summary
    story.append(Paragraph("Executive Summary", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    story.append(Spacer(1, 0.3 * cm))
    exec_summary = summary.get("executive_summary", "")
    story.append(Paragraph(exec_summary[:1000], s["body"]))
    story.append(Spacer(1, 0.5 * cm))

    # Document Statistics
    story.append(Paragraph("Document Statistics", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    story.append(Spacer(1, 0.3 * cm))

    stat_data = [
        ["Metric", "Value"],
        ["Total Words", f"{stats.get('word_count', 0):,}"],
        ["Unique Words", f"{stats.get('unique_word_count', 0):,}"],
        ["Sentences", f"{stats.get('sentence_count', 0):,}"],
        ["Paragraphs", f"{stats.get('paragraph_count', 0):,}"],
        ["Characters", f"{stats.get('character_count', 0):,}"],
        ["Avg Sentence Length", f"{stats.get('average_sentence_length', 0)} words"],
        ["Reading Time", f"{stats.get('reading_time_minutes', 0)} minutes"],
        ["Reading Grade Level", f"{stats.get('reading_grade_level', 0)}"],
        ["Flesch Reading Ease", f"{stats.get('flesch_reading_ease', 0)}"],
        ["Lexical Diversity", f"{round(stats.get('lexical_diversity', 0) * 100, 1)}%"],
        ["Vocabulary Richness", f"{stats.get('vocabulary_richness', 0)}%"],
    ]
    story.append(_kpi_table(stat_data))
    story.append(Spacer(1, 0.5 * cm))

    # Sentiment
    story.append(Paragraph("Sentiment Analysis", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    story.append(Spacer(1, 0.3 * cm))
    doc_sent = sentiment.get("document", {})
    dist = sentiment.get("distribution", {})
    sent_data = [
        ["Metric", "Value"],
        ["Overall Sentiment", doc_sent.get("label", "").title()],
        ["Polarity Score", str(doc_sent.get("polarity", 0))],
        ["Subjectivity Score", str(doc_sent.get("subjectivity", 0))],
        ["Positive Sentences", f"{dist.get('positive', 0)}%"],
        ["Negative Sentences", f"{dist.get('negative', 0)}%"],
        ["Neutral Sentences", f"{dist.get('neutral', 0)}%"],
    ]
    story.append(_kpi_table(sent_data))
    story.append(Spacer(1, 0.5 * cm))

    # Topics
    story.append(Paragraph("Topic Analysis", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    story.append(Spacer(1, 0.3 * cm))
    primary_topics = ", ".join(topics.get("primary_topics", []))
    secondary_topics = ", ".join(topics.get("secondary_topics", []))
    story.append(Paragraph(f"<b>Primary Topics:</b> {primary_topics}", s["body"]))
    story.append(Paragraph(f"<b>Secondary Topics:</b> {secondary_topics}", s["body"]))
    story.append(Spacer(1, 0.3 * cm))

    topic_rows = [["Topic", "Score", "Keywords"]]
    for t in topics.get("topics", [])[:8]:
        topic_rows.append([
            t["topic"],
            str(t["score"]),
            ", ".join(t["keywords"][:4]),
        ])
    if len(topic_rows) > 1:
        story.append(_kpi_table(topic_rows, col_widths=[4 * cm, 3 * cm, 9 * cm]))
    story.append(Spacer(1, 0.5 * cm))

    # Writing Style & DNA
    story.append(Paragraph("Writing Style & Document DNA", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"<b>Style:</b> {style.get('primary_style', 'N/A')} ({style.get('confidence', 0)}% confidence)",
        s["body"],
    ))
    story.append(Paragraph(style.get("description", ""), s["body"]))
    story.append(Spacer(1, 0.3 * cm))

    dna_vals = dna.get("dna", {})
    dna_rows = [["Dimension", "Score"]]
    for k, v in dna_vals.items():
        dna_rows.append([k.replace("_", " ").title(), f"{round(v * 100, 1)}%"])
    story.append(_kpi_table(dna_rows))
    story.append(Spacer(1, 0.5 * cm))

    # Top Words
    story.append(Paragraph("Top 25 Words by Frequency", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    story.append(Spacer(1, 0.3 * cm))
    word_rows = [["Rank", "Word", "Count", "Percentage"]]
    for wf in word_freq[:25]:
        word_rows.append([
            str(wf.get("rank", "")),
            wf.get("word", ""),
            str(wf.get("count", "")),
            f"{wf.get('percentage', 0)}%",
        ])
    story.append(_kpi_table(word_rows, col_widths=[2 * cm, 5 * cm, 3 * cm, 4 * cm]))
    story.append(Spacer(1, 0.5 * cm))

    # AI Insights
    story.append(Paragraph("AI-Generated Insights", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    story.append(Spacer(1, 0.3 * cm))
    for ins in insights[:8]:
        icon = ins.get("icon", "•")
        text = ins.get("insight", "")
        story.append(Paragraph(f"{icon}  {text}", s["body"]))
        story.append(Spacer(1, 0.15 * cm))

    # Bullet Summary
    story.append(PageBreak())
    story.append(Paragraph("Key Bullet Points", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    story.append(Spacer(1, 0.3 * cm))
    for bp in summary.get("bullet_points", [])[:8]:
        story.append(Paragraph(f"• {bp}", s["body"]))
        story.append(Spacer(1, 0.1 * cm))

    # Footer note
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "Generated by LexiMind AI — Transforming Documents into Actionable Intelligence",
        s["small"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
