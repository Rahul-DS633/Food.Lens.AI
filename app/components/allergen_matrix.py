"""
FoodLens UI Component: Allergen Matrix Visualizer
Renders an interactive, accessible grid of family members vs allergens.
"""

from typing import Dict, List, Any
import streamlit as st


STATUS_STYLES = {
    "CONTAINS_YOUR_ALLERGEN": {
        "bg": "#FEE2E2",
        "color": "#991B1B",
        "border": "#F87171",
        "icon": "⚠️",
        "text": "Contains",
    },
    "MAY_CONTAIN_TRACES": {
        "bg": "#FEF3C7",
        "color": "#92400E",
        "border": "#FBBF24",
        "icon": "⚠️",
        "text": "Traces",
    },
    "UNKNOWN": {
        "bg": "#F1F5F9",
        "color": "#475569",
        "border": "#CBD5E1",
        "icon": "❓",
        "text": "Unknown",
    },
    "NONE_DETECTED_IN_READABLE_TEXT": {
        "bg": "#DCFCE7",
        "color": "#166534",
        "border": "#86EFAC",
        "icon": "✓",
        "text": "Not Detected",
    },
}


def render_allergen_matrix(
    members: List[Any],
    allergen_matrix: Dict[str, Dict[str, str]],
):
    """
    Renders an HTML matrix table displaying members vs their respective allergens.
    """
    if not members:
        return

    # Collect unique allergens across all members
    all_allergens = sorted(list({
        alg.lower()
        for m in members
        for alg in getattr(m, "allergies", [])
    }))

    if not all_allergens:
        st.markdown(
            """
            <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 12px; padding: 12px 16px; margin: 12px 0;">
                <span style="color: #166534; font-weight: 700;">✓ No active allergen filters configured for selected family members.</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Build matrix table HTML
    header_cols = "".join([f"<th style='padding: 8px 12px; text-transform: capitalize; border-bottom: 2px solid #CBD5E1; color: #1E293B;'>{alg}</th>" for alg in all_allergens])
    
    rows_html = []
    for m in members:
        m_id = str(getattr(m, "id", m))
        name = getattr(m, "display_name", f"Member {m_id}")
        avatar = getattr(m, "emoji_avatar", "👤")
        is_minor = getattr(m, "is_minor", False)
        minor_tag = " <span style='font-size: 10px; background: #E2E8F0; padding: 1px 5px; border-radius: 4px;'>Minor</span>" if is_minor else ""

        m_dict = allergen_matrix.get(m_id, {})
        cell_tds = []
        for alg in all_allergens:
            st_key = m_dict.get(alg, "NONE_DETECTED_IN_READABLE_TEXT")
            # If member doesn't track this allergen
            if alg not in [a.lower() for a in getattr(m, "allergies", [])]:
                cell_tds.append("<td style='padding: 8px 12px; text-align: center; color: #94A3B8;'>—</td>")
            else:
                cfg = STATUS_STYLES.get(st_key, STATUS_STYLES["NONE_DETECTED_IN_READABLE_TEXT"])
                cell_tds.append(
                    f"<td style='padding: 8px 12px; text-align: center;'>"
                    f"<span style='background: {cfg['bg']}; color: {cfg['color']}; border: 1px solid {cfg['border']}; border-radius: 6px; padding: 3px 8px; font-size: 11.5px; font-weight: 700; white-space: nowrap;'>"
                    f"{cfg['icon']} {cfg['text']}</span></td>"
                )

        row_cells = "".join(cell_tds)
        rows_html.append(
            f"<tr style='border-bottom: 1px solid #E2E8F0;'>"
            f"<td style='padding: 8px 12px; font-weight: 700; color: #0F172A; white-space: nowrap;'>"
            f"{avatar} {name}{minor_tag}</td>"
            f"{row_cells}</tr>"
        )

    table_body = "".join(rows_html)

    st.markdown(
        f"""
        <div style="overflow-x: auto; margin: 14px 0; background: #FFFFFF; border-radius: 12px; border: 1.5px solid #E2E8F0; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <table style="width: 100%; border-collapse: collapse; font-size: 13.5px; text-align: left;">
                <thead style="background: #F8FAFC;">
                    <tr>
                        <th style="padding: 10px 12px; border-bottom: 2px solid #CBD5E1; color: #475569;">Family Member</th>
                        {header_cols}
                    </tr>
                </thead>
                <tbody>
                    {table_body}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True
    )
